import React, { useState, useEffect } from 'react';
import { RefreshCw, CheckCircle2, Clock, Zap, AlertTriangle } from 'lucide-react';
import { Card } from '../../shared/components/Card';
import Badge from '../../shared/components/Badge';
import Button from '../../shared/components/Button';
import PaymentDetailDrawer from '../components/PaymentDetailDrawer';
import { getRecoveryCases } from '../../api/merchantApi';
import { CURRENT_MERCHANT_ID } from '../../config/currentMerchant';

export default function RecoveryCases() {
  const [recoveryCases, setRecoveryCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [selectedPayment, setSelectedPayment] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getRecoveryCases(CURRENT_MERCHANT_ID);
      const stagesList = ['Payment Failed', 'AI Diagnostics', 'Retry Scheduled', 'Customer Contacted', 'Revenue Recovered'];
      
      const mapped = (data || []).map((rc) => {
        const isRecovered = rc.attempt_status === 'Recovered';
        const isPending = rc.attempt_status === 'Pending';
        const currentStage = isRecovered ? 4 : isPending ? 2 : 1;
        const probPct = Math.round(rc.predicted_recovery_probability * 100);

        return {
          caseId: `REC-${rc.payment_id}`,
          paymentId: rc.payment_id,
          merchantId: rc.merchant_id || CURRENT_MERCHANT_ID,
          customer: `Customer (${rc.payment_id.slice(-4)})`,
          amount: rc.amount_inr ?? rc.amount,
          method: 'Card / UPI',
          gateway: 'Razorpay System',
          failureReason: 'Payment Recovery Case in Pipeline',
          errorCode: 'PIPELINE_CASE',
          bank: 'Partner Bank',
          attempts: rc.attempt_number || 1,
          status: isRecovered ? 'RECOVERED' : isPending ? 'IN_RECOVERY' : 'ACTION_REQUIRED',
          strategy: rc.strategy,
          attemptNumber: rc.attempt_number,
          delayMinutes: rc.delay_minutes,
          attemptStatus: rc.attempt_status,
          estimatedRecoveryProb: `${(rc.predicted_recovery_probability * 100).toFixed(1)}%`,
          aiConfidence: probPct,
          currentStage: currentStage,
          stages: stagesList,
          scheduledTime: rc.resolved_at ? `Resolved ${rc.resolved_at}` : `Within ${rc.delay_minutes} min window`
        };
      });
      setRecoveryCases(mapped);
    } catch (err) {
      console.error('Failed to fetch merchant recovery cases:', err);
      setError(err.message || 'Failed to fetch recovery cases');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleOpenDrawer = (rcCase) => {
    setSelectedPayment({
      id: rcCase.paymentId,
      merchant_id: rcCase.merchantId || CURRENT_MERCHANT_ID,
      customer: rcCase.customer,
      amount: rcCase.amount,
      method: rcCase.method,
      gateway: rcCase.gateway,
      failureReason: rcCase.failureReason,
      errorCode: rcCase.errorCode,
      bank: rcCase.bank,
      attempts: rcCase.attempts,
      status: rcCase.status
    });
    setDrawerOpen(true);
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-fadeIn p-4">
        <div className="h-16 bg-slate-900/80 border border-slate-800 rounded-2xl animate-pulse" />
        <div className="h-14 bg-slate-900/80 border border-slate-800 rounded-2xl animate-pulse" />
        <div className="grid grid-cols-1 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-44 bg-slate-900/80 border border-slate-800 rounded-2xl animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-rose-950/40 border border-rose-500/30 p-6 rounded-2xl space-y-4 animate-fadeIn">
        <div className="flex items-center gap-3 text-rose-400 font-bold">
          <AlertTriangle className="w-5 h-5" />
          <span>Failed to load active recovery cases</span>
        </div>
        <p className="text-xs text-slate-300">{error}</p>
        <Button variant="outline" size="sm" onClick={loadData}>
          Retry Connection
        </Button>
      </div>
    );
  }

  const activeCasesCount = recoveryCases.filter((c) => c.attemptStatus === 'Pending').length;

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white">Active Recovery Cases Lifecycle</h2>
          <p className="text-xs text-slate-400">
            Real-time pipeline tracking showing AI diagnostics, smart retries, and customer nudge progress.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="brand" size="md">
            {activeCasesCount} Active Pipeline Cases ({recoveryCases.length} Total)
          </Badge>
        </div>
      </div>

      {/* Pipeline Summary Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 bg-slate-900/90 border border-slate-800 p-4 rounded-2xl">
        {['Payment Failed', 'AI Diagnostics', 'Retry Scheduled', 'Customer Contacted', 'Revenue Recovered'].map((step, idx) => (
          <div key={idx} className="flex flex-col items-center text-center space-y-1">
            <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider">Step 0{idx + 1}</span>
            <span className="text-xs font-semibold text-slate-200">{step}</span>
          </div>
        ))}
      </div>

      {/* Case Cards Grid */}
      <div className="space-y-4">
        {recoveryCases.slice(0, 15).map((rc) => {
          const isComplete = rc.attemptStatus === 'Recovered';
          const isFailed = rc.attemptStatus === 'Failed';

          return (
            <Card key={rc.caseId} className="space-y-5" hover={false}>
              {/* Header Info */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
                <div className="flex items-start gap-3">
                  <div className={`p-3 rounded-xl border ${
                    isComplete 
                      ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' 
                      : isFailed 
                      ? 'bg-rose-500/10 border-rose-500/20 text-rose-400'
                      : 'bg-indigo-500/10 border-indigo-500/20 text-indigo-400'
                  }`}>
                    <RefreshCw className={`w-5 h-5 ${!isComplete && !isFailed ? 'animate-spin' : ''}`} />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-bold text-slate-400">{rc.caseId}</span>
                      <span className="text-xs font-semibold text-white">Payment #{rc.paymentId}</span>
                      <Badge variant={isComplete ? 'success' : isFailed ? 'danger' : 'brand'} size="sm">
                        {isComplete ? 'RECOVERED' : isFailed ? 'FAILED' : 'IN RECOVERY'}
                      </Badge>
                    </div>
                    <div className="text-sm font-bold text-white mt-0.5">
                      {rc.customer} • <span className="text-emerald-400">₹{rc.amount.toLocaleString('en-IN')}</span>
                    </div>
                  </div>
                </div>

                <div className="text-right space-y-0.5">
                  <div className="text-xs text-slate-400 font-medium">Estimated Recovery Probability</div>
                  <div className="text-lg font-extrabold text-emerald-400">{rc.estimatedRecoveryProb}</div>
                </div>
              </div>

              {/* Progress Stepper Visualizer */}
              <div className="space-y-2">
                <div className="flex justify-between text-xs text-slate-400 font-medium">
                  <span>Strategy: <strong className="text-indigo-300">{rc.strategy}</strong></span>
                  <span>Status: <strong className="text-slate-200">{rc.stages[rc.currentStage]}</strong></span>
                </div>

                <div className="grid grid-cols-5 gap-2">
                  {rc.stages.map((stgLabel, idx) => {
                    const isDone = idx <= rc.currentStage;
                    const isCurrent = idx === rc.currentStage;

                    return (
                      <div key={idx} className="space-y-1">
                        <div
                          className={`h-2 rounded-full transition-all duration-300 ${
                            isDone
                              ? isComplete
                                ? 'bg-emerald-400 shadow-sm shadow-emerald-400/50'
                                : isFailed && idx === rc.currentStage
                                ? 'bg-rose-500 shadow-sm shadow-rose-500/50'
                                : 'bg-indigo-500 shadow-sm shadow-indigo-500/50'
                              : 'bg-slate-800'
                          }`}
                        />
                        <span className={`text-[10px] block truncate font-medium ${isCurrent ? 'text-white font-bold' : isDone ? 'text-slate-300' : 'text-slate-600'}`}>
                          {stgLabel}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Strategy & Action Details */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-3 border-t border-slate-800/80 bg-slate-950/40 p-3 rounded-xl">
                <div className="flex items-center gap-2 text-xs text-slate-300">
                  <Clock className="w-4 h-4 text-slate-500" />
                  <span>Next Action Window: <strong className="text-white">{rc.scheduledTime}</strong></span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs text-indigo-400 font-bold">{rc.aiConfidence}% AI Confidence</span>
                  <Button variant="outline" size="sm" onClick={() => handleOpenDrawer(rc)}>
                    View AI Intelligence
                  </Button>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Payment Detail Drawer */}
      <PaymentDetailDrawer
        payment={selectedPayment}
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />
    </div>
  );
}
