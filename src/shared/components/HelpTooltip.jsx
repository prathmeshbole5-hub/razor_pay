import React, { useState } from 'react';
import { HelpCircle } from 'lucide-react';

export default function HelpTooltip({ content, title, className = '' }) {
  const [isVisible, setIsVisible] = useState(false);

  if (!content) return null;

  return (
    <div
      className={`relative inline-flex items-center ${className}`}
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
      onFocus={() => setIsVisible(true)}
      onBlur={() => setIsVisible(false)}
    >
      <button
        type="button"
        aria-label={title || "More info"}
        className="text-slate-500 hover:text-slate-300 focus:outline-none transition-colors p-0.5"
      >
        <HelpCircle className="w-3.5 h-3.5" />
      </button>

      {isVisible && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-56 p-2.5 bg-slate-950 border border-slate-700 text-slate-200 text-[11px] font-medium rounded-xl shadow-xl z-50 pointer-events-none animate-fadeIn leading-relaxed">
          {title && <div className="font-bold text-white mb-1 border-b border-slate-800 pb-1">{title}</div>}
          <p>{content}</p>
          <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-slate-950" />
        </div>
      )}
    </div>
  );
}
