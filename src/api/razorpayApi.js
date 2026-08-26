import { apiRequest } from './client';

/**
 * Razorpay Test Mode API Client
 */

export async function createRazorpayOrder(amount, currency = 'INR', merchantId = 'm_1004', receipt = 'recoverai_demo_order') {
  return apiRequest('/api/payments/create-order', {
    method: 'POST',
    body: JSON.stringify({
      amount: Number(amount),
      currency,
      merchant_id: merchantId,
      receipt
    })
  });
}

export async function verifyRazorpayPayment(paymentId, orderId, signature, merchantId = 'm_1004') {
  return apiRequest('/api/payments/verify', {
    method: 'POST',
    body: JSON.stringify({
      razorpay_payment_id: paymentId,
      razorpay_order_id: orderId,
      razorpay_signature: signature,
      merchant_id: merchantId
    })
  });
}

export async function getLivePaymentEvents(merchantId = 'm_1004') {
  return apiRequest(`/api/payments/events?merchant_id=${encodeURIComponent(merchantId)}`);
}
