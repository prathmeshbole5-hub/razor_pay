import React from 'react';
import {
  ShoppingBag,
  CreditCard,
  CheckCircle2,
  AlertCircle,
  Database,
  Sparkles,
  Search,
  Zap,
  RefreshCw,
  Clock,
  Check
} from 'lucide-react';
import Badge from '../../shared/components/Badge';

export default function LivePaymentTimeline({ timeline = [] }) {
  if (!timeline || timeline.length === 0) {
    return (
      <div className="text-center py-6 text-xs text-slate-500 bg-slate-950/60 rounded-xl border border-slate-800">
        No payment events recorded in timeline yet.
      </div>
    );
  }

  const getEventMeta = (eventType) => {
    switch (eventType) {
      case 'ORDER_CREATED':
        return { icon: ShoppingBag, color: 'text-indigo-400', bg: 'bg-indigo-500/10 border-indigo-500/30' };
      case 'PAYMENT_ATTEMPTED':
        return { icon: CreditCard, color: 'text-cyan-400', bg: 'bg-cyan-500/10 border-cyan-500/30' };
      case 'PAYMENT_SUCCESS':
        return { icon: CheckCircle2, color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/30' };
      case 'PAYMENT_FAILED':
        return { icon: AlertCircle, color: 'text-rose-400', bg: 'bg-rose-500/10 border-rose-500/30' };
      case 'WEBHOOK_RECEIVED':
      case 'WEBHOOK_VERIFIED':
        return { icon: Database, color: 'text-purple-400', bg: 'bg-purple-500/10 border-purple-500/30' };
      case 'ML_ANALYSIS_COMPLETED':
        return { icon: Sparkles, color: 'text-indigo-300', bg: 'bg-indigo-500/10 border-indigo-500/30' };
      case 'ROOT_CAUSE_IDENTIFIED':
        return { icon: Search, color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/30' };
      case 'RECOMMENDATION_GENERATED':
        return { icon: Zap, color: 'text-cyan-300', bg: 'bg-cyan-500/10 border-cyan-500/30' };
      case 'RECOVERY_ACTION_EXECUTED':
        return { icon: RefreshCw, color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/30' };
      default:
        return { icon: Clock, color: 'text-slate-400', bg: 'bg-slate-800 border-slate-700' };
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5 text-indigo-400" />
          Live Payment Event Timeline
        </h4>
        <span className="text-[10px] text-slate-500 font-mono">
          {timeline.length} Event{timeline.length > 1 ? 's' : ''} Logged
        </span>
      </div>

      <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
        {timeline.map((item, idx) => {
          const meta = getEventMeta(item.event_type);
          const Icon = meta.icon;
          const isLast = idx === timeline.length - 1;

          return (
            <div key={idx} className="relative flex items-start gap-3 group">
              {/* Timeline Node Icon */}
              <div className={`absolute -left-6 top-0.5 w-5 h-5 rounded-full ${meta.bg} border flex items-center justify-center shadow-md transition-transform group-hover:scale-110 z-10 bg-slate-950`}>
                <Icon className={`w-3 h-3 ${meta.color}`} />
              </div>

              {/* Event Body */}
              <div className="bg-slate-950/80 border border-slate-800/80 hover:border-indigo-500/30 p-3 rounded-xl flex-1 transition-all">
                <div className="flex items-center justify-between gap-2 mb-1">
                  <span className={`text-xs font-bold tracking-tight ${meta.color}`}>
                    {item.event_type.replace(/_/g, ' ')}
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono shrink-0">
                    {item.created_at ? item.created_at.replace('T', ' ').slice(0, 19) : 'Just now'}
                  </span>
                </div>
                <p className="text-xs text-slate-300 leading-snug">
                  {item.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
