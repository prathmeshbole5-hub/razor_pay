/**
 * Razorpay Internal Operations Portal API Functions
 * Centralized API calls for ecosystem metrics, gateway health, failure intelligence, merchant network, and recovery intelligence.
 */

import { apiRequest } from './client';

/**
 * Fetch ecosystem-level internal dashboard metrics
 */
export async function getInternalDashboard() {
  return apiRequest('/api/internal/dashboard');
}

/**
 * Fetch gateway health and telemetry metrics
 */
export async function getGatewayHealth() {
  return apiRequest('/api/internal/gateway-health');
}

/**
 * Fetch ecosystem failure intelligence metrics
 */
export async function getFailureIntelligence() {
  return apiRequest('/api/internal/failure-intelligence');
}

/**
 * Fetch aggregated merchant network performance metrics
 */
export async function getMerchantNetwork() {
  return apiRequest('/api/internal/merchant-network');
}

/**
 * Fetch recovery strategy intelligence metrics
 */
export async function getRecoveryIntelligence() {
  return apiRequest('/api/internal/recovery-intelligence');
}

/**
 * Fetch all active and past infrastructure incidents from backend
 */
export async function getIncidents() {
  return apiRequest('/api/internal/incidents');
}

/**
 * Fetch all persisted live payments affected by a specific infrastructure incident
 */
export async function getIncidentAffectedPayments(incidentId) {
  return apiRequest(`/api/internal/incidents/${incidentId}/payments`);
}

/**
 * Execute simulated emergency mitigation on an infrastructure incident
 */
export async function executeIncidentMitigation(incidentId) {
  return apiRequest(`/api/internal/incidents/${incidentId}/mitigate`, {
    method: 'POST',
  });
}
