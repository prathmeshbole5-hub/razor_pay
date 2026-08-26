import React, { useState, useEffect } from 'react';
import { ResponsiveContainer, BarChart, Bar, Cell, XAxis, YAxis, Tooltip } from 'recharts';
import { Card } from '../../shared/components/Card';
import Badge from '../../shared/components/Badge';
import Button from '../../shared/components/Button';
import { AlertCircle } from 'lucide-react';
import { getGatewayHealth, getRecoveryIntelligence } from '../../api/internalApi';

export default function InternalAnalytics() {
  const [gateways, setGateways] = useState([]);
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [gwData, stratData] = await Promise.all([
        getGatewayHealth(),
        getRecoveryIntelligence()
      ]);
      setGateways(gwData || []);
      setStrategies(stratData || []);
    } catch (err) {
      console.error('Failed to load internal analytics data:', err);
      setError(err.message || 'Failed to load internal analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="space-y-8 animate-fadeIn font-mono p-4">
        <div className="h-16 bg-slate-900/80 border border-slate-800 rounded-2xl animate-pulse" />
        <div className="h-72 bg-slate-900/80 border border-slate-800 rounded-2xl animate-pulse" />
        <div className="h-72 bg-slate-900/80 border border-slate-800 rounded-2xl animate-pulse" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-rose-950/40 border border-rose-500/30 p-6 rounded-2xl space-y-4 animate-fadeIn font-mono">
        <div className="flex items-center gap-3 text-rose-400 font-bold">
          <AlertCircle className="w-5 h-5" />
          <span>Failed to load internal analytics telemetry</span>
        </div>
        <p className="text-xs text-slate-300">{error}</p>
        <Button variant="outline" size="sm" onClick={loadData}>
          Retry Telemetry Feed
        </Button>
      </div>
    );
  }

  const bankChartData = gateways.map((g) => ({
    bank: g.gateway,
    successRate: g.average_success_rate,
    errorRate: g.average_error_rate
  }));

  return (
    <div className="space-y-8 animate-fadeIn font-mono">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white">Ecosystem Gateway & Recovery Strategy Analytics</h2>
          <p className="text-xs text-slate-400">Network-wide gateway telemetry, bank success rate correlations, and AI strategy effectiveness.</p>
        </div>

        <Badge variant="brand" size="md">
          Live Dataset Archive
        </Badge>
      </div>

      {/* Bank Success Comparison Bar Chart */}
      <Card header="Partner Gateway Success Rate Benchmarking" hover={false}>
        <div className="h-64 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={bankChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <XAxis dataKey="bank" stroke="#64748b" fontSize={11} tickLine={false} />
              <YAxis domain={[70, 100]} stroke="#64748b" fontSize={11} tickLine={false} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0e131f', borderColor: '#334155', borderRadius: '12px', fontSize: '12px', color: '#fff' }}
                formatter={(val) => [`${val}%`, 'Success Rate']}
              />
              <Bar dataKey="successRate" radius={[6, 6, 0, 0]}>
                {bankChartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.successRate < 90 ? '#ff2a5f' : entry.successRate < 96 ? '#fbbf24' : '#10b981'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Recovery Intelligence Strategy Matrix */}
      <Card header="Recovery Intelligence Strategy Conversion Matrix" hover={false}>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider font-semibold">
              <tr>
                <th className="py-3 px-4">Recovery Strategy</th>
                <th className="py-3 px-4">Total Attempts</th>
                <th className="py-3 px-4">Successful Attempts</th>
                <th className="py-3 px-4">Recovered Amount</th>
                <th className="py-3 px-4">Predicted Prob. Avg</th>
                <th className="py-3 px-4 text-right">Success Rate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {strategies.map((st) => (
                <tr key={st.strategy} className="hover:bg-slate-800/40">
                  <td className="py-3.5 px-4 font-semibold text-white">{st.strategy}</td>
                  <td className="py-3.5 px-4 font-mono">{st.total_attempts.toLocaleString('en-IN')}</td>
                  <td className="py-3.5 px-4 font-mono font-bold text-emerald-400">{st.successful_attempts}</td>
                  <td className="py-3.5 px-4 font-bold text-slate-200">
                    ₹{((st.recovered_amount_inr || 0) / 100000).toFixed(2)}L
                  </td>
                  <td className="py-3.5 px-4 font-mono text-cyan-400 font-bold">
                    {(st.average_predicted_recovery_probability * 100).toFixed(1)}%
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <Badge variant={st.success_rate > 40 ? 'success' : st.success_rate > 25 ? 'brand' : 'warning'} size="sm">
                      {st.success_rate}%
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
