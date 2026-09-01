import React, { useState, useEffect } from 'react';
import { Activity, CheckCircle2, XCircle, Clock, ChevronRight, ShieldCheck } from 'lucide-react';
import { Card } from '../../shared/components/Card';
import Badge from '../../shared/components/Badge';
import { Modal } from '../../shared/components/Drawer';
import { getMerchantLivePaymentEvents } from '../../api/intelligenceApi';

export default function LivePaymentActivityList({ refreshTrigger }) {
  const [livePayments, setLivePayments] = useState([]);
  const [selectedPayment, setSelectedPayment] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    fetchEvents();
  }, [refreshTrigger]);

  const fetchEvents = async () => {
    try {
      const res = await getMerchantLivePaymentEvents('m_1004');
      if (res && res.live_payments) {
        setLivePayments(res.live_payments);
      }
    } catch (e) {
      console.warn('[LivePaymentActivityList] Fetch error:', e);
    }
  };

  if (!livePayments.length) {
    return null;
  }

  return (
    <>
      <Card className="p-5 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-bold text-white">Live Razorpay Test Activity Feed</h3>
          </div>
          <Badge variant="brand" size="xs">
            {livePayments.length} Live Event{livePayments.length > 1 ? 's' : ''}
          </Badge>
        </div>

        <div className="space-y-2">
          {livePayments.map((pm) => (
            <div
              key={pm.payment_id}
              onClick={() => {
                setSelectedPayment(pm);
                setDrawerOpen(true);
              }}
              className="bg-slate-950 hover:bg-slate-900 border border-slate-800 hover:border-indigo-500/40 p-3 rounded-xl flex items-center justify-between cursor-pointer transition-all"
            >
              <div className="flex items-center gap-3">
                {pm.status === 'captured' || pm.status === 'verified' ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                ) : (
                  <XCircle className="w-4 h-4 text-red-400 shrink-0" />
                )}
                <div>
                  <div className="text-xs font-bold text-white flex items-center gap-1.5">
                    {pm.payment_id}
                    <span className="text-[10px] text-slate-400 font-normal font-mono">({pm.source})</span>
                  </div>
                  <div className="text-[10px] text-slate-400">
                    Method: {pm.payment_method} | Bank: {pm.bank}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="text-right">
                  <div className="text-xs font-bold text-emerald-400">
                    ₹{(pm.amount_inr || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </div>
                  <div className="text-[10px] uppercase font-semibold text-slate-400">{pm.status}</div>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-500" />
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Selected Live Payment Drawer Modal */}
      <Modal
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        title={`Live Payment Intelligence Details (${selectedPayment?.payment_id})`}
        maxWidth="max-w-md"
      >
        {selectedPayment && (
          <div className="space-y-4 text-xs">
            <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-400">Payment ID:</span>
                <span className="font-bold text-white font-mono">{selectedPayment.payment_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Order ID:</span>
                <span className="text-slate-300 font-mono">{selectedPayment.razorpay_order_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Amount:</span>
                <span className="font-bold text-emerald-400">
                  ₹{(selectedPayment.amount_inr || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Status:</span>
                <span className="uppercase font-bold text-indigo-400">{selectedPayment.status}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Source:</span>
                <span className="text-slate-300 font-mono">{selectedPayment.source}</span>
              </div>
            </div>

            {selectedPayment.intelligence && (
              <div className="bg-indigo-950/40 p-3.5 rounded-xl border border-indigo-500/30 space-y-2">
                <div className="text-xs font-bold text-indigo-300 uppercase">RecoverAI Live Diagnostics</div>
                <div className="flex justify-between">
                  <span className="text-slate-400">ML Recovery Probability:</span>
                  <span className="font-bold text-emerald-400">
                    {Math.round((selectedPayment.intelligence.prediction?.recovery_probability || 0.65) * 100)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Primary Root Cause:</span>
                  <span className="text-slate-200">
                    {selectedPayment.intelligence.root_cause?.primary_root_cause?.title || 'Gateway Timeout'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Recommended Action:</span>
                  <span className="text-slate-200">
                    {selectedPayment.intelligence.recommendation?.recommended_strategy?.strategy || 'Smart Gateway Retry'}
                  </span>
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </>
  );
}
