import React from 'react';
import {
  Activity,
  Server,
  AlertTriangle,
  Network,
  GitMerge,
  BarChart2,
  Shield,
  Radio,
  Cpu
} from 'lucide-react';

export default function InternalSidebar({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'overview', label: 'Ecosystem Overview', icon: Activity, badge: 'LIVE' },
    { id: 'gateway', label: 'Gateway & Bank Health', icon: Server, badge: '1 Outage' },
    { id: 'intelligence', label: 'Failure Intelligence', icon: AlertTriangle, badge: '2 Alerts' },
    { id: 'network', label: 'Merchant Network', icon: Network, badge: '4.8k Active' },
    { id: 'flow', label: 'System Flow Diagram', icon: GitMerge, badge: 'Interactive' },
    { id: 'analytics', label: 'Internal Analytics', icon: BarChart2, badge: null }
  ];

  return (
    <aside className="w-64 bg-slate-950 border-r border-cyan-500/20 flex flex-col justify-between h-screen sticky top-0 z-40 select-none font-mono">
      {/* Brand Header */}
      <div>
        <div className="p-6 border-b border-cyan-500/20">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-cyan-500 flex items-center justify-center text-slate-950 font-black shadow-lg shadow-cyan-500/30">
              <Cpu className="w-6 h-6" />
            </div>
            <div>
              <div className="text-sm font-extrabold tracking-tight text-cyan-200 flex items-center gap-1.5">
                RAZORPAY<span className="text-cyan-400">OPS</span>
              </div>
              <div className="text-[10px] uppercase font-bold text-cyan-400 tracking-wider">RecoverAI Command</div>
            </div>
          </div>
        </div>

        {/* Telemetry Nav Items */}
        <nav className="p-4 space-y-1.5">
          <div className="px-3 py-2 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
            Infrastructure Monitoring
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all duration-200 group ${
                  isActive
                    ? 'bg-cyan-500 text-slate-950 shadow-lg shadow-cyan-500/25 font-bold'
                    : 'text-slate-400 hover:text-cyan-200 hover:bg-slate-900/80 border border-transparent hover:border-cyan-500/20'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-slate-950' : 'text-slate-500 group-hover:text-cyan-400'}`} />
                  <span>{item.label}</span>
                </div>

                {item.badge && (
                  <span
                    className={`text-[9px] font-extrabold px-2 py-0.5 rounded ${
                      isActive
                        ? 'bg-slate-950 text-cyan-400'
                        : item.badge === '1 Outage'
                        ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                        : 'bg-slate-900 text-slate-400 border border-slate-800'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Telemetry Live Pulse Footer Widget */}
      <div className="p-4 border-t border-cyan-500/20">
        <div className="bg-slate-900 border border-cyan-500/20 p-3 rounded-xl space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400">System Telemetry</span>
            <span className="text-emerald-400 font-bold flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
              ONLINE
            </span>
          </div>
          <div className="text-[10px] text-slate-400 space-y-1">
            <div className="flex justify-between">
              <span>Cluster Node:</span>
              <span className="text-cyan-300 font-bold">rzp-asia-south1</span>
            </div>
            <div className="flex justify-between">
              <span>Failure Recovery Engine:</span>
              <span className="text-emerald-400 font-bold">4,120 retries/m</span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
