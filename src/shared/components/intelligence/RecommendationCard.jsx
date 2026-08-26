import React from 'react';
import { Sparkles, ArrowRight, CheckCircle2, RefreshCw } from 'lucide-react';
import Badge from '../Badge';

export default function RecommendationCard({ recommendation }) {
  if (!recommendation) return null;

  const rec = recommendation.recommended_strategy || {};
  const alternatives = recommendation.alternative_strategies || [];

  const recScore = Math.round((parseFloat(rec.recommendation_score) || 0.65) * 100);
  const expProb = Math.round((parseFloat(rec.expected_recovery_probability) || 0.50) * 100);

  return (
    <div className="bg-gradient-to-br from-indigo-950/60 to-slate-950 p-4 rounded-xl border border-indigo-500/30 space-y-3 font-mono text-xs">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 font-bold text-indigo-300">
          <Sparkles className="w-4 h-4 text-indigo-400" />
          <span>AI Recommended Recovery Strategy</span>
        </div>
        <Badge variant="brand" size="sm">
          {recScore}% AI Recommendation Score
        </Badge>
      </div>

      {/* Top Strategy Highlight */}
      <div className="bg-slate-950/80 p-3 rounded-xl border border-indigo-500/20 space-y-2">
        <div className="flex items-center justify-between">
          <div className="text-sm font-bold text-white flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            {rec.strategy || 'Smart gateway retry'}
          </div>
          <span className="text-[11px] font-bold text-emerald-400">
            {expProb}% Exp. Recovery Rate
          </span>
        </div>

        <p className="text-[11px] text-slate-300 leading-normal">
          {rec.reason || 'Based on comparable historical payment failure resolutions and current payment parameters.'}
        </p>
      </div>

      {/* Alternative Strategies */}
      {alternatives.length > 0 && (
        <div className="space-y-1.5 pt-1">
          <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Alternative Recovery Options</span>
          <div className="space-y-1">
            {alternatives.map((alt, idx) => {
              const altScore = Math.round((parseFloat(alt.recommendation_score) || 0.45) * 100);
              const altHist = Math.round((parseFloat(alt.historical_success_rate) || 0.35) * 100);
              return (
                <div key={idx} className="flex items-center justify-between bg-slate-950/60 p-2 rounded-lg border border-slate-800 text-[11px]">
                  <span className="text-slate-300 font-semibold">{alt.strategy}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-slate-400">{altHist}% Hist. Rate</span>
                    <span className="text-indigo-400 font-bold">{altScore}% Score</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
