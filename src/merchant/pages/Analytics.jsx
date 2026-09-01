import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Card } from '../../shared/components/Card';
import Badge from '../../shared/components/Badge';
import Button from '../../shared/components/Button';
import { AlertTriangle } from 'lucide-react';
import { getMerchantAnalytics } from '../../api/merchantApi';
import { CURRENT_MERCHANT_ID } from '../../config/currentMerchant';

export default function Analytics() {
  const [timeframe, setTimeframe] = useState('30D');
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getMerchantAnalytics(CURRENT_MERCHANT_ID);
      setAnalyticsData(res);
    } catch (err) {
      console.error('Failed to fetch merchant analytics data:', err);
      setError(err.message || 'Failed to fetch analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="space-y-8 animate-fadeIn p-4">
        <div className="h-16 bg-slate-900/80 border border-slate-800 rounded-2xl animate-pulse" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="h-80 bg-slate-900/80 border border-slate-800 rounded-2xl animate-pulse" />
          <div className="h-80 bg-slate-900/80 border border-slate-800 rounded-2xl animate-pulse" />
        </div>
        <div className="h-64 bg-slate-900/80 border border-slate-800 rounded-2xl animate-pulse" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-rose-950/40 border border-rose-500/30 p-6 rounded-2xl space-y-4 animate-fadeIn">
        <div className="flex items-center gap-3 text-rose-400 font-bold">
          <AlertTriangle className="w-5 h-5" />
          <span>Failed to load merchant analytics</span>
        </div>
        <p className="text-xs text-slate-300">{error}</p>
        <Button variant="outline" size="sm" onClick={loadData}>
          Retry Connection
        </Button>
      </div>
    );
  }

  const rawReasons = analyticsData?.failures_by_reason || [];
  const totalFailures = rawReasons.reduce((acc, curr) => acc + curr.count, 0) || 1;

  const colorPalette = ['#f43f5e', '#8b5cf6', '#3b82f6', '#06b6d4', '#10b981', '#f59e0b', '#ec4899'];

  const failureReasonsChart = rawReasons.map((item, idx) => ({
    name: item.reason,
    count: item.count,
    value: Math.round((item.count / totalFailures) * 100),
    color: colorPalette[idx % colorPalette.length]
  }));

  const strategyPerformance = (analyticsData?.recovery_performance_by_strategy || []).map((s) => ({
    strategy: s.strategy,
    rate: s.success_rate,
    attempts: s.total_attempts,
    recovered: s.successful_attempts,
    revenue: s.recovered_amount
  }));

  const methodFailures = analyticsData?.failures_by_payment_method || [];
  const totalMethodFailures = methodFailures.reduce((sum, m) => sum + m.count, 0) || 1;

  const methodBreakdown = methodFailures.map((m) => {
    return {
      name: m.method,
      volume: m.volume || 0,
      failures: m.count,
      recoveryRate: m.recovery_rate || 0
    };
  });

  const core = analyticsData?.core_metrics;

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white">Merchant Recovery & Failure Analytics</h2>
          <p className="text-xs text-slate-400">Deep-dive breakdown into failure reasons, payment methods, and AI strategy conversion rates.</p>
        </div>

        <div className="flex items-center gap-2">
          {['7D', '30D', '3M', '6M'].map((tf) => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-xl border transition-all ${
                timeframe === tf
                  ? 'bg-indigo-600 border-indigo-500 text-white shadow-md'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              {tf}
            </button>
          ))}
        </div>
      </div>

      {/* Top Summary KPI Cards if available */}
      {core && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-2xl space-y-1">
            <span className="text-xs text-slate-400 font-medium">Total Volume</span>
            <div className="text-2xl font-extrabold text-white">
              ₹{(core.total_volume || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
            <span className="text-[10px] text-slate-500 font-mono">{core.total_transactions || 0} total transactions</span>
          </div>

          <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-2xl space-y-1">
            <span className="text-xs text-slate-400 font-medium">Revenue At Risk</span>
            <div className="text-2xl font-extrabold text-rose-400">
              ₹{(core.revenue_at_risk || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
            <span className="text-[10px] text-slate-500 font-mono">{core.failed_transactions || 0} failed payments</span>
          </div>

          <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-2xl space-y-1">
            <span className="text-xs text-slate-400 font-medium">Revenue Recovered</span>
            <div className="text-2xl font-extrabold text-emerald-400">
              ₹{(core.revenue_recovered || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
            <span className="text-[10px] text-slate-500 font-mono">{core.recovered_cases || 0} confirmed recovered cases</span>
          </div>

          <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-2xl space-y-1">
            <span className="text-xs text-slate-400 font-medium">Recovery Rate</span>
            <div className="text-2xl font-extrabold text-cyan-400">
              {(core.recovery_rate || 0).toFixed(2)}%
            </div>
            <span className="text-[10px] text-slate-500 font-mono">Confirmed recovery ratio</span>
          </div>
        </div>
      )}

      {/* Grid 1: Failure Reason Distribution & AI Strategy Effectiveness */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Failure Reason Bar Chart */}
        <Card header="Top Failure Reasons" hover={false}>
          {failureReasonsChart.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-xs text-slate-500">
              No failure records found in database
            </div>
          ) : (
            <>
              <div className="h-64 w-full pt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={failureReasonsChart} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <XAxis dataKey="name" stroke="#64748b" fontSize={10} tickLine={false} />
                    <YAxis stroke="#64748b" fontSize={10} tickLine={false} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', fontSize: '12px', color: '#fff' }}
                      formatter={(val, name, item) => [`${val}% (${item.payload.count} txns)`, 'Share']}
                    />
                    <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                      {failureReasonsChart.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="grid grid-cols-2 gap-2 pt-4 border-t border-slate-800 text-xs">
                {failureReasonsChart.map((fr) => (
                  <div key={fr.name} className="flex items-center justify-between p-2 rounded-lg bg-slate-950">
                    <span className="text-slate-400 font-medium truncate">{fr.name}</span>
                    <span className="font-bold text-white">{fr.count} txns</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </Card>

        {/* Strategy Conversion Performance */}
        <Card header="AI Strategy Effectiveness" hover={false}>
          <div className="space-y-4 pt-2">
            {strategyPerformance.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-xs text-slate-500">
                No strategy performance data calculated yet
              </div>
            ) : (
              strategyPerformance.map((sc) => (
                <div key={sc.strategy} className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-white">{sc.strategy}</span>
                    <span className="text-emerald-400 font-extrabold">{sc.rate}% Conversion</span>
                  </div>

                  <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-indigo-500 to-emerald-400"
                      style={{ width: `${sc.rate}%` }}
                    />
                  </div>

                  <div className="flex justify-between text-[11px] text-slate-400 pt-1">
                    <span>{sc.attempts} attempts ({sc.recovered} recovered)</span>
                    <span className="text-white font-bold">₹{(sc.revenue || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })} Recovered</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>

      {/* Grid 2: Payment Method Breakdown Table */}
      <Card header="Payment Method Failure & Recovery Matrix" hover={false}>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider font-semibold">
              <tr>
                <th className="py-3 px-4">Payment Method</th>
                <th className="py-3 px-4">Failed Count</th>
                <th className="py-3 px-4">Failed Volume (₹)</th>
                <th className="py-3 px-4">Percentage Share</th>
                <th className="py-3 px-4 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {methodBreakdown.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-slate-500 text-xs">
                    No payment method failure records found in database
                  </td>
                </tr>
              ) : (
                methodBreakdown.map((mb) => {
                  const share = Math.round((mb.failures / totalMethodFailures) * 100);
                  return (
                    <tr key={mb.name} className="hover:bg-slate-800/40">
                      <td className="py-3.5 px-4 font-semibold text-white">{mb.name}</td>
                      <td className="py-3.5 px-4 font-bold text-slate-200">{mb.failures} failures</td>
                      <td className="py-3.5 px-4 font-mono text-amber-400">₹{(mb.volume || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                      <td className="py-3.5 px-4 text-indigo-300 font-mono">{share}% of total</td>
                      <td className="py-3.5 px-4 text-right">
                        <Badge variant={share < 40 ? 'success' : 'warning'} size="sm">
                          {share < 40 ? 'Optimal' : 'High Failure Volume'}
                        </Badge>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
