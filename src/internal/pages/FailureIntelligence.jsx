import React, { useState, useEffect } from 'react';
import { Sparkles, Flame, AlertCircle, ShieldAlert } from 'lucide-react';
import { failureAnomalies } from '../../data/internalData';
import AnomalyAlertBanner from '../components/AnomalyAlertBanner';
import { Card } from '../../shared/components/Card';
import Badge from '../../shared/components/Badge';
import Button from '../../shared/components/Button';
import { getFailureIntelligence } from '../../api/internalApi';

export default function FailureIntelligence() {
  const [failures, setFailures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getFailureIntelligence();
      setFailures(data || []);
    } catch (err) {
      console.error('Failed to fetch failure intelligence:', err);
      setError(err.message || 'Failed to load failure intelligence');
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
        <div className="h-44 bg-slate-900/80 border border-slate-800 rounded-2xl animate-pulse" />
        <div className="h-80 bg-slate-900/80 border border-slate-800 rounded-2xl animate-pulse" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-rose-950/40 border border-rose-500/30 p-6 rounded-2xl space-y-4 animate-fadeIn font-mono">
        <div className="flex items-center gap-3 text-rose-400 font-bold">
          <AlertCircle className="w-5 h-5" />
          <span>Failed to load failure intelligence matrix</span>
        </div>
        <p className="text-xs text-slate-300">{error}</p>
        <Button variant="outline" size="sm" onClick={loadData}>
          Retry Connection
        </Button>
      </div>
    );
  }

  const totalAtRisk = failures.reduce((sum, f) => sum + f.total_amount_at_risk, 0);
  const totalAtRiskLakhs = (totalAtRisk / 100000).toFixed(1);

  return (
    <div className="space-y-8 animate-fadeIn font-mono">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-cyan-400" />
            AI Failure Intelligence & Anomaly Matrix
          </h2>
          <p className="text-xs text-slate-400">
            Ecosystem payment failure analysis identifying failure spikes, risk exposure, and cross-gateway patterns.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="brand" pulse size="md">
            ₹{totalAtRiskLakhs}L Total Risk Analyzed
          </Badge>
        </div>
      </div>

      {/* Active Anomaly Alerts Stream */}
      <div className="space-y-4">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Detected System Anomalies</h3>
        {failureAnomalies.map((anom) => (
          <AnomalyAlertBanner key={anom.id} anomaly={anom} />
        ))}
      </div>

      {/* Failure Heatmap Matrix */}
      <Card header={
        <div className="flex items-center gap-2">
          <Flame className="w-4 h-4 text-amber-400" />
          <span>Ecosystem Payment Failure Intelligence Matrix (Backend Dataset V2)</span>
        </div>
      } hover={false}>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider font-semibold">
              <tr>
                <th className="py-3.5 px-4">Failure Category</th>
                <th className="py-3.5 px-4">Failure Count</th>
                <th className="py-3.5 px-4">Impacted Merchants</th>
                <th className="py-3.5 px-4">Total Amount at Risk</th>
                <th className="py-3.5 px-4 text-right">Affected Gateways</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {failures.map((row) => (
                <tr key={row.failure_category} className="hover:bg-slate-800/40">
                  <td className="py-4 px-4 font-bold text-white flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-rose-400" />
                    {row.failure_category}
                  </td>
                  <td className="py-4 px-4 font-mono font-bold text-slate-200">
                    {row.failure_count.toLocaleString('en-IN')} failures
                  </td>
                  <td className="py-4 px-4 font-bold text-cyan-400">
                    {row.affected_merchant_count} Merchants
                  </td>
                  <td className="py-4 px-4 font-extrabold text-rose-400">
                    ₹{row.total_amount_at_risk.toLocaleString('en-IN')}
                  </td>
                  <td className="py-4 px-4 text-right">
                    <div className="flex flex-wrap items-center justify-end gap-1">
                      {row.affected_gateways.map((gw) => (
                        <span key={gw} className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-[10px] font-semibold text-slate-300">
                          {gw}
                        </span>
                      ))}
                    </div>
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
