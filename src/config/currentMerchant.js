/**
 * Centralized Merchant Configuration
 * Defines the current logged-in merchant ID for client-side API requests.
 */

import { DEMO_MERCHANT_ID, DEMO_MERCHANT_NAME } from './demoConfig';

export const CURRENT_MERCHANT_ID = DEMO_MERCHANT_ID;
export const CURRENT_MERCHANT_NAME = DEMO_MERCHANT_NAME;

export function getMerchantId() {
  return CURRENT_MERCHANT_ID;
}
