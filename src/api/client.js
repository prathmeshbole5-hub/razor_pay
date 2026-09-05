/**
 * Centralized API Client with Timeout & Reliability Hardening
 * Configures base URL from environment variables with development fallback.
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (
  typeof window !== 'undefined' && 
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://127.0.0.1:8002'
    : 'https://razor-pay-2ycs.onrender.com'
);

export const DEFAULT_TIMEOUT_MS = Number(import.meta.env.VITE_API_TIMEOUT_MS) || 60000;
export const COPILOT_TIMEOUT_MS = Number(import.meta.env.VITE_COPILOT_TIMEOUT_MS) || DEFAULT_TIMEOUT_MS;

export async function apiRequest(endpoint, options = {}, timeoutMs = DEFAULT_TIMEOUT_MS) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const controller = new AbortController();

  if (options?.signal) {
    if (options.signal.aborted) {
      controller.abort();
    } else {
      options.signal.addEventListener('abort', () => controller.abort(), { once: true });
    }
  }

  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const defaultHeaders = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  };

  const { signal: _, ...restOptions } = options;

  const config = {
    ...restOptions,
    signal: controller.signal,
    headers: {
      ...defaultHeaders,
      ...options.headers
    }
  };

  try {
    const response = await fetch(url, config);
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      const errorText = await response.text().catch(() => '');
      let parsedDetail = '';
      try {
        const parsed = JSON.parse(errorText);
        parsedDetail = parsed.detail || parsed.message || errorText;
      } catch (e) {
        parsedDetail = errorText || response.statusText;
      }
      throw new Error(parsedDetail || `API Error [${response.status}]`);
    }

    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error(`Backend is waking up. Request timed out (${Math.round(timeoutMs / 1000)}s) while connecting to backend service. Please retry in a few seconds.`);
    }
    if (error.message && error.message.includes('Failed to fetch')) {
      throw new Error('Backend is waking up or temporarily unavailable. Please retry in a few seconds.');
    }
    throw error;
  }
}
