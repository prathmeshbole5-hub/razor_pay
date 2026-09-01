import React, { useState, useEffect } from 'react';
import { Server, Activity, AlertTriangle, Network, DollarSign, AlertCircle, Cpu, ShieldCheck, Sparkles } from 'lucide-react';
import RealtimeTPSMeter from '../components/RealtimeTPSMeter';
import GatewayStatusCard from '../components/GatewayStatusCard';
import AnomalyAlertBanner from '../components/AnomalyAlertBanner';
import AffectedPaymentsDrawer from '../components/AffectedPaymentsDrawer';
import PaymentDetailDrawer from '../../merchant/components/PaymentDetailDrawer';
import { failureAnomalies as fallbackAnomalies } from '../../data/internalData';
import { StatCard, Card } from '../../shared/components/Card';
import Badge from '../../shared/components/Badge';
import Button from '../../shared/components/Button';
import { getInternalDashboard, getGatewayHealth, getIncidents, executeIncidentMitigation } from '../../api/internalApi';
import { getInternalIntelligenceOverview } from '../../api/intelligenceApi';

export default function InternalOverview({ onNavigate }) {
  const [dashboardData, setDashboardData] = useState(null);
  const [gateways, setGateways] = useState([]);
  const [aiOverview, setAiOverview] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [activeIncidentForDrawer, setActiveIncidentForDrawer] = useState(null);
  const [activePaymentForIntel, setActivePaymentForIntel] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [dash, gwList, aiData, incList] = await Promise.all([
        getInternalDashboard(),
        getGatewayHealth(),
        getInternalIntelligenceOverview(),
        getIncidents().catch(() => [])
      ]);
      setDashboardData(dash);
      setGateways(gwList || []);
      setAiOverview(aiData);

      const activeList = (incList && incList.length > 0) ? incList : fallbackAnomalies;
      setIncidents(activeList);
    } catch (err) {
      console.error('Failed to load internal dashboard data:', err);
      setError(err.message || 'Failed to connect to backend service');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleMitigateIncident = async (incId) => {
    try {
      await executeIncidentMitigation(incId);
      await loadData();
    } catch (err) {
      console.error('Failed to execute mitigation:', err);
    }
  };

  if (loading) {
    return (
      <div className="space-y-8 animate-fadeIn font-mono p-4">
        <div className="h-20 bg-slate-900/80 border border-slate-800 rounded-2xl animate-pulse" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-slate-900/80 border border-slate-800 rounded-2xl animate-pulse" />
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
          <span>Failed to load internal operations telemetry</span>
        </div>
        <p className="text-xs text-slate-300">{error}</p>
        <Button variant="outline" size="sm" onClick={loadData}>
          Retry Telemetry Feed
        </Button>
      </div>
    );
  }

  const formattedGateways = gateways.map((gw) => {
    const statusLabel = gw.current_status === 'DEGRADED' ? 'DEGRADED' 
                      : gw.current_status === 'OUTAGE' ? 'OUTAGE' 
                      : 'HEALTHY';
    
    return {
      id: `gw_${gw.gateway.toLowerCase().replace(/\s+/g, '_')}`,
      name: gw.gateway,
      type: gw.gateway.includes('UPI') ? 'UPI Infrastructure' : gw.gateway.includes('Wallet') ? 'Wallet Infrastructure' : 'Bank Gateway',
      status: statusLabel,
      successRate: gw.average_success_rate,
      latencyMs: Math.round(gw.average_latency_ms),
      failureSpikePct: gw.failure_rate !== undefined ? gw.failure_rate : gw.average_error_rate,
      affectedMerchants: gw.impacted_merchants !== undefined ? gw.impacted_merchants : (gw.incident_count > 0 ? 1 : 0),
      hourlyVolume: gw.total_transactions > 0 ? gw.total_transactions * 100 : 285000,
      errorDominant: gw.error_dominant || 'NONE',
      lastUpdated: 'Live Feed'
    };
  });

  const revRecoveredLakhs = dashboardData ? (dashboardData.total_revenue_recovered / 100000).toFixed(2) : '0';
  const totalRiskLakhs = aiOverview ? (aiOverview.total_revenue_at_risk_inr / 100000).toFixed(2) : '0';

  return (
    <div className="space-y-8 animate-fadeIn font-mono">
      {/* Top Banner Alert if Critical Outage / Live Incident */}
      {incidents.length > 0 && (
        <div className="space-y-4">
          {incidents.map((anom) => (
            <AnomalyAlertBanner
              key={anom.id || anom.incident_id}
              anomaly={anom}
              onMitigate={handleMitigateIncident}
              onViewAffectedPayments={(inc) => setActiveIncidentForDrawer(inc)}
            />
          ))}
        </div>
      )}

      {/* Real-time TPS Meter */}
      <RealtimeTPSMeter initialTPS={1842} />

      {/* Top Level Command Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard
          title="Global Success Rate"
          value={`${(dashboardData?.overall_success_rate || 0).toFixed(2)}%`}
          subtitle="Ecosystem conversion efficiency"
          icon={Activity}
          accentColor="emerald"
          trend="Live Dataset Rate"
          trendType="positive"
          tooltip="Overall percentage of successful payment authorizations across the ecosystem."
        />

        <StatCard
          title="Active Incidents"
          value={`${dashboardData?.active_incidents || 0} Active`}
          subtitle="Gateway degradation alerts"
          icon={AlertTriangle}
          accentColor="rose"
          trend={`${dashboardData?.active_incidents || 0} Incidents`}
          trendType="negative"
          tooltip="Infrastructure incidents currently active and requiring system reroute or mitigation."
        />

        <StatCard
          title="Failed Transactions"
          value={`${(dashboardData?.failed_transactions || 0).toLocaleString('en-IN')}`}
          subtitle={`Out of ${(dashboardData?.total_transactions || 0).toLocaleString('en-IN')} total`}
          icon={Network}
          accentColor="amber"
          trend={`${(dashboardData?.overall_failure_rate || 0).toFixed(2)}% Failure Rate`}
          trendType="neutral"
          tooltip="Total failed payment attempts currently registered in SQLite."
        />

        <StatCard
          title="Revenue Protected"
          value={`₹${revRecoveredLakhs}L`}
          subtitle="Recovered via AI Smart Retries"
          icon={DollarSign}
          accentColor="cyan"
          trend={`${(dashboardData?.overall_recovery_rate || 0).toFixed(2)}% Recovery Rate`}
          trendType="positive"
          tooltip="Total value of failed payments successfully recovered by RecoverAI."
        />
      </div>

      {/* Ecosystem AI Operations Command Center */}
      {aiOverview && (
        <Card header={
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-cyan-400" />
              <span>RecoverAI Ecosystem AI Command Center</span>
            </div>
            <Badge variant="brand" size="sm">
              AI Status: {aiOverview.ai_status} (v{aiOverview.model_version})
            </Badge>
          </div>
        } hover={false}>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5 text-xs">
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
              <span className="text-slate-400 block text-[10px] uppercase">Total Analyzed Cases</span>
              <div className="text-2xl font-extrabold text-white">
                {(aiOverview?.total_payments_analyzed ?? 0).toLocaleString('en-IN')}
              </div>
              <span className="text-slate-500 text-[10px] block">100% Payment Recovery Grain</span>
            </div>

            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
              <span className="text-slate-400 block text-[10px] uppercase">Unrecovered Risk Pipeline</span>
              <div className="text-2xl font-extrabold text-rose-400">
                ₹{totalRiskLakhs}L
              </div>
              <span className="text-slate-500 text-[10px] block">{aiOverview?.unrecovered_risk_cases_count ?? 0} High-Risk Payments</span>
            </div>

            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
              <span className="text-slate-400 block text-[10px] uppercase">AI Recovery Rate Baseline</span>
              <div className="text-2xl font-extrabold text-emerald-400">
                {aiOverview?.ecosystem_recovery_rate_pct ?? 0}%
              </div>
              <span className="text-slate-500 text-[10px] block">Verified Model Predictions</span>
            </div>
          </div>
        </Card>
      )}

      {/* Gateway & Banking Infrastructure Quick Health Grid */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Server className="w-4 h-4 text-cyan-400" />
              Bank & Gateway Telemetry Grid
            </h3>
            <p className="text-xs text-slate-400">Real-time latency, success rate, and error dominant tracking from FastAPI dataset</p>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => onNavigate('gateway')}
          >
            Full Telemetry Monitor
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {formattedGateways.map((gw) => (
            <GatewayStatusCard key={gw.id} gateway={gw} onTriggerRouteSwitch={() => onNavigate('gateway')} />
          ))}
        </div>
      </div>

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
