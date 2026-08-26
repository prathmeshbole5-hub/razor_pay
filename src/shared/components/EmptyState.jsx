import React from 'react';
import { AlertCircle, SearchX } from 'lucide-react';

export function EmptyState({
  title = 'No Data Found',
  description = 'Try adjusting your filters or search criteria.',
  icon: Icon = SearchX,
  action
}) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center rounded-2xl border border-dashed border-slate-800 bg-slate-900/40">
      <div className="p-4 rounded-full bg-slate-800/60 text-slate-400 mb-4">
        <Icon className="w-8 h-8" />
      </div>
      <h4 className="text-base font-semibold text-white mb-1">{title}</h4>
      <p className="text-sm text-slate-400 max-w-sm mb-6">{description}</p>
      {action && <div>{action}</div>}
    </div>
  );
}

export function LoadingSkeleton({ count = 3, type = 'card' }) {
  return (
    <div className="space-y-4 animate-pulse">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="h-20 bg-slate-800/50 rounded-xl border border-slate-800" />
      ))}
    </div>
  );
}

export function Toast({ message, type = 'info', onClose }) {
  const typeStyles = {
    info: 'border-cyan-500/30 bg-slate-900 text-cyan-300',
    success: 'border-emerald-500/30 bg-slate-900 text-emerald-300',
    warning: 'border-amber-500/30 bg-slate-900 text-amber-300',
    danger: 'border-rose-500/30 bg-slate-900 text-rose-300'
  };

  return (
    <div className={`fixed bottom-6 right-6 z-50 flex items-center gap-3 px-4 py-3 rounded-xl border shadow-xl backdrop-blur-md ${typeStyles[type]}`}>
      <span className="text-sm font-medium">{message}</span>
      <button onClick={onClose} className="text-slate-400 hover:text-white">×</button>
    </div>
  );
}
