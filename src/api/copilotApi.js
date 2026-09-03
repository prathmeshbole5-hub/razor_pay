import { API_BASE_URL, apiRequest } from './client';

export async function fetchCopilotQuery(query, merchantId = 'm_1004', mode = 'merchant', history = null) {
  try {
    return await apiRequest('/api/copilot/query', {
      method: 'POST',
      body: JSON.stringify({ query, merchant_id: merchantId, mode, history })
    });
  } catch (error) {
    console.error('[Copilot API] Backend request failed:', error);
    return {
      error: true,
      message: error?.message || 'AI Copilot service is temporarily unavailable. Please retry.'
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
