import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
import os

# Centralized Feature Metadata Definitions for Phase 3A & Phase 3B
IDENTIFIER_COLUMNS = [
    'payment_id',
    'merchant_id',
    'customer_id',
    'failure_id',
    'attempt_id'
]

TARGET_COLUMN = 'recovered'

LEAKAGE_COLUMNS = [
    'status',
    'attempt_status',
    'recovered_amount_inr',
    'risk_amount_inr',
    'resolved_at',
    'merchant_historical_recovered_count'
]

PAYMENT_FEATURES = [
    'amount_inr',
    'payment_method',
    'gateway',
    'transaction_hour',
    'day_of_week',
    'is_weekend'
]

FAILURE_FEATURES = [
    'failure_category',
    'error_code',
    'retryable'
]

MERCHANT_FEATURES = [
    'merchant_segment',
    'industry',
    'merchant_historical_tx_count',
    'merchant_historical_failure_rate',
    'merchant_historical_recovery_rate'
]

GATEWAY_FEATURES = [
    'gateway_historical_latency_ms',
    'gateway_historical_success_rate',
    'gateway_historical_error_rate',
    'gateway_historical_incident_count'
]

RECOVERY_CONTEXT_FEATURES = [
    'strategy',
    'attempt_number',
    'delay_minutes',
    'predicted_recovery_probability'
]

FEATURE_COLUMNS = (
    PAYMENT_FEATURES +
    FAILURE_FEATURES +
    MERCHANT_FEATURES +
    GATEWAY_FEATURES +
    RECOVERY_CONTEXT_FEATURES
)

def build_recovery_intelligence_dataset(data_service=None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Programmatically builds an ML-ready derived recovery intelligence dataset from CSV datasets.
    
    Grain: 1 Row = 1 Payment Recovery Case (5,000 rows).
    Includes time-ordered Expanding Window aggregations for merchant metrics to eliminate data leakage.
    """
    if data_service is None:
        from services.data_service import get_data_service
        data_service = get_data_service()

    # Get raw DataFrames
    merchants = data_service.get_merchants()
    payments = data_service.get_payments()
    payment_failures = data_service.get_payment_failures()
    recovery_attempts = data_service.get_recovery_attempts()
    gateway_events = data_service.get_gateway_events()

    raw_payments_count = len(payments)

    # 1. Merge Datasets at 1 Payment = 1 Row Grain
    df = pd.merge(payments, payment_failures, on='payment_id', how='inner')
    df = pd.merge(df, recovery_attempts, on='payment_id', how='inner')
    df = pd.merge(df, merchants[['merchant_id', 'merchant_name', 'industry', 'merchant_segment']], on='merchant_id', how='left')

    merged_count = len(df)
    assert merged_count == raw_payments_count, f"Row count changed after merge! Expected {raw_payments_count}, got {merged_count}"

    # 2. Time Sorting (Chronological Order)
    df['created_at_dt'] = pd.to_datetime(df['created_at'])
    df = df.sort_values('created_at_dt').reset_index(drop=True)

    # 3. Target Definition
    df[TARGET_COLUMN] = (df['attempt_status'] == 'Recovered').astype(int)

    # 4. Temporal Features
    df['transaction_hour'] = df['created_at_dt'].dt.hour
    df['day_of_week'] = df['created_at_dt'].dt.dayofweek
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)

    # 5. Expanding Window Historical Merchant Features (Zero Data Leakage)
    df['merchant_historical_tx_count'] = df.groupby('merchant_id').cumcount()
    
    # Cumulative recovered transactions prior to current row
    df['merchant_historical_recovered_count'] = (
        df.groupby('merchant_id')[TARGET_COLUMN]
          .shift(1)
          .fillna(0)
          .groupby(df['merchant_id'])
          .cumsum()
    )

    # Prior recovery rate (%)
    df['merchant_historical_recovery_rate'] = np.where(
        df['merchant_historical_tx_count'] > 0,
        (df['merchant_historical_recovered_count'] / df['merchant_historical_tx_count'] * 100).round(2),
        0.0
    )

    # Prior failure rate (%)
    df['merchant_historical_failure_rate'] = np.where(
        df['merchant_historical_tx_count'] > 0,
        ((df['merchant_historical_tx_count'] - df['merchant_historical_recovered_count']) / df['merchant_historical_tx_count'] * 100).round(2),
        0.0
    )

    # 6. Gateway Historical Telemetry Features
    if not gateway_events.empty:
        gw_stats = gateway_events.groupby('gateway').agg(
            gateway_historical_latency_ms=('latency_ms', 'mean'),
            gateway_historical_success_rate=('success_rate', 'mean'),
            gateway_historical_error_rate=('error_rate', 'mean'),
            gateway_historical_incident_count=('is_incident', 'sum')
        ).reset_index()

        gw_stats['gateway_historical_latency_ms'] = gw_stats['gateway_historical_latency_ms'].round(2)
        gw_stats['gateway_historical_success_rate'] = gw_stats['gateway_historical_success_rate'].round(2)
        gw_stats['gateway_historical_error_rate'] = gw_stats['gateway_historical_error_rate'].round(2)
        gw_stats['gateway_historical_incident_count'] = gw_stats['gateway_historical_incident_count'].astype(int)

        df = pd.merge(df, gw_stats, on='gateway', how='left')

    # Safe Missing Value Imputation
    df['gateway_historical_latency_ms'] = df['gateway_historical_latency_ms'].fillna(180.0)
    df['gateway_historical_success_rate'] = df['gateway_historical_success_rate'].fillna(97.5)
    df['gateway_historical_error_rate'] = df['gateway_historical_error_rate'].fillna(2.5)
    df['gateway_historical_incident_count'] = df['gateway_historical_incident_count'].fillna(0).astype(int)
    df['retryable'] = df['retryable'].astype(bool)

    # Organize Columns into Identifiers, Target, Features, and Leakage
    all_columns = IDENTIFIER_COLUMNS + [TARGET_COLUMN] + FEATURE_COLUMNS + LEAKAGE_COLUMNS + ['created_at', 'merchant_name']
    
    # Filter columns that exist
    ordered_columns = [col for col in all_columns if col in df.columns]
    final_df = df[ordered_columns].copy()

    # Data Quality Report
    quality_report = {
        "original_payments_count": raw_payments_count,
        "final_records_count": len(final_df),
        "dataset_grain": "1 row = 1 payment recovery case",
        "feature_count": len(FEATURE_COLUMNS),
        "target_distribution": final_df[TARGET_COLUMN].value_counts().to_dict(),
        "recovered_rate_pct": round(final_df[TARGET_COLUMN].mean() * 100, 2),
        "null_counts": final_df[FEATURE_COLUMNS].isnull().sum().to_dict(),
        "duplicate_payment_ids": int(final_df['payment_id'].duplicated().sum()),
        "merchant_ids_valid": bool(final_df['merchant_id'].notnull().all()),
        "target_leakage_in_features": any(col in FEATURE_COLUMNS for col in LEAKAGE_COLUMNS)
    }

    return final_df, quality_report
