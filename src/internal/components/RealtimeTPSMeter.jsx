import React, { useState, useEffect } from 'react';
import { Activity, ShieldCheck, Zap } from 'lucide-react';

export default function RealtimeTPSMeter({ initialTPS = 1842 }) {
  const [tps, setTps] = useState(initialTPS);

  // Micro jitter animation for realistic live feel
  useEffect(() => {
    const interval = setInterval(() => {
      const delta = Math.floor(Math.random() * 19) - 9;
      setTps((prev) => Math.max(1750, Math.min(1950, prev + delta)));
    }, 1500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-slate-900/90 border border-cyan-500/30 p-6 rounded-2xl shadow-xl flex items-center justify-between font-mono relative overflow-hidden">
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500" />
          </span>
          <span className="text-xs font-bold text-emerald-400 uppercase tracking-widest">LIVE TRANSACTIONS PER SECOND</span>
        </div>

        <div className="text-4xl sm:text-5xl font-black text-cyan-300 tracking-tight flex items-baseline gap-3">
          <span>{tps.toLocaleString()}</span>
          <span className="text-sm font-bold text-slate-400">TPS</span>
        </div>

        <p className="text-xs text-slate-400">Peak today: 2,140 TPS • 99.82% Global Success Rate</p>
      </div>

      <div className="hidden sm:flex flex-col items-end gap-2 text-right">
        <div className="px-3 py-1 rounded bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-bold">
          4,120 Recovery Retries / min
        </div>
        <span className="text-[10px] text-slate-500">Latency: 45ms (Razorpay Core)</span>
      </div>
    </div>
  );
}
