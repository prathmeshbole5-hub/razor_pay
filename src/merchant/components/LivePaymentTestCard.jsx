import React, { useState } from 'react';

import {
  CreditCard,
  Zap,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Loader2,
} from 'lucide-react';

import { Card } from '../../shared/components/Card';
import Button from '../../shared/components/Button';
import Badge from '../../shared/components/Badge';
import { Modal } from '../../shared/components/Drawer';

import {
  createRazorpayOrder,
  verifyRazorpayPayment,
} from '../../api/intelligenceApi';


// ============================================================
// Razorpay Checkout Script Loader
// ============================================================

const loadRazorpayScript = () => {
  return new Promise((resolve) => {
    if (window.Razorpay) {
      resolve(true);
      return;
    }

    const script = document.createElement('script');

    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.async = true;

    script.onload = () => {
      resolve(true);
    };

    script.onerror = () => {
      resolve(false);
    };

    document.body.appendChild(script);
  });
};


// ============================================================
// Main Component
// ============================================================

export default function LivePaymentTestCard({ onPaymentCreated }) {

  // Amount is entered in RUPEES.
  const [amount, setAmount] = useState('1');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [resultDrawerOpen, setResultDrawerOpen] = useState(false);
  const [intelligenceResult, setIntelligenceResult] = useState(null);


  // ============================================================
  // START PAYMENT
  // ============================================================

  const handleStartPayment = async () => {

    if (loading) {
      return;
    }

    setError(null);
    setLoading(true);

    try {

      // --------------------------------------------------------
      // 1. Validate amount
      // --------------------------------------------------------

      const parsedAmount = Number(amount);

      if (
        !Number.isFinite(parsedAmount) ||
        parsedAmount <= 0
      ) {
        throw new Error(
          'Please enter a valid payment amount greater than zero.'
        );
      }

      console.log(
        '💰 Creating Razorpay order for ₹',
        parsedAmount
      );


      // --------------------------------------------------------
      // 2. Create order through our FastAPI backend
      // --------------------------------------------------------

      const orderRes = await createRazorpayOrder(
        parsedAmount,
        'm_1004',
        'INR'
      );

      console.log(
        '✅ Razorpay order response:',
        orderRes
      );


      // --------------------------------------------------------
      // 3. Validate backend response
      // --------------------------------------------------------

      if (!orderRes) {
        throw new Error(
          'Backend returned an empty response.'
        );
      }

      if (!orderRes.order_id) {
        throw new Error(
          'Backend did not return a Razorpay order ID.'
        );
      }

      if (!orderRes.key_id) {
        throw new Error(
          'Backend did not return a Razorpay Test Key ID.'
        );
      }

      if (
        !orderRes.key_id.startsWith('rzp_test_')
      ) {
        console.warn(
          '⚠️ Warning: key_id does not look like a Razorpay test key:',
          orderRes.key_id
        );
      }

      console.log(
        '🆔 Razorpay Order ID:',
        orderRes.order_id
      );

      console.log(
        '🔑 Razorpay Key ID:',
        orderRes.key_id
      );

      console.log(
        '💵 Razorpay Amount:',
        orderRes.amount
      );

      console.log(
        '💵 Razorpay Amount in ₹:',
        Number(orderRes.amount) / 100
      );


      // --------------------------------------------------------
      // 4. Load Razorpay Checkout
      // --------------------------------------------------------

      console.log(
        '🔵 Loading Razorpay Checkout...'
      );

      const isLoaded = await loadRazorpayScript();

      if (!isLoaded) {
        throw new Error(
          'Razorpay Checkout failed to load. Check your internet connection.'
        );
      }

      if (!window.Razorpay) {
        throw new Error(
          'Razorpay Checkout SDK is unavailable.'
        );
      }

      console.log(
        '✅ Razorpay Checkout loaded.'
      );


      // --------------------------------------------------------
      // 5. Configure Razorpay Checkout
      // --------------------------------------------------------

      const options = {

        key: orderRes.key_id,

        // Razorpay expects paise.
        amount: Number(orderRes.amount),

        currency: orderRes.currency || 'INR',

        name: 'CloudMart',

        description:
          'RecoverAI Razorpay Test Payment',

        order_id: orderRes.order_id,

        prefill: {
          name: 'Apex Test User',
          email: 'test@cloudmart.com',
          contact: '9999999999',
        },

        notes: {
          merchant_id: 'm_1004',
          source: 'RecoverAI',
        },

        theme: {
          color: '#6366f1',
        },

        // ------------------------------------------------------
        // Successful payment
        // ------------------------------------------------------

        handler: async function (response) {

          console.log(
            '🟢 Razorpay payment completed:',
            response
          );

          try {

            setError(null);

            // ----------------------------------------------
            // Validate Razorpay response
            // ----------------------------------------------

            if (
              !response?.razorpay_payment_id
            ) {
              throw new Error(
                'Razorpay payment ID was not returned.'
              );
            }

            if (
              !response?.razorpay_order_id
            ) {
              throw new Error(
                'Razorpay order ID was not returned.'
              );
            }

            if (
              !response?.razorpay_signature
            ) {
              throw new Error(
                'Razorpay payment signature was not returned.'
              );
            }


            console.log(
              '💳 Payment ID:',
              response.razorpay_payment_id
            );

            console.log(
              '🆔 Order ID:',
              response.razorpay_order_id
            );

            console.log(
              '🔐 Signature received.'
            );


            // ----------------------------------------------
            // 6. Verify payment on backend
            // ----------------------------------------------

            console.log(
              '🔵 Verifying Razorpay payment on backend...'
            );

            const verifyRes =
              await verifyRazorpayPayment({

                razorpay_payment_id:
                  response.razorpay_payment_id,

                razorpay_order_id:
                  response.razorpay_order_id,

                razorpay_signature:
                  response.razorpay_signature,

                merchant_id: 'm_1004',
              });


            console.log(
              '✅ Backend verification response:',
              verifyRes
            );


            // ----------------------------------------------
            // 7. Check verification result
            // ----------------------------------------------

            if (!verifyRes) {
              throw new Error(
                'Backend returned an empty verification response.'
              );
            }

            if (
              verifyRes.verified === false ||
              verifyRes.success === false ||
              verifyRes.status === 'failed'
            ) {

              throw new Error(
                verifyRes.message ||
                verifyRes.detail ||
                'Razorpay payment verification failed.'
              );
            }


            // ----------------------------------------------
            // 8. Show RecoverAI intelligence
            // ----------------------------------------------

            setIntelligenceResult({
              ...verifyRes,

              payment_id:
                verifyRes.payment_id ||
                response.razorpay_payment_id,

              razorpay_payment_id:
                response.razorpay_payment_id,

              razorpay_order_id:
                response.razorpay_order_id,
            });

            setResultDrawerOpen(true);


            // ----------------------------------------------
            // 9. Refresh dashboard
            // ----------------------------------------------

            if (onPaymentCreated) {
              onPaymentCreated();
            }

          } catch (err) {

            console.error(
              '❌ Payment verification failed:',
              err
            );

            setError(
              err?.message ||
              'Payment verification failed.'
            );

          } finally {

            setLoading(false);
          }
        },


        // ------------------------------------------------------
        // User closes checkout
        // ------------------------------------------------------

        modal: {

          ondismiss: function () {

            console.log(
              '🟡 Razorpay Checkout closed.'
            );

            setLoading(false);
          },
        },


        // ------------------------------------------------------
        // Retry configuration
        // ------------------------------------------------------

        retry: {
          enabled: true,
          max_count: 2,
        },
      };


      // --------------------------------------------------------
      // 6. Create Razorpay instance
      // --------------------------------------------------------

      console.log(
        '🔵 Creating Razorpay Checkout instance...'
      );

      const razorpay =
        new window.Razorpay(options);


      // --------------------------------------------------------
      // 7. Payment failed event
      // --------------------------------------------------------

      razorpay.on(
        'payment.failed',
        function (response) {

          console.error(
            '❌ Razorpay payment failed:',
            response
          );

          const errorDescription =
            response?.error?.description;

          const errorReason =
            response?.error?.reason;

          const errorCode =
            response?.error?.code;

          const message =
            errorDescription ||
            errorReason ||
            'Razorpay payment failed.';

          console.error(
            'Razorpay error code:',
            errorCode
          );

          setError(
            `${message}${errorCode
              ? ` (${errorCode})`
              : ''
            }`
          );

          setLoading(false);
        }
      );


      // --------------------------------------------------------
      // 8. Open Razorpay Checkout
      // --------------------------------------------------------

      console.log(
        '🚀 Opening Razorpay Checkout...'
      );

      razorpay.open();

    } catch (err) {

      console.error(
        '❌ Payment initialization error:',
        err
      );

      setError(
        err?.message ||
        'Failed to initiate Razorpay payment.'
      );

      setLoading(false);
    }
  };


  // ============================================================
  // UI
  // ============================================================

  return (
    <>
      <Card
        className="
          bg-gradient-to-br
          from-slate-900
          via-slate-900
          to-indigo-950/40
          border-indigo-500/30
          p-5
          relative
          overflow-hidden
        "
      >

        {/* ====================================================
            Header
        ==================================================== */}

        <div
          className="
            flex
            flex-col
            sm:flex-row
            sm:items-center
            justify-between
            gap-4
          "
        >

          <div className="space-y-1">

            <div className="flex items-center gap-2">

              <CreditCard
                className="w-5 h-5 text-indigo-400"
              />

              <h3
                className="
                  text-sm
                  font-bold
                  text-white
                "
              >
                Live Razorpay Test Mode Pipeline
              </h3>

              <Badge
                variant="brand"
                size="xs"
              >
                Phase 8A
              </Badge>

            </div>

            <p
              className="
                text-xs
                text-slate-400
              "
            >
              Trigger a real Razorpay Test payment.
              Verified events feed into ML recovery
              prediction, root cause analysis, and
              recommendation engines.
            </p>

          </div>


          {/* ==================================================
              Amount + Button
          ================================================== */}

          <div
            className="
              flex
              items-center
              gap-2
            "
          >

            <div className="relative">

              <span
                className="
                  absolute
                  left-3
                  top-2.5
                  text-xs
                  font-bold
                  text-slate-400
                "
              >
                ₹
              </span>

              <input
                type="number"
                min="1"
                step="1"
                value={amount}
                onChange={(e) =>
                  setAmount(e.target.value)
                }
                disabled={loading}
                className="
                  w-24
                  bg-slate-950
                  border
                  border-slate-800
                  rounded-xl
                  text-xs
                  font-bold
                  text-white
                  pl-6
                  pr-3
                  py-2
                  focus:outline-none
                  focus:border-indigo-500
                  disabled:opacity-50
                "
                placeholder="1"
              />

            </div>


            <Button
              variant="primary"
              size="md"
              icon={loading ? Loader2 : Zap}
              onClick={handleStartPayment}
              disabled={loading}
              className=""
            >
              {loading
                ? 'Processing...'
                : 'Create Test Payment'}
            </Button>

          </div>

        </div>


        {/* ====================================================
            Error
        ==================================================== */}

        {error && (

          <div
            className="
              mt-3
              bg-red-500/10
              border
              border-red-500/30
              text-red-300
              px-3
              py-2
              rounded-xl
              text-xs
              flex
              items-center
              gap-2
            "
          >

            <AlertCircle
              className="
                w-4
                h-4
                text-red-400
                shrink-0
              "
            />

            <span>
              {error}
            </span>

          </div>

        )}

      </Card>


      {/* ======================================================
          Intelligence Result Modal
      ====================================================== */}

      <Modal
        isOpen={resultDrawerOpen}
        onClose={() =>
          setResultDrawerOpen(false)
        }
        title="RecoverAI Live Payment Intelligence Analysis"
        maxWidth="max-w-xl"
      >

        {intelligenceResult && (

          <div
            className="
              space-y-5
              text-xs
            "
          >

            {/* ==================================================
                Payment Verification
            ================================================== */}

            <div
              className="
                bg-emerald-500/10
                border
                border-emerald-500/30
                p-3.5
                rounded-xl
                flex
                items-center
                justify-between
              "
            >

              <div
                className="
                  flex
                  items-center
                  gap-2.5
                "
              >

                <CheckCircle2
                  className="
                    w-5
                    h-5
                    text-emerald-400
                    shrink-0
                  "
                />

                <div>

                  <div
                    className="
                      font-bold
                      text-emerald-300
                      text-xs
                    "
                  >
                    Payment Signature Verified
                  </div>

                  <div
                    className="
                      text-[11px]
                      text-slate-400
                    "
                  >
                    Source: Live Razorpay Test Mode
                  </div>

                </div>

              </div>


              <span
                className="
                  font-mono
                  text-xs
                  font-bold
                  text-emerald-400
                "
              >
                {intelligenceResult.payment_id ||
                  intelligenceResult.razorpay_payment_id ||
                  'Verified'}
              </span>

            </div>


            {/* ==================================================
                ML Recovery Prediction
            ================================================== */}

            {intelligenceResult.intelligence?.prediction && (

              <div
                className="
                  bg-slate-950
                  p-4
                  rounded-xl
                  border
                  border-slate-800
                  space-y-2
                "
              >

                <div
                  className="
                    flex
                    items-center
                    justify-between
                  "
                >

                  <span
                    className="
                      text-slate-400
                      font-medium
                    "
                  >
                    ML Recovery Prediction
                  </span>

                  <span
                    className="
                      font-bold
                      text-emerald-400
                      text-sm
                    "
                  >
                    {roundPct(
                      intelligenceResult
                        .intelligence
                        .prediction
                        .recovery_probability
                    )}
                    %
                  </span>

                </div>


                <div
                  className="
                    w-full
                    bg-slate-800
                    rounded-full
                    h-2
                    overflow-hidden
                  "
                >

                  <div
                    className="
                      bg-emerald-400
                      h-full
                      rounded-full
                      transition-all
                      duration-500
                    "
                    style={{
                      width: `${roundPct(
                        intelligenceResult
                          .intelligence
                          .prediction
                          .recovery_probability
                      )}%`,
                    }}
                  />

                </div>


                <div
                  className="
                    text-[10px]
                    text-slate-500
                    flex
                    items-center
                    justify-between
                  "
                >

                  <span>
                    Class:{' '}
                    <strong>
                      {
                        intelligenceResult
                          .intelligence
                          .prediction
                          .prediction_class
                      }
                    </strong>
                  </span>

                  <span>
                    Model:{' '}
                    <strong>
                      RandomForestClassifier (v1.0.0)
                    </strong>
                  </span>

                </div>

              </div>

            )}


            {/* ==================================================
                Root Cause
            ================================================== */}

            {intelligenceResult.intelligence?.root_cause && (

              <div
                className="
                  bg-slate-950
                  p-4
                  rounded-xl
                  border
                  border-slate-800
                  space-y-2
                "
              >

                <div
                  className="
                    text-[11px]
                    font-bold
                    text-indigo-300
                    uppercase
                    flex
                    items-center
                    gap-1.5
                  "
                >

                  <Sparkles
                    className="
                      w-3.5
                      h-3.5
                      text-indigo-400
                    "
                  />

                  Root Cause Diagnostic

                </div>


                <div
                  className="
                    text-slate-200
                    font-semibold
                  "
                >
                  {
                    intelligenceResult
                      .intelligence
                      .root_cause
                      .primary_root_cause
                      ?.title
                    ||
                    'Payment Handshake Analysis'
                  }
                </div>


                <div
                  className="
                    text-slate-400
                    text-[11px]
                  "
                >
                  {
                    intelligenceResult
                      .intelligence
                      .root_cause
                      .primary_root_cause
                      ?.reason
                    ||
                    'Verified payment transaction handshake.'
                  }
                </div>

              </div>

            )}


            {/* ==================================================
                Recommended Strategy
            ================================================== */}

            {intelligenceResult.intelligence?.recommendation && (

              <div
                className="
                  bg-indigo-950/50
                  border
                  border-indigo-500/30
                  p-3.5
                  rounded-xl
                  space-y-1.5
                "
              >

                <div
                  className="
                    text-[10px]
                    font-bold
                    text-indigo-300
                    uppercase
                  "
                >
                  Recommended Strategy
                </div>


                <div
                  className="
                    font-bold
                    text-white
                    text-xs
                  "
                >
                  {
                    intelligenceResult
                      .intelligence
                      .recommendation
                      .recommended_strategy
                      ?.strategy
                    ||
                    'Smart Gateway Retry'
                  }
                </div>


                <div
                  className="
                    text-slate-300
                    text-[11px]
                  "
                >
                  {
                    intelligenceResult
                      .intelligence
                      .recommendation
                      .recommended_strategy
                      ?.reason
                  }
                </div>

              </div>

            )}


            {/* ==================================================
                Data Quality
            ================================================== */}

            {intelligenceResult.intelligence?.data_quality && (

              <div
                className="
                  bg-slate-900/60
                  p-3
                  rounded-xl
                  border
                  border-slate-800
                  text-[10px]
                  text-slate-400
                  flex
                  items-center
                  justify-between
                "
              >

                <span>
                  Data Completeness:{' '}

                  <strong
                    className="
                      text-emerald-400
                    "
                  >
                    {intPct(
                      intelligenceResult
                        .intelligence
                        .data_quality
                        .feature_completeness
                    )}
                    %
                  </strong>
                </span>


                <span>
                  Mode:{' '}

                  <strong
                    className="
                      text-indigo-400
                    "
                  >
                    {
                      intelligenceResult
                        .intelligence
                        .data_quality
                        .prediction_mode
                    }
                  </strong>
                </span>

              </div>

            )}

          </div>

        )}

      </Modal>

    </>
  );
}


// ============================================================
// Helper Functions
// ============================================================

function roundPct(value) {

  if (
    value === null ||
    value === undefined
  ) {
    return 65;
  }

  return Math.round(
    value > 1
      ? value
      : value * 100
  );
}


function intPct(value) {

  if (
    value === null ||
    value === undefined
  ) {
    return 100;
  }

  return Math.round(
    value > 1
      ? value
      : value * 100
  );
}