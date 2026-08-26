import pandas as pd
import random
from typing import Dict, Any, List
from datetime import datetime
from services.data_service import get_data_service

class SimulationService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SimulationService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.data_service = get_data_service()
        self.reset_simulation()

    def reset_simulation(self):
        """Resets the in-memory simulation event stream to clean baseline state"""
        self.events: List[Dict[str, Any]] = [
            {
                "event_id": "sim_evt_1001",
                "timestamp": datetime.now().isoformat(),
                "event_type": "PAYMENT_FAILURE_DETECTED",
                "payment_id": "pay_104421",
                "merchant_id": "m_1004",
                "amount_inr": 2823.02,
                "failure_category": "User Abandoned",
                "gateway": "ICICI UPI",
                "status": "FAILURE_LOGGED"
            },
            {
                "event_id": "sim_evt_1002",
                "timestamp": datetime.now().isoformat(),
                "event_type": "AI_DIAGNOSTICS_COMPLETED",
                "payment_id": "pay_104421",
                "recovery_probability": 0.5928,
                "recommended_strategy": "OTP reminder",
                "status": "STRATEGY_SCHEDULED"
            }
        ]

    def get_events(self) -> List[Dict[str, Any]]:
        """Returns in-memory event stream"""
        return self.events

    def simulate_event(self, event_type: str = "failure") -> Dict[str, Any]:
        """
        Generates a new simulated event in memory without modifying original CSV source datasets.
        """
        now_str = datetime.now().isoformat()
        sample_payment_id = f"pay_sim_{random.randint(10000, 99999)}"
        
        gateways = ["Axis Wallet", "HDFC Gateway", "ICICI UPI", "Razorpay", "SBI Card Gateway"]
        categories = ["User Abandoned", "Bank Declined", "Network Timeout", "Gateway Error", "OTP Failed"]
        strategies = ["Smart gateway retry", "Retry after 10 minutes", "OTP reminder", "UPI payment link"]

        if event_type == "gateway_spike":
            gw = random.choice(gateways)
            new_event = {
                "event_id": f"sim_evt_{random.randint(2000, 9999)}",
                "timestamp": now_str,
                "event_type": "GATEWAY_LATENCY_SPIKE",
                "gateway": gw,
                "latency_ms": random.randint(350, 600),
                "error_rate_pct": float(round(random.uniform(4.5, 9.8), 2)),
                "status": "INCIDENT_ALERT"
            }
        elif event_type == "recovery":
            new_event = {
                "event_id": f"sim_evt_{random.randint(2000, 9999)}",
                "timestamp": now_str,
                "event_type": "AUTOMATED_RECOVERY_SUCCESS",
                "payment_id": sample_payment_id,
                "merchant_id": f"m_100{random.randint(0, 4)}",
                "amount_inr": float(round(random.uniform(500.0, 8500.0), 2)),
                "executed_strategy": random.choice(strategies),
                "status": "REVENUE_PROTECTED"
            }
        else: # failure event
            new_event = {
                "event_id": f"sim_evt_{random.randint(2000, 9999)}",
                "timestamp": now_str,
                "event_type": "PAYMENT_FAILURE_DETECTED",
                "payment_id": sample_payment_id,
                "merchant_id": f"m_100{random.randint(0, 4)}",
                "amount_inr": float(round(random.uniform(200.0, 9500.0), 2)),
                "failure_category": random.choice(categories),
                "gateway": random.choice(gateways),
                "status": "FAILURE_LOGGED"
            }

        self.events.insert(0, new_event)
        if len(self.events) > 50:
            self.events = self.events[:50]

        return new_event

def get_simulation_service() -> SimulationService:
    return SimulationService()
