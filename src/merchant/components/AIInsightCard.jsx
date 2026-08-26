import React from 'react';
import { Sparkles, ArrowRight, Zap, AlertTriangle, ShieldCheck } from 'lucide-react';
import Button from '../../shared/components/Button';
import Badge from '../../shared/components/Badge';

export default function AIInsightCard({ insight, onReviewCases }) {
  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-indigo-950/80 via-slate-900 to-slate-900 border border-indigo-500/30 p-6 sm:p-8 shadow-2xl shadow-indigo-950/40">
      {/* Glow decorative element */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl -z-10 pointer-events-none" />

      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
        <div className="space-y-3 max-w-2xl">
          <div className="flex items-center gap-3">
            <Badge variant="brand" pulse dot size="md">
              <Sparkles className="w-3.5 h-3.5 mr-1" />
              AI RECOVERY INSIGHT
            </Badge>
            <span className="text-xs text-indigo-300 font-semibold">{insight.confidenceScore}% Confidence</span>
          </div>

          <h3 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            {insight.title}
          </h3>

          <p className="text-sm text-slate-300 leading-relaxed">
            {insight.description}
          </p>

          <div className="flex items-center gap-2 pt-1 text-xs text-indigo-300 font-medium bg-indigo-900/30 border border-indigo-500/20 px-3.5 py-2 rounded-xl">
            <Zap className="w-4 h-4 text-indigo-400 shrink-0" />
            <span><strong className="text-white">AI Recommendation:</strong> {insight.recommendation}</span>
          </div>
        </div>

        {/* Action & Metric highlight box */}
        <div className="w-full lg:w-auto flex flex-col sm:flex-row lg:flex-col items-stretch lg:items-end justify-between gap-4 border-t lg:border-t-0 lg:border-l border-slate-800 pt-4 lg:pt-0 lg:pl-8">
          <div>
            <div className="text-xs text-slate-400 font-medium">Potential Recoverable Revenue</div>
            <div className="text-2xl sm:text-3xl font-extrabold text-emerald-400 tracking-tight">
              ₹{insight.potentialRecovery.toLocaleString('en-IN')}
            </div>
            <div className="text-[11px] text-slate-500">{insight.affectedPaymentsCount} affected transactions queued</div>
          </div>

          <Button
            variant="primary"
            size="md"
            icon={ArrowRight}
            iconPosition="right"
            onClick={onReviewCases}
            className="w-full sm:w-auto"
          >
            {insight.actionText || 'Review Cases'}
          </Button>
        </div>
      </div>
    </div>
  );
}
