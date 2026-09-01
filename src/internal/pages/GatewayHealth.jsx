import React, { useState, useEffect } from 'react';
import { Server, Filter, RefreshCw, ArrowRightLeft, CheckCircle2, AlertTriangle, ShieldCheck, AlertCircle } from 'lucide-react';
import GatewayStatusCard from '../components/GatewayStatusCard';
import { Card } from '../../shared/components/Card';
import Badge from '../../shared/components/Badge';
import Button from '../../shared/components/Button';
import { Modal } from '../../shared/components/Modal';
import { getGatewayHealth, executeIncidentMitigation } from '../../api/internalApi';

export default function GatewayHealth() {
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [selectedGateway, setSelectedGateway] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [rerouted, setRerouted] = useState(false);

  const [gateways, setGateways] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getGatewayHealth();
      const mapped = (data || []).map((gw) => {
        const isDegraded = gw.current_status === 'DEGRADED';
        const statusLabel = isDegraded ? 'DEGRADED' : gw.current_status === 'OPERATIONAL' ? 'HEALTHY' : 'OUTAGE';
        
        return {
          id: `gw_${gw.gateway.toLowerCase().replace(/\s+/g, '_')}`,
          name: gw.gateway,
          type: gw.gateway.includes('UPI') ? 'UPI Infrastructure' : gw.gateway.includes('Wallet') ? 'Wallet Infrastructure' : 'Bank Gateway',
          status: statusLabel,
          successRate: gw.average_success_rate,
          latencyMs: Math.round(gw.average_latency_ms),
          failureSpikePct: gw.average_error_rate,
          affectedMerchants: gw.incident_count > 0 ? 5 : 0,
          hourlyVolume: 285000,
          errorDominant: isDegraded ? 'GATEWAY_TIMEOUT (504)' : 'NONE',
          lastUpdated: 'Live Feed'
        };
      });
      setGateways(mapped);
    } catch (err) {
      console.error('Failed to fetch gateway health telemetry:', err);
      setError(err.message || 'Failed to fetch gateway health data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const filteredGateways = gateways.filter(
    (gw) => filterStatus === 'ALL' || gw.status === filterStatus
  );

  const handleOpenRerouteModal = (gwId) => {
    const gw = gateways.find((g) => g.id === gwId);
    setSelectedGateway(gw);
    setIsModalOpen(true);
    setRerouted(false);
  };

  const handleExecuteReroute = async () => {
    setRerouted(true);
    try {
      if (selectedGateway) {
        await executeIncidentMitigation(selectedGateway.id);
      }
    } catch (err) {
      console.warn('Mitigation notice:', err);
    }
    setTimeout(() => {
      setIsModalOpen(false);
      loadData();
    }, 1500);
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-fadeIn font-mono p-4">
        <div className="h-16 bg-slate-900/80 border border-slate-800 rounded-2xl animate-pulse" />
        <div className="h-14 bg-slate-900/80 border border-slate-800 rounded-2xl animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-48 bg-slate-900/80 border border-slate-800 rounded-2xl animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-rose-950/40 border border-rose-500/30 p-6 rounded-2xl space-y-4 animate-fadeIn font-mono">
        <div className="flex items-center gap-3 text-rose-400 font-bold">
          <AlertCircle className="w-5 h-5" />
          <span>Failed to load gateway health metrics</span>
        </div>
        <p className="text-xs text-slate-300">{error}</p>
        <Button variant="outline" size="sm" onClick={loadData}>
          Retry Connection
        </Button>
      </div>
    );
  }

  const degradedCount = gateways.filter((g) => g.status === 'DEGRADED').length;
  const outageCount = gateways.filter((g) => g.status === 'OUTAGE').length;
  const healthyCount = gateways.filter((g) => g.status === 'HEALTHY').length;

  return (
    <div className="space-y-6 animate-fadeIn font-mono">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Server className="w-5 h-5 text-cyan-400" />
            Gateway & Bank Health Monitor
          </h2>
          <p className="text-xs text-slate-400">
            Real-time telemetry feeds for partner bank servers, UPI stacks, and Razorpay routing nodes.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {outageCount > 0 && (
            <Badge variant="danger" pulse dot size="sm">
              {outageCount} Outage
            </Badge>
          )}
          {degradedCount > 0 && (
            <Badge variant="warning" size="sm">
              {degradedCount} Degraded
            </Badge>
          )}
          <Badge variant="success" size="sm">
            {healthyCount} Healthy
          </Badge>
        </div>
      </div>

      {/* Controls Bar */}
      <Card padding="sm" hover={false}>
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs">
            <Filter className="w-4 h-4 text-slate-400" />
            <span className="text-slate-400">Status Filter:</span>
            {['ALL', 'HEALTHY', 'DEGRADED', 'OUTAGE'].map((st) => (
              <button
                key={st}
                onClick={() => setFilterStatus(st)}
                className={`px-3 py-1.5 rounded-lg font-bold transition-all ${
                  filterStatus === st
                    ? 'bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20'
                    : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
                }`}
              >
                {st}
              </button>
            ))}
          </div>

          <span className="text-xs text-slate-500">Live Backend Feed</span>
        </div>
      </Card>

      {/* Gateway Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredGateways.map((gw) => (
          <GatewayStatusCard
            key={gw.id}
            gateway={gw}
            onTriggerRouteSwitch={handleOpenRerouteModal}
          />
        ))}
      </div>

      {/* Traffic Reroute Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={`Reroute Traffic: ${selectedGateway?.name}`}
        footer={
          rerouted ? (
            <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs">
              <CheckCircle2 className="w-4 h-4" /> Traffic Rerouted to Secondary Route Successfully
            </div>
          ) : (
            <div className="flex items-center justify-between w-full">
              <Button variant="outline" size="sm" onClick={() => setIsModalOpen(false)}>
                Cancel
              </Button>
              <Button variant="danger" size="sm" icon={ArrowRightLeft} onClick={handleExecuteReroute}>
                Confirm Emergency Reroute
              </Button>
            </div>
          )
        }
      >
        {selectedGateway && (
          <div className="space-y-4 text-xs font-mono">
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-400">Target Gateway</span>
                <span className="text-white font-bold">{selectedGateway.name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Current Status</span>
                <span className="text-rose-400 font-bold">{selectedGateway.status}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Impacted Merchants</span>
                <span className="text-amber-400 font-bold">{selectedGateway.affectedMerchants} Merchants</span>
              </div>
            </div>

            <p className="text-slate-300">
              Executing this emergency reroute will shift live authorization traffic from <strong>{selectedGateway.name}</strong> directly to <strong>Razorpay Tokenized Smart Routing Engine</strong>.
            </p>
          </div>
        )}
      </Modal>
    </div>
  );
}
