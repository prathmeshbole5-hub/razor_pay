import { API_BASE_URL, apiRequest } from './client';

export async function createRazorpayOrder(amount = 100, merchantId = 'm_1004', currency = 'INR') {
  return await apiRequest('/api/payments/create-order', {
    method: 'POST',
    body: JSON.stringify({
      amount: parseFloat(amount),
      currency,
      merchant_id: merchantId,
      receipt: `recoverai_test_${Date.now()}`
    })
  });
}

export async function verifyRazorpayPayment(payload) {
  return await apiRequest('/api/payments/verify', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export async function getLivePaymentIntelligence(paymentId, merchantId = 'm_1004') {
  return await apiRequest(`/api/merchant/live-payments/${paymentId}/intelligence?merchant_id=${encodeURIComponent(merchantId)}`);
}

export async function getLivePaymentEvents(merchantId = 'm_1004') {
  return await apiRequest(`/api/merchant/live-payments/events?merchant_id=${encodeURIComponent(merchantId)}`);
}

export async function getMerchantLivePaymentEvents(merchantId = 'm_1004') {
  return await apiRequest(`/api/merchant/live-payments/events?merchant_id=${encodeURIComponent(merchantId)}`);
}

export async function getMerchantPaymentIntelligence(paymentId, merchantId = 'm_1004') {
  return await apiRequest(`/api/merchant/intelligence/payment-analysis/${paymentId}?merchant_id=${encodeURIComponent(merchantId)}`);
}

export async function getInternalIntelligenceOverview() {
  return await apiRequest('/api/internal/dashboard');
}

export async function triggerSimulateEvent(eventType = 'failure') {
  return await apiRequest(`/api/demo/simulate?event_type=${encodeURIComponent(eventType)}`, {
    method: 'POST'
  });
}

export async function resetDemoSimulation() {
  return await apiRequest('/api/demo/reset', {
    method: 'POST'
  });
}

export async function executeLivePaymentAction(paymentId, merchantId = 'm_1004', actionType = 'smart_retry') {
  return await apiRequest(`/api/merchant/live-payments/${encodeURIComponent(paymentId)}/actions`, {
    method: 'POST',
    body: JSON.stringify({
      merchant_id: merchantId,
      action_type: actionType
    })
  });
}

export async function getLivePaymentActions(paymentId, merchantId = 'm_1004') {
  return await apiRequest(`/api/merchant/live-payments/${encodeURIComponent(paymentId)}/actions?merchant_id=${encodeURIComponent(merchantId)}`);
}

export async function getLivePaymentTimeline(paymentId, merchantId = 'm_1004') {
  return await apiRequest(`/api/merchant/live-payments/${encodeURIComponent(paymentId)}/timeline?merchant_id=${encodeURIComponent(merchantId)}`);
}

export async function resetAllDemoData() {
  return await apiRequest('/api/demo/reset-all', {
    method: 'POST'
  });
}

export async function seedDemoScenario() {
  return await apiRequest('/api/demo/seed', {
    method: 'POST'
  });
}


