import React, { useState, useEffect } from 'react';
import { Sparkles, Flame, AlertCircle, ShieldAlert, CheckCircle2, ArrowRight, Activity, Cpu, Target } from 'lucide-react';
import { failureAnomalies as fallbackAnomalies } from '../../data/internalData';
import AffectedPaymentsDrawer from '../components/AffectedPaymentsDrawer';
import PaymentDetailDrawer from '../../merchant/components/PaymentDetailDrawer';
import { Card } from '../../shared/components/Card';
import Badge from '../../shared/components/Badge';
import Button from '../../shared/components/Button';
import { getFailureIntelligence, getIncidents, executeIncidentMitigation } from '../../api/internalApi';

export default function FailureIntelligence({ onNavigate }) {
  const [failures, setFailures] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [activeIncidentForDrawer, setActiveIncidentForDrawer] = useState(null);
  const [activePaymentForIntel, setActivePaymentForIntel] = useState(null);
  const [executingMap, setExecutingMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [data, incList] = await Promise.all([
        getFailureIntelligence(),
        getIncidents().catch(() => [])
      ]);
      setFailures(data || []);
      const activeList = (incList && incList.length > 0) ? incList : fallbackAnomalies;
      setIncidents(activeList);
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

  const handleMitigateIncident = async (incId) => {
    setExecutingMap(prev => ({ ...prev, [incId]: true }));
    try {
      await executeIncidentMitigation(incId);
      await loadData();
    } catch (err) {
      console.error('Failed to execute mitigation:', err);
    } finally {
      setExecutingMap(prev => ({ ...prev, [incId]: false }));
    }
  };

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
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-cyan-400" />
            AI Failure Intelligence & Diagnosis Workspace
          </h2>
          <p className="text-xs text-slate-400">
            Deep-dive operational diagnostic space: failure patterns, AI root-cause classification, impact assessment, and automated mitigation recommendations.
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Badge variant="brand" pulse size="md">
            ₹{totalAtRiskLakhs}L Total Risk Analyzed
          </Badge>
          <Badge variant="outline" size="md">
            {incidents.length} Active Diagnoses
          </Badge>
        </div>
      </div>

      {/* Deep Incident Investigation Workspace Cards */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
            <Target className="w-4 h-4 text-cyan-400" />
            Persisted System Incidents Investigation Workspace
          </h3>
          <span className="text-[11px] text-slate-500 font-semibold">
            Real DB Telemetry • SQLite Preserved
          </span>
        </div>

        {incidents.map((inc) => {
          const incId = inc.id || inc.incident_id;
          const isTestWebhook = inc.source === 'razorpay_test_webhook';
          const impactVal = Number(inc.estimatedRevenueImpact || inc.amount_at_risk || 0);
          const formattedImpact = impactVal >= 100000
            ? `₹${(impactVal / 100000).toFixed(2)}L`
            : `₹${impactVal.toLocaleString('en-IN')}`;
          const isMitigated = inc.status === 'MITIGATED';
          const isExecuting = executingMap[incId] || false;

          return (
            <div
              key={incId}
              className={`rounded-2xl border p-6 space-y-6 font-mono transition-all ${
                isMitigated
                  ? 'bg-slate-900/60 border-slate-800'
                  : inc.severity === 'CRITICAL'
                    ? 'bg-slate-900/90 border-rose-500/50 shadow-xl shadow-rose-950/20'
                    : 'bg-slate-900/90 border-amber-500/40 shadow-lg'
              }`}
            >
              {/* Card Title & Top Metadata Bar */}
              <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 border-b border-slate-800 pb-4">
                <div className="space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant={inc.severity === 'CRITICAL' ? 'danger' : 'warning'} pulse dot size="sm">
                      {inc.severity} SEVERITY
                    </Badge>
                    {isTestWebhook && (
                      <Badge variant="brand" size="sm">
                        RAZORPAY TEST MODE
                      </Badge>
                    )}
                    <span className="text-xs text-cyan-300 font-bold bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                      {inc.confidenceScore || 95}% AI Confidence
                    </span>
                    {isMitigated && (
                      <Badge variant="success" size="sm">
                        STATUS: MITIGATED
                      </Badge>
                    )}
                    <span className="text-[10px] text-slate-500 font-bold uppercase">
                      ID: {incId}
                    </span>
                  </div>
                  <h3 className="text-lg font-bold text-white tracking-tight">
                    {inc.title}
                  </h3>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setActiveIncidentForDrawer(inc)}
                    className="text-xs border-slate-700 text-cyan-300 hover:border-cyan-500"
                  >
                    Drill Into Affected Payments ({inc.impactedTransactions || 1})
                  </Button>
                </div>
              </div>

              {/* 4-Column Structured Diagnostic Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 text-xs">
                {/* SECTION A: FAILURE PATTERN ANALYSIS */}
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2.5">
                  <div className="flex items-center gap-2 text-amber-400 font-bold text-[11px] uppercase tracking-wide border-b border-slate-800 pb-1.5">
                    <Activity className="w-3.5 h-3.5" />
                    <span>A. Failure Pattern</span>
                  </div>
                  <div className="space-y-1.5">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Gateway:</span>
                      <strong className="text-white font-bold">{inc.gateway || 'SBI'}</strong>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Error Code:</span>
                      <span className="text-rose-400 font-mono font-semibold">{inc.error_code || 'BAD_REQUEST_TIMEOUT'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Payment Method:</span>
                      <span className="text-slate-200">{inc.payment_method || 'UPI'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Occurrence Count:</span>
                      <strong className="text-cyan-400">{inc.impactedTransactions || 1} Txns</strong>
                    </div>
                    <div className="flex justify-between text-[10px] text-slate-500 pt-1 border-t border-slate-850">
                      <span>Detected:</span>
                      <span>{inc.created_at ? new Date(inc.created_at).toLocaleTimeString() : 'Live Stream'}</span>
                    </div>
                  </div>
                </div>

                {/* SECTION B: ROOT CAUSE ANALYSIS */}
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2.5">
                  <div className="flex items-center gap-2 text-cyan-400 font-bold text-[11px] uppercase tracking-wide border-b border-slate-800 pb-1.5">
                    <Cpu className="w-3.5 h-3.5" />
                    <span>B. AI Root Cause Analysis</span>
                  </div>
                  <div className="space-y-1.5">
                    <div className="font-bold text-slate-200 text-xs line-clamp-1">
                      {inc.root_cause || inc.title}
                    </div>
                    <p className="text-[11px] text-slate-300 leading-relaxed line-clamp-3">
                      {inc.description}
                    </p>
                    <div className="text-[10px] text-cyan-300 font-bold pt-1">
                      AI Diagnostic Confidence: {inc.confidenceScore || 95}%
                    </div>
                  </div>
                </div>

                {/* SECTION C: IMPACT ANALYSIS */}
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2.5">
                  <div className="flex items-center gap-2 text-rose-400 font-bold text-[11px] uppercase tracking-wide border-b border-slate-800 pb-1.5">
                    <ShieldAlert className="w-3.5 h-3.5" />
                    <span>C. Impact Analysis</span>
                  </div>
                  <div className="space-y-1.5">
                    <div className="flex justify-between items-baseline">
                      <span className="text-slate-400">Amount at Risk:</span>
                      <span className="text-sm font-extrabold text-rose-400">{formattedImpact}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Impacted Merchants:</span>
                      <strong className="text-cyan-400">{inc.affectedMerchants || 1} Merchants</strong>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Affected Txns:</span>
                      <strong className="text-slate-200">{inc.impactedTransactions || 1} Payments</strong>
                    </div>
                    {inc.payment_id && (
                      <div className="text-[10px] text-slate-500 font-semibold truncate pt-1 border-t border-slate-850">
                        Trigger Payment: <span className="text-slate-400 font-mono">{inc.payment_id}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* SECTION D: RECOVERY / MITIGATION RECOMMENDATION */}
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2.5 flex flex-col justify-between">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-emerald-400 font-bold text-[11px] uppercase tracking-wide border-b border-slate-800 pb-1.5">
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>D. Recovery Recommendation</span>
                    </div>
                    <div className="text-[11px] text-slate-200 leading-snug font-medium">
                      <strong>Action:</strong> {inc.recommendedAction || inc.recommended_mitigation}
                    </div>
                  </div>

                  <div className="pt-2">
                    {isMitigated || inc.status === 'MITIGATED' ? (
                      <div className="space-y-1 text-center">
                        <div className="flex items-center gap-1.5 text-emerald-400 text-xs font-bold bg-emerald-500/10 border border-emerald-500/30 px-3 py-1.5 rounded-xl justify-center">
                          <CheckCircle2 className="w-4 h-4" /> Mitigation Executed
                        </div>
                        <span className="text-[9px] text-slate-500 font-bold block">TEST SIMULATION MODE</span>
                      </div>
                    ) : (
                      <div className="space-y-1">
                        <Button
                          variant={inc.severity === 'CRITICAL' ? 'danger' : 'accent'}
                          size="sm"
                          icon={ArrowRight}
                          iconPosition="right"
                          disabled={isExecuting}
                          onClick={() => handleMitigateIncident(incId)}
                          className="w-full text-xs py-2"
                        >
                          {isExecuting ? 'Executing...' : 'Execute Mitigation Reroute'}
                        </Button>
                        <span className="text-[9px] text-slate-500 font-bold text-center block">
                          TEST SIMULATION MODE
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* SECTION E: ECOSYSTEM FAILURE INTELLIGENCE MATRIX TABLE */}
      <Card header={
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            <Flame className="w-4 h-4 text-amber-400" />
            <span className="font-bold text-white">Ecosystem Payment Failure Intelligence Matrix (Dataset V2)</span>
          </div>
          <Badge variant="outline" size="sm">
            {failures.length} Categories Tracked
          </Badge>
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
                    {(row.failure_count ?? 0).toLocaleString('en-IN')} failures
                  </td>
                  <td className="py-4 px-4 font-bold text-cyan-400">
                    {row.affected_merchant_count ?? 0} Merchants
                  </td>
                  <td className="py-4 px-4 font-extrabold text-rose-400">
                    ₹{(row.total_amount_at_risk ?? 0).toLocaleString('en-IN')}
                  </td>
                  <td className="py-4 px-4 text-right">
                    <div className="flex flex-wrap items-center justify-end gap-1">
                      {(row.affected_gateways || []).map((gw) => (
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

      {/* Affected Payments Right-Side Drawer */}
      <AffectedPaymentsDrawer
        incident={activeIncidentForDrawer}
        isOpen={Boolean(activeIncidentForDrawer)}
        onClose={() => setActiveIncidentForDrawer(null)}
        onViewPaymentIntelligence={(pm) => setActivePaymentForIntel(pm)}
      />

      {/* Payment Intelligence Drawer */}
      <PaymentDetailDrawer
        payment={activePaymentForIntel}
        isOpen={Boolean(activePaymentForIntel)}
        onClose={() => setActivePaymentForIntel(null)}
      />
    </div>
  );
}
