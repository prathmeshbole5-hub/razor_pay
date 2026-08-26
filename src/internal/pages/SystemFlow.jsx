import React from 'react';
import FlowNodeDiagram from '../components/FlowNodeDiagram';
import { GitMerge, Zap } from 'lucide-react';
import Badge from '../../shared/components/Badge';

export default function SystemFlow() {
  return (
    <div className="space-y-6 animate-fadeIn font-mono">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <GitMerge className="w-5 h-5 text-cyan-400" />
            System Flow & Automated Recovery Routing Architecture
          </h2>
          <p className="text-xs text-slate-400">
            Interactive node topology mapping payment flow from Consumer SDK ingress through Bank Gateways to RecoverAI AI recovery fallback.
          </p>
        </div>

        <Badge variant="brand" size="md">
          Smart Reroute Circuit Active
        </Badge>
      </div>

      <FlowNodeDiagram />
    </div>
  );
}
