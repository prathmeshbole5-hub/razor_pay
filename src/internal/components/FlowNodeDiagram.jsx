import React, { useState } from 'react';
import { ArrowRight, CheckCircle2, AlertTriangle, XCircle, Zap, Shield, Cpu } from 'lucide-react';
import { systemFlowNodes } from '../../data/internalData';
import { Card } from '../../shared/components/Card';
import Badge from '../../shared/components/Badge';

export default function FlowNodeDiagram() {
  const [activeNode, setActiveNode] = useState(systemFlowNodes[2]); // Default Razorpay Gateway Router

  const nodeStatusStyles = {
    NORMAL: 'border-cyan-500/30 bg-slate-900 text-cyan-300',
    HEALTHY: 'border-emerald-500/40 bg-slate-900 text-emerald-400',
    DEGRADED: 'border-amber-500/50 bg-amber-950/20 text-amber-300',
    OUTAGE: 'border-rose-500/70 bg-rose-950/30 text-rose-300 animate-pulse',
    ACTIVE_RECOVERY: 'border-indigo-500/40 bg-indigo-950/40 text-indigo-300',
    SUCCESS: 'border-emerald-500/40 bg-emerald-950/40 text-emerald-300'
  };

  return (
    <Card header="Interactive Ecosystem Architecture & Recovery Routing Flow" hover={false}>
      <div className="space-y-6 font-mono">
        <p className="text-xs text-slate-400">
          Click any architecture node below to inspect real-time throughput, latency metrics, and failure recovery state.
        </p>

        {/* Visual Flow Connector Pipeline */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-center">
          {systemFlowNodes.slice(0, 4).map((node, idx) => (
            <div key={node.id} className="relative group">
              <div
                onClick={() => setActiveNode(node)}
                className={`p-4 rounded-2xl border ${nodeStatusStyles[node.status] || nodeStatusStyles.NORMAL} cursor-pointer transition-all duration-200 hover:scale-105 shadow-lg ${
                  activeNode?.id === node.id ? 'ring-2 ring-cyan-400 border-cyan-400' : ''
                }`}
              >
                <div className="flex items-center justify-between text-[10px] font-bold uppercase text-slate-400 mb-1">
                  <span>{node.category}</span>
                  <Badge variant={node.status === 'OUTAGE' ? 'danger' : node.status === 'DEGRADED' ? 'warning' : 'info'} size="sm">
                    {node.status}
                  </Badge>
                </div>
                <div className="text-sm font-bold text-white truncate">{node.label}</div>
                <div className="text-xs text-cyan-400 font-extrabold mt-2 flex justify-between">
                  <span>{node.tps} TPS</span>
                  {node.latency && <span className="text-slate-400">{node.latency}</span>}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Failure & Recovery Branch */}
        <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-4">
          <div className="text-xs font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-2">
            <Zap className="w-4 h-4 text-indigo-400" />
            Automated Failure Interception & AI Recovery Layer
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {systemFlowNodes.slice(4).map((node) => (
              <div
                key={node.id}
                onClick={() => setActiveNode(node)}
                className={`p-4 rounded-2xl border ${nodeStatusStyles[node.status] || nodeStatusStyles.NORMAL} cursor-pointer transition-all duration-200 hover:scale-105 shadow-lg ${
                  activeNode?.id === node.id ? 'ring-2 ring-cyan-400 border-cyan-400' : ''
                }`}
              >
                <div className="flex items-center justify-between text-[10px] font-bold uppercase text-slate-400 mb-1">
                  <span>{node.category}</span>
                  <Badge variant={node.status === 'OUTAGE' ? 'danger' : node.status === 'DEGRADED' ? 'warning' : 'brand'} size="sm">
                    {node.status}
                  </Badge>
                </div>
                <div className="text-sm font-bold text-white truncate">{node.label}</div>
                <div className="text-xs text-cyan-400 font-extrabold mt-2 flex justify-between">
                  <span>{node.tps} TPS</span>
                  {node.latency && <span className="text-slate-400">{node.latency}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Selected Node Telemetry Detail Box */}
        {activeNode && (
          <div className="bg-slate-950 p-5 rounded-2xl border border-cyan-500/30 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-cyan-400" />
                <h4 className="text-sm font-bold text-white">Node Inspection: {activeNode.label}</h4>
              </div>
              <Badge variant="info" size="sm">
                Category: {activeNode.category}
              </Badge>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs pt-2 border-t border-slate-800">
              <div>
                <span className="text-slate-400 block">Live Throughput</span>
                <span className="text-sm font-bold text-cyan-300">{activeNode.tps} TPS</span>
              </div>
              <div>
                <span className="text-slate-400 block">Health Status</span>
                <span className={`text-sm font-bold ${activeNode.status === 'OUTAGE' ? 'text-rose-400' : activeNode.status === 'DEGRADED' ? 'text-amber-400' : 'text-emerald-400'}`}>
                  {activeNode.status}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block">Measured Latency</span>
                <span className="text-sm font-bold text-white">{activeNode.latency || '12ms (Internal)'}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Circuit State</span>
                <span className="text-sm font-bold text-emerald-400">NORMAL_CLOSED</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}
