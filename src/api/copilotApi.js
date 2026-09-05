import { API_BASE_URL, apiRequest, COPILOT_TIMEOUT_MS } from './client';

export async function fetchCopilotQuery(query, merchantId = 'm_1004', mode = 'merchant', history = null) {
  try {
    return await apiRequest('/api/copilot/query', {
      method: 'POST',
      body: JSON.stringify({ query, merchant_id: merchantId, mode, history })
    }, COPILOT_TIMEOUT_MS);
  } catch (error) {
    console.error('[Copilot API] Backend request failed:', error);
    return {
      error: true,
      message: error?.message || 'Backend is waking up. Please retry in a few seconds.'
    };
  }
}

export async function fetchCopilotPrompts(mode = 'merchant') {
  try {
    return await apiRequest(`/api/copilot/prompts?mode=${encodeURIComponent(mode)}`);
  } catch (error) {
    console.warn('[Copilot API] Prompts fallback:', error);
    return null;
  }
}
