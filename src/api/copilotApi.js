import { API_BASE_URL, apiRequest } from './client';

export async function fetchCopilotQuery(query, merchantId = 'm_1004', mode = 'merchant') {
  try {
    return await apiRequest('/api/copilot/query', {
      method: 'POST',
      body: JSON.stringify({ query, merchant_id: merchantId, mode })
    });
  } catch (error) {
    console.warn('[Copilot API] Falling back to local simulation due to network/API state:', error);
    return null;
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
