import React from 'react';
import { Cpu, Activity, ShieldAlert, Sparkles } from 'lucide-react';
import Badge from '../Badge';

export default function IntelligenceSummaryCard({ intelligence }) {
  if (!intelligence) return null;

  const pred = intelligence.prediction || {};
  const rc = intelligence.root_cause || {};
  const rec = intelligence.recommendation || {};

  const pct = Math.round((parseFloat(pred.recovery_probability) || 0.50) * 100);
  const band = pred.prediction_class || 'Medium Recovery Probability';
  const causeTitle = rc.primary_root_cause?.title || rc.primary_root_cause?.category || 'Authorization Decline';
  const recStrategy = rec.recommended_strategy?.strategy || 'Smart gateway retry';

  const isHigh = pct >= 70;
  const isMedium = pct >= 40 && pct < 70;
  const badgeVariant = isHigh ? 'success' : isMedium ? 'warning' : 'danger';

  return (
    <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3 font-mono text-xs">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 font-bold text-slate-200">
          <Cpu className="w-4 h-4 text-cyan-400" />
          <span>🤖 AI Recovery Intelligence Summary</span>
        </div>
        <Badge variant={badgeVariant} size="sm">
          {pct}% Probability ({band})
        </Badge>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
        <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800/80">
          <span className="text-slate-500 block text-[10px] uppercase font-semibold">Recovery Probability</span>
          <span className={`font-bold text-sm ${isHigh ? 'text-emerald-400' : isMedium ? 'text-amber-400' : 'text-rose-400'}`}>
            {pct}%
          </span>
        </div>

        <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800/80">
          <span className="text-slate-500 block text-[10px] uppercase font-semibold">Root Cause</span>
          <span className="font-bold text-xs text-white truncate block">{causeTitle}</span>
        </div>

        <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800/80">
          <span className="text-slate-500 block text-[10px] uppercase font-semibold">Recommended Action</span>
          <span className="font-bold text-xs text-indigo-400 truncate block">{recStrategy}</span>
        </div>
      </div>
    </div>
  );
}
