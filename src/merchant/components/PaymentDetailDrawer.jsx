import React, { useState, useEffect } from 'react';
import { Drawer } from '../../shared/components/Drawer';
import Badge from '../../shared/components/Badge';
import Button from '../../shared/components/Button';
import LivePaymentTimeline from './LivePaymentTimeline';
import { RefreshCw, CheckCircle2, AlertTriangle, Zap, Check } from 'lucide-react';
import {
  getMerchantPaymentIntelligence,
  executeLivePaymentAction,
  getLivePaymentTimeline,
  getLivePaymentActions
} from '../../api/intelligenceApi';
import { CURRENT_MERCHANT_ID } from '../../config/currentMerchant';
import RecoveryProbabilityCard from '../../shared/components/intelligence/RecoveryProbabilityCard';
import RootCauseCard from '../../shared/components/intelligence/RootCauseCard';
import RecommendationCard from '../../shared/components/intelligence/RecommendationCard';
import IntelligenceLoadingState from '../../shared/components/intelligence/IntelligenceLoadingState';
import IntelligenceErrorState from '../../shared/components/intelligence/IntelligenceErrorState';

export default function PaymentDetailDrawer({ payment, isOpen, onClose, onActionExecuted }) {
  if (!payment) return null;

  const [isProcessing, setIsProcessing] = useState(false);
  const [actionDone, setActionDone] = useState(false);
  const [actionMsg, setActionMsg] = useState('');
  const [actionError, setActionError] = useState('');

  const [intelligence, setIntelligence] = useState(null);
  const [loadingAi, setLoadingAi] = useState(true);
  const [errorAi, setErrorAi] = useState(null);

  const [timeline, setTimeline] = useState([]);
  const [actionHistory, setActionHistory] = useState([]);

  const paymentId = payment.id || payment.payment_id;
  const merchantId = payment.merchant_id || CURRENT_MERCHANT_ID;
  const amountVal = payment.amount || payment.amount_inr || 0;

  const loadIntelligenceAndTimeline = async () => {
    if (!paymentId) return;
    setLoadingAi(true);
    setErrorAi(null);
    try {
      const [intelData, timelineData, actionsData] = await Promise.allSettled([
        getMerchantPaymentIntelligence(paymentId, merchantId),
        getLivePaymentTimeline(paymentId, merchantId),
        getLivePaymentActions(paymentId, merchantId)
      ]);

      if (intelData.status === 'fulfilled') {
        setIntelligence(intelData.value);
      } else {
        console.warn('Intelligence load notice:', intelData.reason);
      }

      if (timelineData.status === 'fulfilled' && Array.isArray(timelineData.value)) {
        setTimeline(timelineData.value);
      } else if (payment.timeline) {
        setTimeline(payment.timeline);
      }

      if (actionsData.status === 'fulfilled' && actionsData.value?.actions) {
        setActionHistory(actionsData.value.actions);
      }
    } catch (err) {
      console.error('Failed to load merchant payment intelligence:', err);
      setErrorAi(err.message || 'Failed to connect to RecoverAI backend');
    } finally {
      setLoadingAi(false);
    }
  };

  useEffect(() => {
    if (isOpen && paymentId) {
      setActionDone(false);
      setActionMsg('');
      setActionError('');
      loadIntelligenceAndTimeline();
    }
  }, [isOpen, paymentId]);

  const handleExecuteAction = async () => {
    setIsProcessing(true);
    setActionError('');
    try {
      let recStrategy = intelligence?.recommendation?.recommended_strategy?.strategy?.toLowerCase() || '';
      let actionType = 'smart_retry';
      if (recStrategy.includes('otp')) actionType = 'otp_reminder';
      else if (recStrategy.includes('link') || recStrategy.includes('whatsapp')) actionType = 'payment_link';
      else if (recStrategy.includes('later') || recStrategy.includes('cool')) actionType = 'retry_later';
      else if (recStrategy.includes('manual')) actionType = 'manual_follow_up';

      const res = await executeLivePaymentAction(paymentId, merchantId, actionType);
      setIsProcessing(false);
      setActionDone(true);
      setActionMsg(res.message || `Recovery action '${actionType}' executed successfully.`);

      // Refresh timeline & action history
      const [tData, aData] = await Promise.allSettled([
        getLivePaymentTimeline(paymentId, merchantId),
        getLivePaymentActions(paymentId, merchantId)
      ]);
      if (tData.status === 'fulfilled' && Array.isArray(tData.value)) {
        setTimeline(tData.value);
      }
      if (aData.status === 'fulfilled' && aData.value?.actions) {
        setActionHistory(aData.value.actions);
      }

      if (onActionExecuted) onActionExecuted(paymentId);
    } catch (err) {
      setIsProcessing(false);
      setActionError(err.message || 'Failed to execute recovery action.');
    }
  };

  const statusVariant = {
    RECOVERED: 'success',
    IN_RECOVERY: 'brand',
    ACTION_REQUIRED: 'warning',
    FAILED: 'danger',
    captured: 'success',
    verified: 'success',
    failed: 'danger',
    created: 'brand'
  }[(payment.status || '').toLowerCase()] || 'default';

  return (
    <Drawer
      isOpen={isOpen}
      onClose={onClose}
      title={`Payment Intelligence #${paymentId}`}
      footer={
        <div className="space-y-2 w-full">
          {actionMsg && (
            <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 p-2.5 rounded-xl text-xs font-semibold justify-center animate-fadeIn">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{actionMsg}</span>
            </div>
          )}

          {actionError && (
            <div className="flex items-center gap-2 bg-rose-500/10 border border-rose-500/30 text-rose-400 p-2.5 rounded-xl text-xs font-semibold justify-center animate-fadeIn">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{actionError}</span>
            </div>
          )}

          <div className="flex items-center justify-between w-full pt-1">
            <Button variant="outline" size="sm" onClick={onClose}>
              Close
            </Button>
            <Button
              variant="primary"
              size="sm"
              icon={RefreshCw}
              isLoading={isProcessing}
              disabled={actionDone}
              onClick={handleExecuteAction}
            >
              {actionDone ? 'Action Executed' : 'Execute Recommended Action'}
            </Button>
          </div>
        </div>
      }
    >
      <div className="space-y-6">
        {/* Top Header Card */}
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400">Total Amount</span>
            <Badge variant={statusVariant} dot size="md">
              {(payment.status || 'created').replace('_', ' ').toUpperCase()}
            </Badge>
          </div>
          <div className="text-3xl font-extrabold text-white">
            ₹{amountVal.toLocaleString('en-IN')}
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-slate-800/80">
            <div>
              <span className="text-slate-500 block">Customer / ID</span>
              <span className="text-slate-200 font-semibold">{payment.customer || merchantId}</span>
            </div>
            <div>
              <span className="text-slate-500 block">Payment Method</span>
              <span className="text-slate-200 font-semibold">{payment.method || payment.payment_method || 'Card'}</span>
            </div>
          </div>
        </div>

        {/* AI Recovery Intelligence Live Section */}
        <div className="space-y-3">
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">AI Recovery Diagnostics & Insights</h4>

          {loadingAi ? (
            <IntelligenceLoadingState />
          ) : errorAi ? (
            <IntelligenceErrorState error={errorAi} onRetry={loadIntelligenceAndTimeline} />
          ) : intelligence ? (
            <div className="space-y-4">
              {/* 1. Recovery Probability */}
              <RecoveryProbabilityCard prediction={intelligence.prediction} />

              {/* 2. Root Cause Analysis */}
              <RootCauseCard rootCause={intelligence.root_cause} />

              {/* 3. AI Recommended Action */}
              <RecommendationCard recommendation={intelligence.recommendation} />
            </div>
          ) : null}
        </div>

        {/* Executed Actions History (if any) */}
        {actionHistory.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
              <Zap className="w-3.5 h-3.5 text-emerald-400" />
              Executed Recovery Actions ({actionHistory.length})
            </h4>
            <div className="space-y-1.5">
              {actionHistory.map((act) => (
                <div key={act.action_id} className="bg-slate-950 p-2.5 rounded-xl border border-emerald-500/20 text-xs flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                    <span className="font-semibold text-slate-200 uppercase">{act.action_type.replace('_', ' ')}</span>
                  </div>
                  <span className="text-[10px] text-slate-400 font-mono">{act.created_at.slice(0, 19).replace('T', ' ')}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Detailed Breakdown */}
        <div className="space-y-3">
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Transaction Diagnostics</h4>
          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Failure Reason / Status</span>
              <span className="text-rose-400 font-medium">{payment.failureReason || payment.error_description || payment.status}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Error Code</span>
              <span className="font-mono text-slate-300">{payment.errorCode || payment.error_code || 'N/A'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Gateway / Bank</span>
              <span className="text-slate-200">{payment.gateway || payment.bank || 'Razorpay Gateway'}</span>
            </div>
          </div>
        </div>

        {/* Vertical Event Timeline Component */}
        <LivePaymentTimeline timeline={timeline} />
      </div>
    </Drawer>
  );
}
