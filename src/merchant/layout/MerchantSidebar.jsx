import React from 'react';
import {
  LayoutDashboard,
  CreditCard,
  RefreshCw,
  Bot,
  BarChart3,
  User,
  ShieldCheck,
  Zap,
  ChevronRight,
  Activity
} from 'lucide-react';

export default function MerchantSidebar({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, badge: null },
    { id: 'live-payments', label: 'Live Payments', icon: Activity, badge: 'Live DB' },
    { id: 'denials', label: 'Payment Denials', icon: CreditCard, badge: '24 Failed' },
    { id: 'cases', label: 'Recovery Cases', icon: RefreshCw, badge: '14 Active' },
    { id: 'copilot', label: 'AI Copilot', icon: Bot, badge: 'AI Assistant' },
    { id: 'analytics', label: 'Analytics', icon: BarChart3, badge: null },
    { id: 'profile', label: 'Merchant Profile', icon: User, badge: null }
  ];


  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800/80 flex flex-col justify-between h-screen sticky top-0 z-40 select-none">
      {/* Brand Header */}
      <div>
        <div className="p-6 border-b border-slate-800/80">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-indigo-600 flex items-center justify-center text-white shadow-lg shadow-indigo-600/30">
              <Zap className="w-5 h-5 fill-current" />
            </div>
            <div>
              <div className="text-base font-extrabold tracking-tight text-white flex items-center gap-1.5">
                RECOVER<span className="text-indigo-400">AI</span>
              </div>
              <div className="text-[10px] uppercase font-bold text-indigo-400 tracking-wider">Merchant Portal</div>
            </div>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="p-4 space-y-1.5">
          <div className="px-3 py-2 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
            Revenue Recovery
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all duration-200 group ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/25 font-semibold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 transition-transform duration-200 ${isActive ? 'text-white' : 'text-slate-500 group-hover:text-slate-300'}`} />
                  <span>{item.label}</span>
                </div>

                {item.badge && (
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      isActive
                        ? 'bg-white/20 text-white'
                        : item.badge.includes('AI')
                        ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20'
                        : 'bg-slate-800 text-slate-400'
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

      {/* Bottom Merchant Summary Widget */}
      <div className="p-4 border-t border-slate-800/80">
        <div className="bg-slate-900/90 border border-slate-800 p-3.5 rounded-2xl space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400 font-medium">Recovery Rate</span>
            <span className="text-emerald-400 font-bold">74.2%</span>
          </div>
          <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-indigo-500 to-emerald-400 w-[74.2%]" />
          </div>
          <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
            <span>₹42.8L Recovered</span>
            <span className="text-slate-400 font-semibold">+3.8% MoM</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
