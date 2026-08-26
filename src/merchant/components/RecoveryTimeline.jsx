import React from 'react';
import { CheckCircle2, Clock, AlertTriangle, ArrowRight, Zap, RefreshCw } from 'lucide-react';
import Badge from '../../shared/components/Badge';

export default function RecoveryTimeline({ timeline = [] }) {
  const getEventIcon = (type) => {
    switch (type) {
      case 'success':
        return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-amber-400" />;
      case 'error':
        return <AlertTriangle className="w-4 h-4 text-rose-400" />;
      case 'info':
      default:
        return <Zap className="w-4 h-4 text-indigo-400" />;
    }
  };

  return (
    <div className="space-y-4">
      <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Failure & Recovery Timeline</h4>
      <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
        {timeline.map((item, idx) => (
          <div key={idx} className="relative group">
            <div className="absolute -left-6 top-0.5 p-1 rounded-full bg-slate-900 border border-slate-700 shadow-sm">
              {getEventIcon(item.type)}
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-200">{item.event}</span>
              <span className="text-slate-500 font-mono">{item.time}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
