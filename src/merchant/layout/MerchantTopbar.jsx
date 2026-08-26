import React from 'react';
import { Search, Bell, Sparkles, ChevronDown } from 'lucide-react';
import PortalSwitcher from '../../shared/components/PortalSwitcher';
import { CURRENT_MERCHANT_NAME } from '../../config/currentMerchant';

export default function MerchantTopbar({ currentPortal, onPortalChange, activePageTitle = 'Dashboard' }) {
  const initials = CURRENT_MERCHANT_NAME.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();

  return (
    <header className="sticky top-0 z-30 bg-slate-950/80 border-b border-slate-800/80 backdrop-blur-md px-4 sm:px-8 py-3 flex items-center justify-between gap-4">
      {/* Left section: Page title & Business Context */}
      <div className="flex items-center gap-4">
        <div>
          <h1 className="text-lg font-bold text-white tracking-tight">{activePageTitle}</h1>
          <p className="text-xs text-slate-400 hidden sm:block">{CURRENT_MERCHANT_NAME} • RecoverAI Merchant Hub</p>
        </div>
      </div>

      {/* Center: Global Portal Switcher */}
      <div className="hidden md:block">
        <PortalSwitcher currentPortal={currentPortal} onPortalChange={onPortalChange} />
      </div>

      {/* Right section: Search, Actions, Profile */}
      <div className="flex items-center gap-3">
        {/* Mobile Portal Switcher Trigger */}
        <div className="block md:hidden">
          <PortalSwitcher currentPortal={currentPortal} onPortalChange={onPortalChange} />
        </div>

        {/* Quick Search */}
        <div className="relative hidden xl:block">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search payment ID, email..."
            className="w-64 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-200 placeholder-slate-500 pl-9 pr-4 py-2 focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>

        {/* AI Quick Indicator */}
        <div className="hidden sm:flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 px-3 py-1.5 rounded-xl">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
          <span className="text-xs font-semibold text-indigo-300">AI Recovery Active</span>
        </div>

        {/* Notification Bell */}
        <button className="relative p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800 transition-colors">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-indigo-500" />
        </button>

        {/* Merchant Avatar */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center text-xs font-bold text-white shadow-md">
            {initials}
          </div>
          <div className="hidden lg:block text-left">
            <div className="text-xs font-semibold text-white leading-tight">Alex Rivera</div>
            <div className="text-[10px] text-slate-400">Head of Payments</div>
          </div>
          <ChevronDown className="w-3.5 h-3.5 text-slate-500 hidden lg:block" />
        </div>
      </div>
    </header>
  );
}
