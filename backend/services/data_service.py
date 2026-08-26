import os
import pandas as pd
from typing import Dict

class DataService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataService, cls).__new__(cls)
            cls._instance._load_data()
        return cls._instance

    def _load_data(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data")

        # Load CSVs
        self.merchants_df = pd.read_csv(os.path.join(data_dir, "merchants.csv"))
        self.customers_df = pd.read_csv(os.path.join(data_dir, "customers.csv"))
        self.payments_df = pd.read_csv(os.path.join(data_dir, "payments.csv"))
        self.payment_failures_df = pd.read_csv(os.path.join(data_dir, "payment_failures.csv"))
        self.recovery_attempts_df = pd.read_csv(os.path.join(data_dir, "recovery_attempts.csv"))
        self.gateway_events_df = pd.read_csv(os.path.join(data_dir, "gateway_events.csv"))

        # Clean ID string columns
        for col in ["merchant_id"]:
            if col in self.merchants_df.columns:
                self.merchants_df[col] = self.merchants_df[col].astype(str).str.strip()
        for col in ["merchant_id", "payment_id", "customer_id"]:
            if col in self.payments_df.columns:
                self.payments_df[col] = self.payments_df[col].astype(str).str.strip()
        if "payment_id" in self.payment_failures_df.columns:
            self.payment_failures_df["payment_id"] = self.payment_failures_df["payment_id"].astype(str).str.strip()
        if "payment_id" in self.recovery_attempts_df.columns:
            self.recovery_attempts_df["payment_id"] = self.recovery_attempts_df["payment_id"].astype(str).str.strip()

        # Datetime conversions
        if "created_at" in self.merchants_df.columns:
            self.merchants_df["created_at"] = pd.to_datetime(self.merchants_df["created_at"], errors="coerce")
        if "created_at" in self.payments_df.columns:
            self.payments_df["created_at"] = pd.to_datetime(self.payments_df["created_at"], errors="coerce")
        if "timestamp" in self.gateway_events_df.columns:
            self.gateway_events_df["timestamp"] = pd.to_datetime(self.gateway_events_df["timestamp"], errors="coerce")
        if "resolved_at" in self.recovery_attempts_df.columns:
            self.recovery_attempts_df["resolved_at"] = pd.to_datetime(self.recovery_attempts_df["resolved_at"], errors="coerce")

    def get_merchants(self) -> pd.DataFrame:
        return self.merchants_df

    def get_customers(self) -> pd.DataFrame:
        return self.customers_df

    def get_payments(self) -> pd.DataFrame:
        return self.payments_df

    def get_payment_failures(self) -> pd.DataFrame:
        return self.payment_failures_df

    def get_recovery_attempts(self) -> pd.DataFrame:
        return self.recovery_attempts_df

    def get_gateway_events(self) -> pd.DataFrame:
        return self.gateway_events_df

# Global accessor function for easy imports
def get_data_service() -> DataService:
    return DataService()
