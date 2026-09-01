import React from 'react';
import HelpTooltip from './HelpTooltip';

export function Card({
  children,
  className = '',
  hover = true,
  padding = 'md',
  header,
  headerAction,
  footer
}) {
  const paddings = {
    none: 'p-0',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8'
  };

  return (
    <div
      className={`bg-slate-900/80 border border-slate-800 rounded-2xl backdrop-blur-sm transition-all duration-200 ${
        hover ? 'hover:border-slate-700 hover:shadow-lg hover:shadow-black/40 hover:-translate-y-0.5' : ''
      } ${className}`}
    >
      {(header || headerAction) && (
        <div className="flex items-center justify-between border-b border-slate-800/80 px-6 py-4">
          <div className="font-semibold text-slate-100">{header}</div>
          {headerAction && <div>{headerAction}</div>}
        </div>
      )}
      <div className={paddings[padding] || paddings.md}>{children}</div>
      {footer && (
        <div className="border-t border-slate-800/80 px-6 py-4 bg-slate-950/40 rounded-b-2xl">
          {footer}
        </div>
      )}
    </div>
  );
}

export function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  trendType = 'positive', // positive | negative | neutral
  accentColor = 'indigo', // indigo | emerald | rose | cyan | amber
  tooltip,
  className = ''
}) {
  const accentClasses = {
    indigo: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20',
    emerald: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    rose: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
    cyan: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
    amber: 'text-amber-400 bg-amber-500/10 border-amber-500/20'
  };

  const trendColors = {
    positive: 'text-emerald-400 bg-emerald-500/10',
    negative: 'text-rose-400 bg-rose-500/10',
    neutral: 'text-slate-400 bg-slate-800'
  };

  return (
    <Card className={`group relative overflow-hidden ${className}`}>
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-1.5">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">{title}</p>
            {tooltip && <HelpTooltip content={tooltip} title={title} />}
          </div>
          <div className="text-2xl sm:text-3xl font-bold text-white tracking-tight">{value}</div>
        </div>

        {Icon && (
          <div className={`p-3 rounded-xl border ${accentClasses[accentColor] || accentClasses.indigo} transition-transform duration-300 group-hover:scale-110`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      {(subtitle || trend) && (
        <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
          {subtitle && <span className="text-slate-400">{subtitle}</span>}
          {trend && (
            <span className={`px-2 py-0.5 rounded-full font-semibold ${trendColors[trendType]}`}>
              {trend}
            </span>
          )}
        </div>
      )}
    </Card>
  );
}
