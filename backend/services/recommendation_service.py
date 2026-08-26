import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from services.data_service import get_data_service
from intelligence.intelligence_data_service import get_intelligence_data_service
from intelligence.recovery_prediction_service import get_recovery_prediction_service

ALL_STRATEGIES = [
    "Retry after 10 minutes",
    "Smart gateway retry",
    "Alternate payment method",
    "UPI payment link",
    "Email reminder",
    "OTP reminder"
]

class RecommendationService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RecommendationService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.data_service = get_data_service()
        self.intelligence_service = get_intelligence_data_service()
        self.prediction_service = get_recovery_prediction_service()
        self._precompute_strategy_benchmarks()

    def _precompute_strategy_benchmarks(self):
        """Precomputes historical strategy success rates from recovery_attempts dataset"""
        derived_df = self.intelligence_service.get_intelligence_dataset()
        
        # Overall strategy success rates
        strat_stats = derived_df.groupby('strategy').agg(
            total_attempts=('payment_id', 'count'),
            recovered_count=('recovered', 'sum')
        ).reset_index()

        strat_stats['success_rate'] = (strat_stats['recovered_count'] / strat_stats['total_attempts']).round(4)
        self.overall_strategy_rates = strat_stats.set_index('strategy')['success_rate'].to_dict()

        # Category-level strategy success rates
        cat_stats = derived_df.groupby(['failure_category', 'strategy']).agg(
            total_attempts=('payment_id', 'count'),
            recovered_count=('recovered', 'sum')
        ).reset_index()
        cat_stats['success_rate'] = (cat_stats['recovered_count'] / cat_stats['total_attempts']).round(4)
        
        self.category_strategy_rates = {}
        for _, r in cat_stats.iterrows():
            key = (r['failure_category'], r['strategy'])
            self.category_strategy_rates[key] = float(r['success_rate'])

    def _get_strategy_compatibility(self, failure_category: str, strategy: str) -> float:
        """Returns deterministic domain compatibility score between failure category and recovery strategy"""
        matrix = {
            'User Abandoned': {
                'OTP reminder': 1.0,
                'Email reminder': 0.90,
                'UPI payment link': 0.85,
                'Alternate payment method': 0.60,
                'Retry after 10 minutes': 0.40,
                'Smart gateway retry': 0.30
            },
            'Bank Declined': {
                'Alternate payment method': 1.0,
                'UPI payment link': 0.85,
                'Email reminder': 0.70,
                'OTP reminder': 0.60,
                'Retry after 10 minutes': 0.30,
                'Smart gateway retry': 0.20
            },
            'Network Timeout': {
                'Smart gateway retry': 1.0,
                'Retry after 10 minutes': 0.95,
                'Alternate payment method': 0.75,
                'UPI payment link': 0.60,
                'OTP reminder': 0.40,
                'Email reminder': 0.30
            },
            'Gateway Error': {
                'Smart gateway retry': 1.0,
                'Retry after 10 minutes': 0.95,
                'Alternate payment method': 0.80,
                'UPI payment link': 0.65,
                'OTP reminder': 0.40,
                'Email reminder': 0.30
            },
            'OTP Failed': {
                'OTP reminder': 1.0,
                'UPI payment link': 0.85,
                'Email reminder': 0.75,
                'Alternate payment method': 0.60,
                'Retry after 10 minutes': 0.30,
                'Smart gateway retry': 0.20
            },
            'Insufficient Funds': {
                'UPI payment link': 1.0,
                'Alternate payment method': 0.90,
                'Email reminder': 0.80,
                'OTP reminder': 0.70,
                'Retry after 10 minutes': 0.40,
                'Smart gateway retry': 0.20
            }
        }
        
        cat_matrix = matrix.get(failure_category, {})
        return float(cat_matrix.get(strategy, 0.50))

    def recommend_recovery_strategy(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """
        Determines the optimal recovery strategy using historical success rates, ML recovery probability,
        and failure category compatibility.
        """
        derived_df = self.intelligence_service.get_intelligence_dataset()
        match = derived_df[derived_df['payment_id'] == payment_id]

        if match.empty:
            return None

        row = match.iloc[0].to_dict()
        failure_category = str(row.get('failure_category', 'Unknown'))
        retryable = bool(row.get('retryable', True))

        # Get ML Recovery Prediction
        pred_res = self.prediction_service.predict_recovery_probability(row)
        ml_prob = float(pred_res.get('recovery_probability', 0.50))

        # Rank all 6 strategies deterministically
        ranked_list = []

        for strat in ALL_STRATEGIES:
            # 1. Historical success rate for this category + strategy
            hist_rate = self.category_strategy_rates.get(
                (failure_category, strat),
                self.overall_strategy_rates.get(strat, 0.35)
            )

            # 2. Category compatibility
            compat = self._get_strategy_compatibility(failure_category, strat)

            # 3. Deterministic Recommendation Score Formula
            # Score = 0.40 * hist_rate + 0.35 * ml_prob + 0.15 * compat + 0.10 * retryable
            rec_score = float(round(
                (0.40 * hist_rate) +
                (0.35 * ml_prob) +
                (0.15 * compat) +
                (0.10 * (1.0 if retryable else 0.5)),
                4
            ))

            expected_prob = float(round(min(hist_rate * 0.5 + ml_prob * 0.5, 0.98), 4))

            # Strategy specific reason
            if strat == "Smart gateway retry":
                reason = f"Automatically reroutes transaction to secondary healthy gateway for {failure_category} failures."
            elif strat == "Retry after 10 minutes":
                reason = f"Allows temporary bank server latency spike to resolve before re-submitting transaction."
            elif strat == "Alternate payment method":
                reason = f"Prompts customer to switch payment instrument to bypass issuing bank authorization decline."
            elif strat == "UPI payment link":
                reason = f"Sends instant 1-click UPI collect request to customer mobile device."
            elif strat == "Email reminder":
                reason = f"Sends automated payment link email to customer for abandoned checkout recovery."
            else: # OTP reminder
                reason = f"Sends SMS 2FA reminder with direct authorization link."

            ranked_list.append({
                "strategy": strat,
                "recommendation_score": rec_score,
                "expected_recovery_probability": expected_prob,
                "historical_success_rate": float(round(hist_rate, 4)),
                "reason": reason
            })

        # Sort strategies descending by recommendation score
        ranked_list.sort(key=lambda x: x['recommendation_score'], reverse=True)

        top_strategy = ranked_list[0]
        alternatives = ranked_list[1:3] # Top 2 alternatives

        return {
            "payment_id": payment_id,
            "recommended_strategy": top_strategy,
            "alternative_strategies": alternatives
        }

def get_recommendation_service() -> RecommendationService:
    return RecommendationService()
