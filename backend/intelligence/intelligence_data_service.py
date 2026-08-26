import os
import pandas as pd
from typing import Dict, Any, Tuple
from intelligence.feature_engineering import (
    build_recovery_intelligence_dataset,
    IDENTIFIER_COLUMNS,
    TARGET_COLUMN,
    LEAKAGE_COLUMNS,
    FEATURE_COLUMNS,
    PAYMENT_FEATURES,
    FAILURE_FEATURES,
    MERCHANT_FEATURES,
    GATEWAY_FEATURES,
    RECOVERY_CONTEXT_FEATURES
)

class IntelligenceDataService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IntelligenceDataService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        derived_dir = os.path.join(base_dir, "data", "derived")
        os.makedirs(derived_dir, exist_ok=True)
        self.derived_file_path = os.path.join(derived_dir, "recovery_intelligence_dataset.csv")

        # Generate intelligence dataset & quality report
        self.dataset_df, self.quality_report = build_recovery_intelligence_dataset()
        self.save_derived_dataset()

    def save_derived_dataset(self):
        """Saves the derived dataset programmatically to backend/data/derived/recovery_intelligence_dataset.csv"""
        self.dataset_df.to_csv(self.derived_file_path, index=False)

    def get_intelligence_dataset(self) -> pd.DataFrame:
        """Returns the ML-ready intelligence DataFrame"""
        return self.dataset_df

    def get_feature_metadata(self) -> Dict[str, Any]:
        """Returns metadata definitions for model training in Phase 3B"""
        return {
            "identifier_columns": IDENTIFIER_COLUMNS,
            "target_column": TARGET_COLUMN,
            "leakage_columns": LEAKAGE_COLUMNS,
            "feature_columns": FEATURE_COLUMNS,
            "feature_categories": {
                "payment_features": PAYMENT_FEATURES,
                "failure_features": FAILURE_FEATURES,
                "merchant_features": MERCHANT_FEATURES,
                "gateway_features": GATEWAY_FEATURES,
                "recovery_context_features": RECOVERY_CONTEXT_FEATURES
            }
        }

    def get_data_quality_report(self) -> Dict[str, Any]:
        """Returns dataset quality and statistical metrics"""
        return self.quality_report

def get_intelligence_data_service() -> IntelligenceDataService:
    return IntelligenceDataService()
