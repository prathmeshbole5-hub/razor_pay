import React, { useState } from 'react';
import { AlertTriangle, ChevronDown, ChevronUp, ShieldAlert, CheckCircle2 } from 'lucide-react';
import Badge from '../Badge';

export default function RootCauseCard({ rootCause }) {
  if (!rootCause) return null;

  const [expanded, setExpanded] = useState(false);

  const primary = rootCause.primary_root_cause || {};
  const factors = rootCause.contributing_factors || [];
  const confPct = Math.round((parseFloat(primary.confidence) || 0.85) * 100);

  return (
    <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3 font-mono text-xs">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 font-bold text-slate-300">
          <ShieldAlert className="w-4 h-4 text-amber-400" />
          <span>AI Root Cause Diagnostics</span>
        </div>
        <Badge variant="warning" size="sm">
          {confPct}% Confidence
        </Badge>
      </div>

      <div className="space-y-1.5 pt-1">
        <div className="text-sm font-bold text-white">
          {primary.title || primary.category || 'Payment Authorization Failure'}
        </div>
        <p className="text-slate-300 text-[11px] leading-relaxed">
          {primary.reason || 'Failure detected during payment gateway authorization.'}
        </p>
      </div>

      {/* Contributing Factors Accordion */}
      {factors.length > 0 && (
        <div className="pt-2 border-t border-slate-900 space-y-2">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center justify-between w-full text-[11px] text-slate-400 hover:text-white transition-colors"
          >
            <span>Contributing Factors ({factors.length})</span>
            {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {expanded && (
            <div className="space-y-2 pt-1">
              {factors.map((fac, idx) => {
                const impactVariant = fac.impact === 'High' ? 'danger' : fac.impact === 'Medium' ? 'warning' : 'info';
                return (
                  <div key={idx} className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800/80 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-200">{fac.factor}</span>
                      <Badge variant={impactVariant} size="sm">{fac.impact} Impact</Badge>
                    </div>
                    <p className="text-[10px] text-slate-400">{fac.detail}</p>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
