import React, { useState, useEffect } from 'react';
import { Network, Lock, AlertCircle } from 'lucide-react';
import { Card } from '../../shared/components/Card';
import Badge from '../../shared/components/Badge';
import Button from '../../shared/components/Button';
import { getMerchantNetwork } from '../../api/internalApi';

export default function MerchantNetwork() {
  const [merchants, setMerchants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getMerchantNetwork();
      setMerchants(data || []);
    } catch (err) {
      console.error('Failed to fetch merchant network telemetry:', err);
      setError(err.message || 'Failed to load merchant network');
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
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-40 bg-slate-900/80 border border-slate-800 rounded-2xl animate-pulse" />
          ))}
        </div>
        <div className="h-64 bg-slate-900/80 border border-slate-800 rounded-2xl animate-pulse" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-rose-950/40 border border-rose-500/30 p-6 rounded-2xl space-y-4 animate-fadeIn font-mono">
        <div className="flex items-center gap-3 text-rose-400 font-bold">
          <AlertCircle className="w-5 h-5" />
          <span>Failed to load ecosystem merchant network</span>
        </div>
        <p className="text-xs text-slate-300">{error}</p>
        <Button variant="outline" size="sm" onClick={loadData}>
          Retry Connection
        </Button>
      </div>
    );
  }

  const totalMerchantsCount = merchants.length;
  const totalVolumeSum = merchants.reduce((sum, m) => sum + m.payment_volume, 0);

  return (
    <div className="space-y-8 animate-fadeIn font-mono">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Network className="w-5 h-5 text-cyan-400" />
            Ecosystem Merchant Network Intelligence
          </h2>
          <p className="text-xs text-slate-400">
            Aggregated merchant performance telemetry from dataset source of truth. End-customer personal transaction privacy is strictly preserved.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="info" size="md">
            <Lock className="w-3 h-3 mr-1" />
            Privacy Enforced
          </Badge>
          <Badge variant="brand" size="md">
            {totalMerchantsCount} Registered Network Merchants
          </Badge>
        </div>
      </div>

      {/* Merchant Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {merchants.map((m) => (
          <Card key={m.merchant_id} hover={false} className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="text-xs font-mono font-bold text-indigo-400">{m.merchant_id}</div>
              <Badge variant="brand" size="sm">{m.merchant_segment}</Badge>
            </div>

            <div className="text-lg font-bold text-white truncate">{m.merchant_name}</div>
            <div className="text-xs text-slate-400">{m.industry}</div>

            <div className="space-y-1.5 pt-2 border-t border-slate-800 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">Payment Volume</span>
                <span className="text-white font-bold">₹{(m.payment_volume / 100000).toFixed(2)}L</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Failure Rate</span>
                <span className="text-rose-400 font-bold">{m.failure_rate}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Recovery Rate</span>
                <span className="text-emerald-400 font-bold">{m.recovery_rate}%</span>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Aggregated Merchant Telemetry Table */}
      <Card header="Network Merchant Performance Matrix" hover={false}>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider font-semibold">
              <tr>
                <th className="py-3.5 px-4">Merchant ID</th>
                <th className="py-3.5 px-4">Merchant Name</th>
                <th className="py-3.5 px-4">Segment</th>
                <th className="py-3.5 px-4">Total Transactions</th>
                <th className="py-3.5 px-4">Failed Transactions</th>
                <th className="py-3.5 px-4">Failure Rate</th>
                <th className="py-3.5 px-4 text-right">Recovery Rate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {merchants.map((m) => (
                <tr key={m.merchant_id} className="hover:bg-slate-800/40">
                  <td className="py-4 px-4 font-mono font-bold text-indigo-400">{m.merchant_id}</td>
                  <td className="py-4 px-4 font-bold text-white">{m.merchant_name}</td>
                  <td className="py-4 px-4 font-mono text-slate-300">{m.merchant_segment}</td>
                  <td className="py-4 px-4 font-mono">{m.transaction_count.toLocaleString('en-IN')}</td>
                  <td className="py-4 px-4 font-mono text-rose-400 font-bold">{m.failure_count}</td>
                  <td className="py-4 px-4 font-bold text-rose-400">{m.failure_rate}%</td>
                  <td className="py-4 px-4 text-right font-extrabold text-emerald-400">
                    {m.recovery_rate}%
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
