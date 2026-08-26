import React from 'react';
import { Activity, ShieldAlert, Radio, AlertTriangle, ChevronDown } from 'lucide-react';
import PortalSwitcher from '../../shared/components/PortalSwitcher';

export default function InternalTopbar({ currentPortal, onPortalChange, activePageTitle = 'Overview' }) {
  return (
    <header className="sticky top-0 z-30 bg-slate-950 border-b border-cyan-500/20 backdrop-blur-md px-4 sm:px-8 py-3 flex items-center justify-between gap-4">
      {/* Left Title & Command Status */}
      <div className="flex items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold text-cyan-300 font-mono tracking-tight">{activePageTitle}</h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 font-mono">
              DEGRADED_PERFORMANCE
            </span>
          </div>
          <p className="text-[11px] text-slate-400 font-mono hidden sm:block">
            Razorpay Core Payment Telemetry & Infrastructure Operations Center
          </p>
        </div>
      </div>

      {/* Center: Global Portal Switcher */}
      <div className="hidden md:block">
        <PortalSwitcher currentPortal={currentPortal} onPortalChange={onPortalChange} />
      </div>

      {/* Right Telemetry Controls */}
      <div className="flex items-center gap-3">
        <div className="block md:hidden">
          <PortalSwitcher currentPortal={currentPortal} onPortalChange={onPortalChange} />
        </div>

        {/* Live TPS Counter Badge */}
        <div className="flex items-center gap-2 bg-slate-900 border border-cyan-500/30 px-3 py-1.5 rounded-xl font-mono">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500" />
          </span>
          <span className="text-xs font-extrabold text-white">1,842</span>
          <span className="text-[10px] text-cyan-400 font-bold">TPS</span>
        </div>

        {/* Active Incidents Alert Pill */}
        <div className="hidden sm:flex items-center gap-1.5 bg-rose-500/10 border border-rose-500/30 px-3 py-1.5 rounded-xl font-mono text-xs text-rose-400">
          <AlertTriangle className="w-3.5 h-3.5 animate-bounce" />
          <span className="font-bold">2 Incidents Active</span>
        </div>

        {/* User Profile */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-600 to-blue-600 flex items-center justify-center text-xs font-bold text-white shadow-md font-mono">
            OPS
          </div>
          <div className="hidden lg:block text-left font-mono">
            <div className="text-xs font-bold text-cyan-200">Ops Engineer</div>
            <div className="text-[9px] text-slate-400">Razorpay Infrastructure</div>
          </div>
        </div>
      </div>
    </header>
  );
}
