import React, { useState } from 'react';
import { AlertTriangle, Sparkles, ShieldAlert, ArrowRight, CheckCircle2 } from 'lucide-react';
import Button from '../../shared/components/Button';
import Badge from '../../shared/components/Badge';

export default function AnomalyAlertBanner({ anomaly, onMitigate }) {
  const [mitigated, setMitigated] = useState(false);

  const handleMitigate = () => {
    setMitigated(true);
    if (onMitigate) onMitigate(anomaly.id);
  };

  return (
    <div className={`relative overflow-hidden rounded-2xl border p-6 font-mono ${
      anomaly.severity === 'CRITICAL'
        ? 'bg-gradient-to-r from-rose-950/80 via-slate-900 to-slate-900 border-rose-500/50 shadow-2xl shadow-rose-950/50'
        : 'bg-gradient-to-r from-amber-950/60 via-slate-900 to-slate-900 border-amber-500/40 shadow-xl'
    }`}>
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
        <div className="space-y-2 max-w-3xl">
          <div className="flex items-center gap-3">
            <Badge variant={anomaly.severity === 'CRITICAL' ? 'danger' : 'warning'} pulse dot size="sm">
              AI ANOMALY DETECTED • {anomaly.severity}
            </Badge>
            <span className="text-xs text-cyan-300 font-bold">{anomaly.confidenceScore}% Confidence</span>
          </div>

          <h3 className="text-lg font-bold text-white tracking-tight">
            {anomaly.title}
          </h3>

          <p className="text-xs text-slate-300 leading-relaxed">
            {anomaly.description}
          </p>

          <div className="flex items-center gap-2 pt-1 text-xs text-cyan-300 font-medium bg-slate-950 border border-slate-800 p-2.5 rounded-xl">
            <Sparkles className="w-4 h-4 text-cyan-400 shrink-0" />
            <span><strong>Recommended System Action:</strong> {anomaly.recommendedAction}</span>
          </div>
        </div>

        {/* Impact Box & Mitigate Trigger */}
        <div className="w-full lg:w-auto flex flex-col sm:flex-row lg:flex-col items-stretch lg:items-end justify-between gap-4 border-t lg:border-t-0 lg:border-l border-slate-800 pt-4 lg:pt-0 lg:pl-8 shrink-0">
          <div className="space-y-1 text-left lg:text-right">
            <span className="text-[10px] text-slate-400 block uppercase font-bold">Estimated Impact</span>
            <div className="text-xl font-extrabold text-rose-400">
              ₹{(anomaly.estimatedRevenueImpact / 100000).toFixed(1)}L At Risk
            </div>
            <div className="text-[10px] text-slate-400 font-bold">
              {anomaly.affectedMerchants} Merchants • {anomaly.impactedTransactions} Transactions
            </div>
          </div>

          {mitigated ? (
            <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold bg-emerald-500/10 border border-emerald-500/30 px-4 py-2 rounded-xl">
              <CheckCircle2 className="w-4 h-4" /> Mitigation Executed
            </div>
          ) : (
            <Button
              variant={anomaly.severity === 'CRITICAL' ? 'danger' : 'accent'}
              size="md"
              icon={ArrowRight}
              iconPosition="right"
              onClick={handleMitigate}
            >
              Execute Mitigation Reroute
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
