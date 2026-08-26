import React from 'react';
import { Activity, ShieldCheck, Cpu } from 'lucide-react';
import Badge from '../Badge';

export default function RecoveryProbabilityCard({ prediction }) {
  if (!prediction) return null;

  const prob = floatVal(prediction.recovery_probability);
  const pct = Math.round(prob * 100);
  const band = prediction.prediction_class || 'Medium Recovery Probability';
  const confidencePct = Math.round(floatVal(prediction.confidence_score) * 100);

  const isHigh = pct >= 70;
  const isMedium = pct >= 40 && pct < 70;

  const barColor = isHigh ? 'bg-emerald-400' : isMedium ? 'bg-amber-400' : 'bg-rose-500';
  const textColor = isHigh ? 'text-emerald-400' : isMedium ? 'text-amber-400' : 'text-rose-400';
  const badgeVariant = isHigh ? 'success' : isMedium ? 'warning' : 'danger';

  return (
    <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3 font-mono">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs font-bold text-slate-300">
          <Activity className="w-4 h-4 text-cyan-400" />
          <span>ML Recovery Probability</span>
        </div>
        <Badge variant={badgeVariant} size="sm">
          {band}
        </Badge>
      </div>

      <div className="flex items-baseline justify-between pt-1">
        <div className={`text-3xl font-extrabold ${textColor}`}>
          {pct}%
        </div>
        <div className="text-xs text-slate-400">
          Confidence Score: <strong className="text-white">{confidencePct}%</strong>
        </div>
      </div>

      {/* Visual Progress Bar Indicator */}
      <div className="space-y-1">
        <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
          <div
            className={`h-full ${barColor} transition-all duration-500 rounded-full`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <div className="flex justify-between text-[10px] text-slate-500 pt-0.5">
          <span>Low (0%)</span>
          <span>Medium (40%)</span>
          <span>High (70%+)</span>
        </div>
      </div>

      <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1 border-t border-slate-900">
        <span className="flex items-center gap-1">
          <Cpu className="w-3 h-3 text-slate-400" />
          Model: {prediction.model_type || 'RandomForestClassifier'}
        </span>
        <span>Version: {prediction.model_version || '1.0.0'}</span>
      </div>
    </div>
  );
}

function floatVal(val) {
  const num = parseFloat(val);
  return isNaN(num) ? 0.0 : num;
}
