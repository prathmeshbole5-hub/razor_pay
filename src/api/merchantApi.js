/**
 * Merchant Portal API Functions
 * Centralized API calls for merchant dashboard, failed payments, recovery cases, and analytics.
 */

import { apiRequest } from './client';
import { CURRENT_MERCHANT_ID } from '../config/currentMerchant';

/**
 * Fetch merchant dashboard metrics
 * @param {string} merchantId 
 */
export async function getMerchantDashboard(merchantId = CURRENT_MERCHANT_ID) {
  return apiRequest(`/api/merchant/dashboard?merchant_id=${encodeURIComponent(merchantId)}`);
}

/**
 * Fetch failed payment records for merchant
 * @param {string} merchantId 
 */
export async function getFailedPayments(merchantId = CURRENT_MERCHANT_ID) {
  return apiRequest(`/api/merchant/payments/failed?merchant_id=${encodeURIComponent(merchantId)}`);
}

/**
 * Fetch recovery cases for merchant
 * @param {string} merchantId 
 */
export async function getRecoveryCases(merchantId = CURRENT_MERCHANT_ID) {
  return apiRequest(`/api/merchant/recovery-cases?merchant_id=${encodeURIComponent(merchantId)}`);
}

/**
 * Fetch merchant analytics breakdowns
 * @param {string} merchantId 
 */
export async function getMerchantAnalytics(merchantId = CURRENT_MERCHANT_ID) {
  return apiRequest(`/api/merchant/analytics?merchant_id=${encodeURIComponent(merchantId)}`);
}
