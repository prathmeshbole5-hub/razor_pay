import React from 'react';
import { Server, AlertTriangle, CheckCircle2, XCircle, Activity, ArrowRightLeft } from 'lucide-react';
import Badge from '../../shared/components/Badge';
import Button from '../../shared/components/Button';

export default function GatewayStatusCard({ gateway, onTriggerRouteSwitch }) {
  const statusStyles = {
    HEALTHY: {
      border: 'border-emerald-500/30 hover:border-emerald-500/60',
      badge: 'success',
      icon: CheckCircle2,
      iconColor: 'text-emerald-400',
      glow: ''
    },
    DEGRADED: {
      border: 'border-amber-500/40 hover:border-amber-500/70',
      badge: 'warning',
      icon: AlertTriangle,
      iconColor: 'text-amber-400',
      glow: 'shadow-lg shadow-amber-950/40'
    },
    OUTAGE: {
      border: 'border-rose-500/60 hover:border-rose-500/90 bg-gradient-to-b from-rose-950/20 to-slate-900',
      badge: 'danger',
      icon: XCircle,
      iconColor: 'text-rose-400 animate-pulse',
      glow: 'shadow-xl shadow-rose-950/60 border-2'
    }
  }[gateway.status] || {
    border: 'border-slate-800',
    badge: 'default',
    icon: Server,
    iconColor: 'text-slate-400',
    glow: ''
  };

  const Icon = statusStyles.icon;

  return (
    <div className={`bg-slate-900/90 border ${statusStyles.border} ${statusStyles.glow} rounded-2xl p-5 space-y-4 font-mono transition-all duration-200`}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={`p-2.5 rounded-xl bg-slate-950 border border-slate-800 ${statusStyles.iconColor}`}>
            <Icon className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-white">{gateway.name}</h4>
            <span className="text-[10px] text-slate-400">{gateway.type}</span>
          </div>
        </div>

        <Badge variant={statusStyles.badge} dot pulse={gateway.status === 'OUTAGE'} size="sm">
          {gateway.status}
        </Badge>
      </div>

      {/* Metrics breakdown */}
      <div className="grid grid-cols-2 gap-3 text-xs bg-slate-950 p-3 rounded-xl border border-slate-800/80">
        <div>
          <span className="text-[10px] text-slate-400 block">Success Rate</span>
          <span className={`font-bold ${gateway.successRate < 90 ? 'text-rose-400 font-black' : gateway.successRate < 97 ? 'text-amber-400' : 'text-emerald-400'}`}>
            {gateway.successRate}%
          </span>
        </div>

        <div>
          <span className="text-[10px] text-slate-400 block">Latency</span>
          <span className={`font-bold ${gateway.latencyMs > 1000 ? 'text-rose-400' : 'text-slate-200'}`}>
            {gateway.latencyMs}ms
          </span>
        </div>

        <div>
          <span className="text-[10px] text-slate-400 block">Failure Spike</span>
          <span className={`font-bold ${gateway.failureSpikePct > 20 ? 'text-rose-400' : 'text-slate-300'}`}>
            +{gateway.failureSpikePct}%
          </span>
        </div>

        <div>
          <span className="text-[10px] text-slate-400 block">Impacted Merchants</span>
          <span className="font-bold text-white">{gateway.affectedMerchants}</span>
        </div>
      </div>

      {/* Action / Warning info */}
      {gateway.status !== 'HEALTHY' && (
        <div className="flex items-center justify-between pt-1">
          <span className="text-[10px] text-rose-300 font-semibold truncate max-w-[200px]">
            {gateway.errorDominant}
          </span>

          <Button
            variant={gateway.status === 'OUTAGE' ? 'danger' : 'accent'}
            size="sm"
            icon={ArrowRightLeft}
            onClick={() => onTriggerRouteSwitch && onTriggerRouteSwitch(gateway.id)}
          >
            Reroute Traffic
          </Button>
        </div>
      )}
    </div>
  );
}
