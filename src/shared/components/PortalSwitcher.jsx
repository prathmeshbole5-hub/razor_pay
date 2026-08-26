import React from 'react';
import { Building2, ShieldAlert, ArrowRightLeft } from 'lucide-react';
import { CURRENT_MERCHANT_NAME } from '../../config/currentMerchant';

export default function PortalSwitcher({ currentPortal, onPortalChange }) {
  const shortMerchantName = CURRENT_MERCHANT_NAME.split(' ')[0];

  return (
    <div className="flex items-center gap-2 bg-slate-900/90 border border-slate-800 p-1.5 rounded-xl shadow-lg">
      <button
        onClick={() => onPortalChange('merchant')}
        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 ${
          currentPortal === 'merchant'
            ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/20'
            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
        }`}
      >
        <Building2 className="w-3.5 h-3.5" />
        <span>Merchant Portal</span>
        <span className="hidden sm:inline-block text-[10px] opacity-75 font-normal ml-1 bg-black/20 px-1.5 py-0.5 rounded">{shortMerchantName}</span>
      </button>

      <div className="w-px h-4 bg-slate-800" />

      <button
        onClick={() => onPortalChange('internal')}
        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 ${
          currentPortal === 'internal'
            ? 'bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/20'
            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
        }`}
      >
        <ShieldAlert className="w-3.5 h-3.5" />
        <span>Razorpay Internal</span>
        <span className="hidden sm:inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
          LIVE
        </span>
      </button>
    </div>
  );
}
