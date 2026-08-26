"""
RecoverAI Intelligence Data & Feature Layer
Module initializing feature engineering logic, feature metadata, and dataset generation service.
"""

from .feature_engineering import (
    IDENTIFIER_COLUMNS,
    TARGET_COLUMN,
    LEAKAGE_COLUMNS,
    FEATURE_COLUMNS,
    PAYMENT_FEATURES,
    FAILURE_FEATURES,
    MERCHANT_FEATURES,
    GATEWAY_FEATURES,
    RECOVERY_CONTEXT_FEATURES,
    build_recovery_intelligence_dataset
)
from .intelligence_data_service import (
    IntelligenceDataService,
    get_intelligence_data_service
)

__all__ = [
    "IDENTIFIER_COLUMNS",
    "TARGET_COLUMN",
    "LEAKAGE_COLUMNS",
    "FEATURE_COLUMNS",
    "PAYMENT_FEATURES",
    "FAILURE_FEATURES",
    "MERCHANT_FEATURES",
    "GATEWAY_FEATURES",
    "RECOVERY_CONTEXT_FEATURES",
    "build_recovery_intelligence_dataset",
    "IntelligenceDataService",
    "get_intelligence_data_service"
]
