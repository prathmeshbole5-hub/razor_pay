import React from 'react';
import { Sparkles } from 'lucide-react';

export default function IntelligenceLoadingState() {
  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-4 font-mono animate-fadeIn">
      <div className="flex items-center gap-2 text-indigo-400">
        <Sparkles className="w-4 h-4 animate-spin" />
        <span className="text-xs font-bold uppercase tracking-wider">Analyzing Payment Failure via RecoverAI ML Pipeline...</span>
      </div>

      <div className="space-y-3">
        <div className="h-16 bg-slate-950/80 border border-slate-800/80 rounded-xl animate-pulse" />
        <div className="h-24 bg-slate-950/80 border border-slate-800/80 rounded-xl animate-pulse" />
        <div className="h-24 bg-slate-950/80 border border-slate-800/80 rounded-xl animate-pulse" />
      </div>
    </div>
  );
}
