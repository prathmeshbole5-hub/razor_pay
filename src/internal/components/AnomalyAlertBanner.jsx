import React, { useState } from 'react';
import { AlertTriangle, Sparkles, ShieldAlert, ArrowRight, CheckCircle2 } from 'lucide-react';
import Button from '../../shared/components/Button';
import Badge from '../../shared/components/Badge';

export default function AnomalyAlertBanner({ anomaly, onMitigate, onViewAffectedPayments }) {
  const [mitigated, setMitigated] = useState(anomaly?.status === 'MITIGATED');
  const [isExecuting, setIsExecuting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleMitigate = async () => {
    setIsExecuting(true);
    setErrorMsg('');
    const incId = anomaly.id || anomaly.incident_id;
    try {
      if (onMitigate) {
        await onMitigate(incId);
      }
      setMitigated(true);
    } catch (err) {
      console.error('Mitigation execution failed:', err);
      setErrorMsg(err.message || 'Mitigation failed. Retry');
    } finally {
      setIsExecuting(false);
    }
  };

  const isTestWebhook = anomaly.source === 'razorpay_test_webhook';
  const impactVal = Number(anomaly.estimatedRevenueImpact || anomaly.amount_at_risk || 0);
  const formattedImpact = impactVal >= 100000
    ? `₹${(impactVal / 100000).toFixed(1)}L At Risk`
    : `₹${impactVal.toLocaleString('en-IN')} At Risk`;

  return (
    <div className={`relative overflow-hidden rounded-2xl border p-6 font-mono ${
      anomaly.severity === 'CRITICAL'
        ? 'bg-gradient-to-r from-rose-950/80 via-slate-900 to-slate-900 border-rose-500/50 shadow-2xl shadow-rose-950/50'
        : 'bg-gradient-to-r from-amber-950/60 via-slate-900 to-slate-900 border-amber-500/40 shadow-xl'
    }`}>
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
        <div className="space-y-2 max-w-3xl">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={anomaly.severity === 'CRITICAL' ? 'danger' : 'warning'} pulse dot size="sm">
              AI ANOMALY DETECTED • {anomaly.severity}
            </Badge>
            {isTestWebhook && (
              <Badge variant="brand" size="sm">
                RAZORPAY TEST MODE
              </Badge>
            )}
            <span className="text-xs text-cyan-300 font-bold">{anomaly.confidenceScore || 95}% Confidence</span>
          </div>

          <h3 className="text-lg font-bold text-white tracking-tight">
            {anomaly.title}
          </h3>

          <p className="text-xs text-slate-300 leading-relaxed">
            {anomaly.description}
          </p>

          {anomaly.payment_id && (
            <div className="text-[11px] text-slate-400 font-semibold flex items-center gap-2 pt-0.5">
              <span>Affected Payment:</span>
              <span className="text-cyan-400 font-mono font-bold bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                {anomaly.payment_id}
              </span>
              {anomaly.gateway && (
                <span>• Gateway: <strong className="text-slate-200">{anomaly.gateway}</strong></span>
              )}
            </div>
          )}

          <div className="flex items-center gap-2 pt-1 text-xs text-cyan-300 font-medium bg-slate-950 border border-slate-800 p-2.5 rounded-xl">
            <Sparkles className="w-4 h-4 text-cyan-400 shrink-0" />
            <span><strong>Recommended System Action:</strong> {anomaly.recommendedAction || anomaly.recommended_mitigation}</span>
          </div>

          {errorMsg && (
            <div className="text-xs text-rose-400 font-semibold bg-rose-950/60 border border-rose-500/30 p-2 rounded-xl">
              {errorMsg}
            </div>
          )}
        </div>

        {/* Impact Box & Actions Trigger */}
        <div className="w-full lg:w-auto flex flex-col sm:flex-row lg:flex-col items-stretch lg:items-end justify-between gap-4 border-t lg:border-t-0 lg:border-l border-slate-800 pt-4 lg:pt-0 lg:pl-8 shrink-0">
          <div className="space-y-1 text-left lg:text-right">
            <span className="text-[10px] text-slate-400 block uppercase font-bold">Estimated Impact</span>
            <div className="text-xl font-extrabold text-rose-400">
              {formattedImpact}
            </div>
            <div className="text-[10px] text-slate-400 font-bold">
              {anomaly.affectedMerchants || 1} Merchants • {anomaly.impactedTransactions || 1} Transactions
            </div>
          </div>

          <div className="flex flex-col gap-2 w-full">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onViewAffectedPayments && onViewAffectedPayments(anomaly)}
              className="w-full text-slate-200 border-slate-700 hover:border-cyan-500/50 hover:text-cyan-300 text-xs py-2"
            >
              View Affected Payments ({anomaly.impactedTransactions || 1})
            </Button>

            {mitigated || anomaly.status === 'MITIGATED' ? (
              <div className="flex flex-col items-center lg:items-end gap-1">
                <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold bg-emerald-500/10 border border-emerald-500/30 px-3 py-1.5 rounded-xl w-full justify-center">
                  <CheckCircle2 className="w-4 h-4" /> Mitigation Executed
                </div>
                <span className="text-[10px] text-slate-500 font-bold">TEST SIMULATION MODE</span>
              </div>
            ) : (
              <Button
                variant={anomaly.severity === 'CRITICAL' ? 'danger' : 'accent'}
                size="md"
                icon={ArrowRight}
                iconPosition="right"
                disabled={isExecuting}
                onClick={handleMitigate}
              >
                {isExecuting ? 'Executing mitigation...' : 'Execute Mitigation Reroute'}
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
