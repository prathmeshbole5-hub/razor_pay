import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import Button from '../Button';

export default function IntelligenceErrorState({ error, onRetry }) {
  return (
    <div className="bg-rose-950/40 border border-rose-500/30 rounded-xl p-4 space-y-3 font-mono text-xs">
      <div className="flex items-center gap-2 text-rose-400 font-bold">
        <AlertCircle className="w-4 h-4" />
        <span>Failed to load AI Recovery Intelligence</span>
      </div>
      <p className="text-slate-300 leading-relaxed">{error || 'Backend AI service unavailable.'}</p>
      {onRetry && (
        <Button variant="outline" size="sm" icon={RefreshCw} onClick={onRetry}>
          Retry AI Diagnostics
        </Button>
      )}
    </div>
  );
}
