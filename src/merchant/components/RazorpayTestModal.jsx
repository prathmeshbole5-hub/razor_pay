import React, { useState } from 'react';
import { Modal } from '../../shared/components/Modal';
import Button from '../../shared/components/Button';
import Badge from '../../shared/components/Badge';
import { CreditCard, CheckCircle2, AlertTriangle, ShieldCheck, Zap, RefreshCw } from 'lucide-react';
import { createRazorpayOrder, verifyRazorpayPayment } from '../../api/razorpayApi';

export default function RazorpayTestModal({ isOpen, onClose, merchantId = 'm_1004', onInspectPayment }) {
  const [amount, setAmount] = useState('500');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [orderResult, setOrderResult] = useState(null);
  const [verification, setVerification] = useState(null);

  const razorpayKeyId = import.meta.env.VITE_RAZORPAY_KEY_ID;
  const isConfigured = razorpayKeyId && razorpayKeyId !== 'rzp_test_placeholder';

  const loadRazorpayScript = () => {
    return new Promise((resolve) => {
      if (window.Razorpay) {
        resolve(true);
        return;
      }
      const script = document.createElement('script');
      script.src = 'https://checkout.razorpay.com/v1/checkout.js';
      script.onload = () => resolve(true);
      script.onerror = () => resolve(false);
      document.body.appendChild(script);
    });
  };

  const handleStartCheckout = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setVerification(null);
    setOrderResult(null);

    const numericAmount = parseFloat(amount);
    if (isNaN(numericAmount) || numericAmount <= 0) {
      setError('Please enter a valid amount greater than 0');
      setLoading(false);
      return;
    }

    try {
      // 1. Create order on backend
      const order = await createRazorpayOrder(numericAmount, 'INR', merchantId);
      setOrderResult(order);

      // Check if checkout.js script can be loaded
      const scriptLoaded = await loadRazorpayScript();

      if (scriptLoaded && window.Razorpay && order.key_id && order.key_id !== 'rzp_test_placeholder') {
        // Real Razorpay Checkout modal
        const options = {
          key: order.key_id,
          amount: order.amount,
          currency: order.currency || 'INR',
          name: 'RecoverAI Test Merchant',
          description: 'RecoverAI Test Mode Payment Transaction',
          order_id: order.order_id,
          handler: async function (response) {
            try {
              const ver = await verifyRazorpayPayment(
                response.razorpay_payment_id,
                response.razorpay_order_id,
                response.razorpay_signature,
                merchantId
              );
              setVerification(ver);
            } catch (verErr) {
              setError(verErr.message || 'Signature verification failed');
            }
          },
          prefill: {
            name: 'Demo Merchant User',
            email: 'demo@recoverai.io',
            contact: '9876543210'
          },
          theme: {
            color: '#4f46e5'
          }
        };

        const rzp = new window.Razorpay(options);
        rzp.on('payment.failed', function (resp) {
          setError(`Payment Failed: ${resp.error.description || resp.error.reason} (${resp.error.code})`);
        });
        rzp.open();
      } else {
        throw new Error(
          'Razorpay Checkout script could not be loaded or Razorpay API credentials are missing. Please check your environment setup.'
        );
      }
    } catch (err) {
      console.error('Razorpay test payment failed:', err);
      setError(err.message || 'Failed to initialize payment checkout');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Razorpay Test Mode Checkout"
    >
      <div className="space-y-5 text-slate-200 text-xs">
        {/* Environment Status Banner */}
        <div className={`p-3.5 rounded-xl border flex items-start gap-3 ${
          isConfigured 
            ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-300'
            : 'bg-amber-950/40 border-amber-500/30 text-amber-300'
        }`}>
          {isConfigured ? (
            <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
          ) : (
            <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          )}
          <div className="space-y-1">
            <div className="font-bold text-white flex items-center gap-2">
              <span>Razorpay Test Mode Status:</span>
              <Badge variant={isConfigured ? 'success' : 'warning'} size="sm">
                {isConfigured ? 'API Credentials Active' : 'Test Mode (Unconfigured Keys)'}
              </Badge>
            </div>
            {!isConfigured && (
              <p className="text-[11px] text-slate-300 leading-relaxed">
                <strong className="text-amber-300 font-semibold">Razorpay Test Mode is not configured.</strong> Set <code className="bg-black/40 px-1 py-0.5 rounded text-amber-200">VITE_RAZORPAY_KEY_ID</code> and backend <code className="bg-black/40 px-1 py-0.5 rounded text-amber-200">RAZORPAY_KEY_ID</code> in environment variables to enable live Razorpay popups. Server test mode verification remains available below.
              </p>
            )}
          </div>
        </div>

        {/* Input Form */}
        <form onSubmit={handleStartCheckout} className="space-y-4 bg-slate-950 p-4 rounded-xl border border-slate-800">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Test Amount (₹ INR)
            </label>
            <div className="relative">
              <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 font-bold">₹</span>
              <input
                type="number"
                min="1"
                step="1"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="500"
                className="w-full bg-slate-900 border border-slate-800 rounded-xl text-sm text-white font-bold pl-8 pr-4 py-2.5 focus:outline-none focus:border-indigo-500"
                required
              />
            </div>
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-slate-800/80">
            <div className="text-[11px] text-slate-400">
              Merchant: <strong className="text-indigo-300 font-mono">{merchantId}</strong>
            </div>
            <Button
              type="submit"
              variant="primary"
              size="md"
              icon={CreditCard}
              isLoading={loading}
            >
              Launch Razorpay Test Order
            </Button>
          </div>
        </form>

        {/* Error Output */}
        {error && (
          <div className="p-3.5 bg-rose-950/40 border border-rose-500/30 rounded-xl text-rose-300 text-xs space-y-2 animate-fadeIn">
            <div className="font-bold text-rose-400 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              <span>Checkout Notice</span>
            </div>
            <p className="text-[11px]">{error}</p>
          </div>
        )}

        {/* Order & Verification Output */}
        {verification && (
          <div className="p-4 bg-emerald-950/40 border border-emerald-500/30 rounded-xl space-y-3 animate-fadeIn">
            <div className="flex items-center justify-between">
              <div className="font-bold text-emerald-400 flex items-center gap-2 text-sm">
                <CheckCircle2 className="w-5 h-5" />
                <span>Payment Signature Server-Verified</span>
              </div>
              <Badge variant="success" size="sm">
                {verification.status}
              </Badge>
            </div>

            <div className="grid grid-cols-2 gap-2 text-[11px] bg-slate-950/60 p-3 rounded-lg border border-emerald-500/20 font-mono">
              <div>
                <span className="text-slate-400 block font-sans">Payment ID</span>
                <span className="text-white font-bold">{verification.payment_id}</span>
              </div>
              <div>
                <span className="text-slate-400 block font-sans">Order ID</span>
                <span className="text-white font-bold">{verification.order_id}</span>
              </div>
            </div>

            {onInspectPayment && (
              <div className="pt-1 text-right">
                <Button
                  variant="accent"
                  size="sm"
                  icon={Zap}
                  onClick={() => {
                    onClose();
                    onInspectPayment(verification.payment_id);
                  }}
                >
                  Inspect RecoverAI Intelligence
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </Modal>
  );
}
