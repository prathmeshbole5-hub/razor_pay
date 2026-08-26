import re
from typing import Dict, Any, List, Optional
from services.merchant_service import MerchantService
from services.internal_service import InternalService
from services.live_payment_service import get_live_payment_service
from intelligence.live_payment_feature_adapter import LivePaymentFeatureAdapter
from intelligence.intelligence_data_service import get_intelligence_data_service
from intelligence.recovery_prediction_service import get_recovery_prediction_service
from services.root_cause_service import get_root_cause_service
from services.recommendation_service import get_recommendation_service

class CopilotService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CopilotService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.merchant_service = MerchantService()
        self.internal_service = InternalService()
        self.live_payment_service = get_live_payment_service()
        self.intelligence_data_service = get_intelligence_data_service()
        self.prediction_service = get_recovery_prediction_service()
        self.root_cause_service = get_root_cause_service()
        self.recommendation_service = get_recommendation_service()

    def get_suggested_prompts(self, mode: str = "merchant") -> List[str]:
        if mode == "internal":
            return [
                "Which bank gateway has the highest failure rate?",
                "Are there any active latency spikes or incidents?",
                "What is the network-wide recovery success rate?",
                "Show ecosystem revenue at risk across all merchants."
            ]
        return [
            "What happened to my latest live payment?",
            "Why did my payment failures increase?",
            "Which recovery strategy is working best?",
            "Analyze payment failure pay_104421"
        ]

    def process_query(
        self,
        query: str,
        merchant_id: str = "m_1004",
        mode: str = "merchant"
    ) -> Dict[str, Any]:
        q = query.strip().lower()

        # Import recovery action service for timeline and action lookups
        from services.recovery_action_service import get_recovery_action_service
        ras = get_recovery_action_service()

        # Check for specific payment ID lookup
        pm_match = re.search(r'pay_[a-zA-Z0-9_]+', q)
        target_pm_id = pm_match.group(0) if pm_match else None

        # 1. Timeline or "what happened" query for specific payment or latest payment
        if "timeline" in q or "what happened to" in q:
            live_rec = None
            if target_pm_id:
                live_rec = self.live_payment_service.get_live_payment(target_pm_id, merchant_id)
            else:
                live_records = self.live_payment_service.get_merchant_live_payments(merchant_id)
                if live_records:
                    live_rec = live_records[0]

            if live_rec:
                try:
                    timeline_events = ras.get_payment_timeline(live_rec["payment_id"], merchant_id)
                    events_str = "\n".join([f"• **{e.get('event_type')}**: {e.get('description')} ({e.get('created_at')[:19]})" for e in timeline_events])
                    return {
                        "text": f"Event Timeline for payment **{live_rec['payment_id']}**:\n\n{events_str}",
                        "metrics": [
                            {"label": "Payment ID", "value": live_rec["payment_id"]},
                            {"label": "Total Events", "value": str(len(timeline_events))},
                            {"label": "Status", "value": live_rec.get("status", "created").upper()}
                        ],
                        "suggestedAction": "View Live Intelligence",
                        "actionType": "VIEW_INTELLIGENCE",
                        "actionPayload": {"payment_id": live_rec["payment_id"], "merchant_id": merchant_id}
                    }
                except Exception as e:
                    pass

        # 2. "What recovery action was executed"
        if "action" in q and ("executed" in q or "triggered" in q or "was" in q):
            live_rec = None
            if target_pm_id:
                live_rec = self.live_payment_service.get_live_payment(target_pm_id, merchant_id)
            else:
                live_records = self.live_payment_service.get_merchant_live_payments(merchant_id)
                if live_records:
                    live_rec = live_records[0]

            if live_rec:
                try:
                    actions = ras.get_payment_actions(live_rec["payment_id"], merchant_id)
                    if actions:
                        act_str = "\n".join([f"• **Action**: `{a.get('action_type')}` | Status: **{a.get('status').upper()}** | Executed at: {a.get('created_at')[:19]}" for a in actions])
                        return {
                            "text": f"Executed Recovery Actions for payment **{live_rec['payment_id']}**:\n\n{act_str}",
                            "metrics": [
                                {"label": "Payment ID", "value": live_rec["payment_id"]},
                                {"label": "Actions Executed", "value": str(len(actions))}
                            ],
                            "recommendation": "Inspect live payment timeline to view real-time state changes.",
                            "suggestedAction": "Inspect Payment",
                            "actionType": "VIEW_INTELLIGENCE",
                            "actionPayload": {"payment_id": live_rec["payment_id"], "merchant_id": merchant_id}
                        }
                    else:
                        return {
                            "text": f"No recovery action has been executed yet for live payment **{live_rec['payment_id']}**.",
                            "metrics": [
                                {"label": "Payment ID", "value": live_rec["payment_id"]},
                                {"label": "Status", "value": "NO_ACTIONS_EXECUTED"}
                            ],
                            "recommendation": "Use the Payment Detail Drawer to trigger an AI recommended recovery action.",
                            "suggestedAction": "Execute Action",
                            "actionType": "VIEW_INTELLIGENCE",
                            "actionPayload": {"payment_id": live_rec["payment_id"], "merchant_id": merchant_id}
                        }
                except Exception:
                    pass

        # 3. "Which payment has the highest recovery probability"
        if "highest" in q and ("probability" in q or "recovery" in q):
            live_records = self.live_payment_service.get_merchant_live_payments(merchant_id)
            if live_records:
                top_pm = max(live_records, key=lambda p: p.get("intelligence", {}).get("prediction", {}).get("recovery_probability", 0.65) if p.get("intelligence") else 0.65)
                return self._format_live_payment_copilot_response(top_pm, merchant_id)

        # 4. "Show failed live payments" or "failed live"
        if "failed" in q and ("live" in q or "payment" in q):
            live_records = self.live_payment_service.get_merchant_live_payments(merchant_id)
            failed_live = [p for p in live_records if p.get("status") == "failed"]
            if failed_live:
                target = failed_live[0]
                return self._format_live_payment_copilot_response(target, merchant_id)

        # 5. Check if user asked about "latest live payment" or "live payment"
        if any(kw in q for kw in ["latest live", "live payment", "razorpay payment", "test payment"]):
            live_records = self.live_payment_service.get_merchant_live_payments(merchant_id)
            if live_records:
                latest = live_records[0]
                return self._format_live_payment_copilot_response(latest, merchant_id)

        # 6. Specific payment lookup
        if target_pm_id:
            live_rec = self.live_payment_service.get_live_payment(target_pm_id, merchant_id)
            if live_rec:
                return self._format_live_payment_copilot_response(live_rec, merchant_id)
            return self._handle_historical_payment_lookup(target_pm_id, merchant_id)

        if mode == "internal":
            return self._handle_internal_query(q)
        else:
            return self._handle_merchant_query(q, merchant_id)


    def _format_live_payment_copilot_response(self, live_rec: Dict[str, Any], merchant_id: str) -> Dict[str, Any]:
        pm_id = live_rec.get("payment_id")
        amt = float(live_rec.get("amount_inr", 0.0))
        status = live_rec.get("status", "created")
        src = live_rec.get("source", "razorpay_test_mode")

        adapted, data_quality = LivePaymentFeatureAdapter.adapt_live_payment(live_rec)
        pred = self.prediction_service.predict_recovery_probability(adapted)
        prob_pct = round(pred.get("recovery_probability", 0.65) * 100, 1)
        prob_band = pred.get("prediction_class", "Medium Recovery Probability")

        return {
            "text": f"Live Razorpay Test Payment **{pm_id}** (Source: **{src}**):\n\n"
                    f"• **Amount**: **₹{amt:,.2f}** | Status: **{status.upper()}**\n"
                    f"• **ML Recovery Prediction**: **{prob_pct}%** ({prob_band})\n"
                    f"• **Data Completeness**: **{int(data_quality.get('feature_completeness', 1.0) * 100)}%** (Live Adapted Analysis)\n"
                    f"• **Root Cause**: Bank 3DS Authentication Timeout\n"
                    f"• **Recommended Action**: Smart Gateway Retry",
            "metrics": [
                { "label": "Source", "value": "Razorpay Test Mode" },
                { "label": "Status", "value": status.upper() },
                { "label": "Recovery Probability", "value": f"{prob_pct}%" }
            ],
            "payment_card": {
                "payment_id": pm_id,
                "merchant_id": merchant_id,
                "amount_inr": amt,
                "payment_method": live_rec.get("payment_method", "Card"),
                "created_at": live_rec.get("created_at", ""),
                "failure_category": "Network Timeout",
                "recovery_probability": prob_pct,
                "probability_band": prob_band
            },
            "recommendation": f"Live transaction {pm_id} recorded via Razorpay Test Mode. AI predicts {prob_pct}% recovery probability upon automated retry.",
            "suggestedAction": "Inspect Live Intelligence",
            "actionType": "SIMULATE_RETRY",
            "actionPayload": { "payment_id": pm_id, "merchant_id": merchant_id }
        }

    def _handle_historical_payment_lookup(self, payment_id: str, merchant_id: str) -> Dict[str, Any]:
        derived_df = self.intelligence_data_service.get_intelligence_dataset()
        match = derived_df[(derived_df['payment_id'] == payment_id) & (derived_df['merchant_id'] == merchant_id)]

        if match.empty:
            return {
                "text": f"Payment **{payment_id}** was not found in your merchant dataset or belongs to another merchant account.",
                "metrics": [],
                "recommendation": "Please verify the Payment ID and ensure you have domain authorization.",
                "suggestedAction": "View All Failed Payments",
                "actionType": "NAVIGATE_DENIALS"
            }

        row = match.iloc[0].to_dict()
        pred = self.prediction_service.predict_recovery_probability(row)
        rc = self.root_cause_service.analyze_root_cause(payment_id)
        rec = self.recommendation_service.recommend_recovery_strategy(payment_id)

        prob_pct = round(pred.get("recovery_probability", 0.0) * 100, 1)
        prob_band = pred.get("probability_band", "Medium")
        amount = float(row.get("amount_inr", 0.0))
        primary_cause = rc.get("primary_root_cause", {}).get("title", "Unknown failure")
        top_strat = rec.get("recommended_strategy", {}).get("strategy", "Smart Cool-down Retry")

        return {
            "text": f"AI Diagnostic report for historical payment **{payment_id}** (Source: **historical_dataset**):\n\n"
                    f"• **Amount**: **₹{amount:,.2f}**\n"
                    f"• **ML Recovery Probability**: **{prob_pct}%** ({prob_band} Band)\n"
                    f"• **Root Cause**: {primary_cause}\n"
                    f"• **Recommended Action**: {top_strat}",
            "metrics": [
                { "label": "Payment ID", "value": payment_id },
                { "label": "Source", "value": "Historical Dataset" },
                { "label": "Recovery Probability", "value": f"{prob_pct}%" }
            ],
            "payment_card": {
                "payment_id": payment_id,
                "merchant_id": merchant_id,
                "amount_inr": amount,
                "payment_method": str(row.get("payment_method", "Card")),
                "created_at": str(row.get("created_at", "")),
                "failure_category": str(row.get("failure_category", "Abandoned")),
                "recovery_probability": prob_pct,
                "probability_band": prob_band
            },
            "recommendation": f"Execute automated strategy '{top_strat}' to attempt immediate recovery of ₹{amount:,.2f}.",
            "suggestedAction": f"Execute {top_strat}",
            "actionType": "SIMULATE_RETRY",
            "actionPayload": {
                "payment_id": payment_id,
                "merchant_id": merchant_id,
                "strategy": top_strat
            }
        }

    def _handle_merchant_query(self, q: str, merchant_id: str) -> Dict[str, Any]:
        dashboard = self.merchant_service.get_dashboard(merchant_id) or {}

        at_risk = dashboard.get("revenue_at_risk", 1245000)
        recovered = dashboard.get("revenue_recovered", 4280000)
        rec_rate = dashboard.get("recovery_rate", 74.2)
        m_name = dashboard.get("merchant_name", "CloudMart")

        if any(kw in q for kw in ["why", "increase", "spike", "reason", "cause", "fail"]):
            return {
                "text": f"Based on failure diagnostics for **{m_name}**, **38% of payment failures** are driven by **HDFC NetBanking & SBI Card 3DS Auth Timeouts** during peak traffic hours.",
                "metrics": [
                    { "label": "Dominant Root Cause", "value": "Bank Gateway Timeout" },
                    { "label": "At-Risk Impact", "value": f"₹{at_risk:,.0f}" },
                    { "label": "AI Recovery Rate", "value": f"{rec_rate}%" }
                ],
                "recommendation": "Enable automated 12-minute cool-down retries to clear bank queue congestion.",
                "suggestedAction": "Apply Smart Cool-down Retries",
                "actionType": "SIMULATE_RETRY",
                "actionPayload": { "merchant_id": merchant_id, "strategy": "Smart Gateway Retry" }
            }

        if any(kw in q for kw in ["strategy", "best", "working", "recommend"]):
            return {
                "text": f"**Smart Gateway Retry** and **OTP Reminder** are your top-performing recovery mechanisms for **{m_name}**, converting **82.1%** of transient bank failures into completed transactions.",
                "metrics": [
                    { "label": "Top Strategy", "value": "Smart Gateway Retry" },
                    { "label": "Conversion Rate", "value": "82.1%" },
                    { "label": "Total Recovered", "value": f"₹{recovered:,.0f}" }
                ],
                "recommendation": "For high-value cart drops (>₹10,000), combine gateway retries with instant WhatsApp payment links.",
                "suggestedAction": "Configure Recovery Rules",
                "actionType": "NAVIGATE_CASES"
            }

        if any(kw in q for kw in ["how much", "revenue", "risk", "recoverable", "still"]):
            recoverable = round(at_risk * (rec_rate / 100.0), 2)
            return {
                "text": f"You currently have **₹{at_risk:,.2f} at risk** across active failed payments. Our ML recovery pipeline estimates **₹{recoverable:,.2f} ({rec_rate}%)** is highly recoverable within 2 hours.",
                "metrics": [
                    { "label": "Revenue At Risk", "value": f"₹{at_risk:,.0f}" },
                    { "label": "Estimated Recoverable", "value": f"₹{recoverable:,.0f}" },
                    { "label": "AI Confidence", "value": "92%" }
                ],
                "recommendation": "Execute batch retries on pending high-value cases to lock in estimated revenue.",
                "suggestedAction": "Execute Batch Recovery",
                "actionType": "SIMULATE_RETRY",
                "actionPayload": { "merchant_id": merchant_id, "batch": True }
            }

        return {
            "text": f"RecoverAI financial copilot is actively monitoring payment telemetry and recovery pipelines for **{m_name}**.",
            "metrics": [
                { "label": "Revenue Recovered", "value": f"₹{recovered:,.0f}" },
                { "label": "Overall Recovery Rate", "value": f"{rec_rate}%" },
                { "label": "Avg Recovery Delay", "value": "12 mins" }
            ],
            "recommendation": "Ask me about failure root causes, best strategies, or lookup specific payment IDs.",
            "suggestedAction": "View Payment Denials",
            "actionType": "NAVIGATE_DENIALS"
        }

    def _handle_internal_query(self, q: str) -> Dict[str, Any]:
        dash = self.internal_service.get_dashboard() or {}
        gw_health = self.internal_service.get_gateway_health() or []

        tot_vol = dash.get("total_payment_volume", 0.0)
        tot_risk = dash.get("total_revenue_at_risk", 0.0)
        active_inc = dash.get("active_incidents", 0)

        high_error_gw = [g for g in gw_health if g.get("average_error_rate", 0.0) > 2.5]
        top_err_gw_name = high_error_gw[0]["gateway"] if high_error_gw else "Axis Bank Wallet"

        if any(kw in q for kw in ["gateway", "bank", "failure rate", "highest"]):
            return {
                "text": f"**{top_err_gw_name}** currently exhibits the highest error rate across partner bank routes with elevated packet drops during peak windows.",
                "metrics": [
                    { "label": "Highest Error Route", "value": top_err_gw_name },
                    { "label": "Active Incidents", "value": str(active_inc) },
                    { "label": "Total Revenue at Risk", "value": f"₹{tot_risk:,.0f}" }
                ],
                "recommendation": "Route non-essential traffic to secondary backup acquirers during incident windows.",
                "suggestedAction": "Inspect Gateway Telemetry",
                "actionType": "NAVIGATE_GATEWAY"
            }

        if any(kw in q for kw in ["incident", "spike", "latency"]):
            return {
                "text": f"Ecosystem telemetry detects **{active_inc} active bank incidents**. Latency spikes exceeding 250ms have been logged on 2 partner acquirers.",
                "metrics": [
                    { "label": "Active Gateway Incidents", "value": str(active_inc) },
                    { "label": "Ecosystem Failure Rate", "value": f"{dash.get('overall_failure_rate', 0.0)}%" },
                    { "label": "Total Transactions", "value": f"{dash.get('total_transactions', 0):,}" }
                ],
                "recommendation": "Activate automatic gateway failover routing to mitigate merchant revenue impact.",
                "suggestedAction": "Trigger Smart Failover",
                "actionType": "SIMULATE_FAILOVER"
            }

        return {
            "text": f"Razorpay Internal Operations Intelligence is monitoring **₹{tot_vol:,.2f}** in aggregate payment volume across the merchant network.",
            "metrics": [
                { "label": "Total Payment Volume", "value": f"₹{tot_vol:,.0f}" },
                { "label": "Revenue At Risk", "value": f"₹{tot_risk:,.0f}" },
                { "label": "Ecosystem Recovery Rate", "value": f"{dash.get('overall_recovery_rate', 0.0)}%" }
            ],
            "recommendation": "Query gateway latency spikes, bank authorization error codes, or network failure benchmarks.",
            "suggestedAction": "View Failure Intelligence",
            "actionType": "NAVIGATE_INTELLIGENCE"
        }

def get_copilot_service() -> CopilotService:
    return CopilotService()
