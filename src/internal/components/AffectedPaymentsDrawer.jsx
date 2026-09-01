import React, { useState, useEffect } from 'react';
import { Drawer } from '../../shared/components/Drawer';
import Badge from '../../shared/components/Badge';
import Button from '../../shared/components/Button';
import { getIncidentAffectedPayments } from '../../api/internalApi';
import { Search, Sparkles, AlertCircle, RefreshCw, Layers, ShieldAlert, ArrowRight } from 'lucide-react';

export default function AffectedPaymentsDrawer({ incident, isOpen, onClose, onViewPaymentIntelligence }) {
  if (!incident) return null;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  const incidentId = incident.id || incident.incident_id;

  const loadAffectedPayments = async () => {
    if (!incidentId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await getIncidentAffectedPayments(incidentId);
      setData(res);
    } catch (err) {
      console.error('Failed to load incident affected payments:', err);
      setError(err.message || 'Unable to load affected payments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && incidentId) {
      setSearchQuery('');
      loadAffectedPayments();
    }
  }, [isOpen, incidentId]);

  const rawPayments = data?.payments || [];
  const filteredPayments = rawPayments.filter((pm) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    const pid = String(pm.payment_id || pm.id || '').toLowerCase();
    const method = String(pm.payment_method || '').toLowerCase();
    const bank = String(pm.bank || pm.gateway || '').toLowerCase();
    const errDesc = String(pm.error_description || pm.failure_reason || '').toLowerCase();
    const errCode = String(pm.error_code || '').toLowerCase();
    return pid.includes(q) || method.includes(q) || bank.includes(q) || errDesc.includes(q) || errCode.includes(q);
  });

  const totalCount = data?.total_transactions || incident.impactedTransactions || rawPayments.length;
  const totalImpactVal = Number(data?.total_amount_at_risk || incident.estimatedRevenueImpact || incident.amount_at_risk || 0);
  const formattedImpact = totalImpactVal >= 100000
    ? `₹${(totalImpactVal / 100000).toFixed(2)}L`
    : `₹${totalImpactVal.toLocaleString('en-IN')}`;

  const isTestMode = (incident.source === 'razorpay_test_webhook') || (data?.source === 'razorpay_test_webhook');

  return (
    <Drawer isOpen={isOpen} onClose={onClose} title="AFFECTED PAYMENTS" width="w-full max-w-xl">
      <div className="space-y-6 font-mono pb-8">

        {/* Header Summary Panel */}
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={incident.severity === 'CRITICAL' ? 'danger' : 'warning'} size="sm" dot>
              {incident.severity || 'WARNING'} ANOMALY
            </Badge>
            {isTestMode && (
              <Badge variant="brand" size="sm">
                RAZORPAY TEST MODE
              </Badge>
            )}
            <span className="text-xs text-cyan-300 font-bold ml-auto">
              ID: {incidentId}
            </span>
          </div>

          <h3 className="text-base font-bold text-white tracking-tight">
            {data?.title || incident.title}
          </h3>

          <div className="flex items-center justify-between text-xs border-t border-slate-800/80 pt-3">
            <span className="text-slate-400 font-semibold flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              <span>{totalCount} Total Affected Transactions</span>
            </span>
            <span className="text-rose-400 font-extrabold text-sm">
              {formattedImpact} Impact
            </span>
          </div>
        </div>

        {/* Search Bar */}
        <div className="relative">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search payment ID, method, or reason..."
            className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-4 py-2.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
          />
        </div>

        {/* Payments List Container */}
        {loading ? (
          <div className="space-y-3 pt-2">
            <div className="h-24 bg-slate-900/60 border border-slate-800/60 rounded-xl animate-pulse" />
            <div className="h-24 bg-slate-900/60 border border-slate-800/60 rounded-xl animate-pulse" />
            <div className="h-24 bg-slate-900/60 border border-slate-800/60 rounded-xl animate-pulse" />
          </div>
        ) : error ? (
          <div className="bg-rose-950/40 border border-rose-500/30 p-5 rounded-xl text-center space-y-3">
            <AlertCircle className="w-6 h-6 text-rose-400 mx-auto" />
            <p className="text-xs text-rose-300 font-semibold">Unable to load affected payments</p>
            <p className="text-[11px] text-slate-400">{error}</p>
            <Button variant="outline" size="sm" icon={RefreshCw} onClick={loadAffectedPayments}>
              Retry Loading
            </Button>
          </div>
        ) : filteredPayments.length === 0 ? (
          <div className="bg-slate-900/50 border border-slate-800/50 p-8 rounded-xl text-center space-y-2">
            <Layers className="w-6 h-6 text-slate-600 mx-auto" />
            <p className="text-xs text-slate-400 font-semibold">No affected payments found.</p>
            {searchQuery && (
              <p className="text-[11px] text-slate-500">No transactions match search '{searchQuery}'</p>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-[11px] text-slate-400 font-semibold px-1">
              <span>SHOWING {filteredPayments.length} TRANSACTIONS</span>
              <span>NEWEST FIRST</span>
            </div>

            {filteredPayments.map((pm) => {
              const pid = pm.payment_id || pm.id;
              const amt = Number(pm.amount || pm.amount_inr || 0);
              const fmtAmt = `₹${amt.toLocaleString('en-IN')}`;
              const method = pm.payment_method || 'Card';
              const bank = pm.bank || pm.gateway || 'Razorpay Gateway';
              const failureDesc = pm.error_description || pm.failure_reason || 'Transaction authorization failed';
              const errCode = pm.error_code ? `(${pm.error_code})` : '';

              // Timestamp formatting
              let timeStr = 'Recently';
              if (pm.created_at || pm.timestamp) {
                try {
                  const d = new Date(pm.created_at || pm.timestamp);
                  timeStr = d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }) + ', ' +
                            d.toLocaleTimeString('en-IN', { hour: 'numeric', minute: '2-digit', hour12: true });
                } catch (e) {
                  timeStr = String(pm.created_at || pm.timestamp);
                }
              }

              return (
                <div
                  key={pid}
                  className="bg-slate-900/90 border border-slate-800 hover:border-cyan-500/40 p-4 rounded-xl space-y-3 transition-all group"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-xs text-cyan-300 font-mono bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                        {pid}
                      </span>
                      {pm.source === 'razorpay_test_mode' && (
                        <span className="text-[9px] text-amber-400 font-bold bg-amber-500/10 border border-amber-500/30 px-1.5 py-0.5 rounded">
                          TEST
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="danger" size="sm">
                        {String(pm.status || 'FAILED').toUpperCase()}
                      </Badge>
                      <span className="text-sm font-extrabold text-white">
                        {fmtAmt}
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs border-t border-slate-800/60 pt-2.5">
                    <div>
                      <span className="text-[10px] text-slate-500 block font-bold">METHOD & ROUTE</span>
                      <span className="text-slate-300 font-semibold">{method} • {bank}</span>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] text-slate-500 block font-bold">TIMESTAMP</span>
                      <span className="text-slate-400 font-medium">{timeStr}</span>
                    </div>
                  </div>

                  <div className="text-xs text-rose-300/90 bg-slate-950/80 border border-slate-800 p-2 rounded-lg">
                    <span className="text-[10px] text-slate-500 block font-bold">FAILURE TELEMETRY</span>
                    <span>{failureDesc} <span className="text-slate-500 font-mono text-[11px]">{errCode}</span></span>
                  </div>

                  <div className="pt-1 flex items-center justify-end">
                    <Button
                      variant="outline"
                      size="sm"
                      icon={Sparkles}
                      onClick={() => onViewPaymentIntelligence && onViewPaymentIntelligence(pm)}
                      className="text-cyan-400 border-cyan-500/30 hover:bg-cyan-500/10 hover:border-cyan-500/60 text-xs"
                    >
                      View Intelligence
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Drawer>
  );
}
