// Razorpay Internal Operations Data Store (Aggregated Ecosystem Intelligence)

export const internalEcosystemMetrics = {
  liveTPS: 1842,
  tpsTrend: '+124 TPS vs peak hour',
  globalSuccessRate: 99.82,
  successRateChange: '-0.14%',
  activeIncidentsCount: 2,
  affectedMerchantsCount: 310,
  revenueProtectedToday: 184200000, // ₹18.42 Cr
  activeMerchantsCount: 4820,
  recoveryEngineThroughput: '4,120 retries/min',
  systemStatus: 'DEGRADED_PERFORMANCE' // HEALTHY | DEGRADED_PERFORMANCE | CRITICAL_OUTAGE
};

export const gatewayHealthData = [
  {
    id: 'gw_hdfc_nb',
    name: 'HDFC NetBanking',
    type: 'NetBanking Gateway',
    status: 'DEGRADED',
    successRate: 94.2,
    latencyMs: 1420,
    failureSpikePct: 28.4,
    affectedMerchants: 142,
    hourlyVolume: 124000,
    errorDominant: 'GATEWAY_TIMEOUT (504)',
    lastUpdated: '10s ago'
  },
  {
    id: 'gw_sbi_otp',
    name: 'SBI Card OTP 3DS Server',
    type: 'Card OTP Authentication',
    status: 'OUTAGE',
    successRate: 82.5,
    latencyMs: 3850,
    failureSpikePct: 42.1,
    affectedMerchants: 310,
    hourlyVolume: 285000,
    errorDominant: 'OTP_SMS_GATEWAY_DOWN (503)',
    lastUpdated: '5s ago'
  },
  {
    id: 'gw_icici_upi',
    name: 'ICICI UPI Router',
    type: 'UPI Infrastructure',
    status: 'HEALTHY',
    successRate: 99.91,
    latencyMs: 180,
    failureSpikePct: -1.2,
    affectedMerchants: 0,
    hourlyVolume: 840000,
    errorDominant: 'NONE',
    lastUpdated: '2s ago'
  },
  {
    id: 'gw_axis_wallet',
    name: 'Axis Bank Stack',
    type: 'Bank API Direct',
    status: 'HEALTHY',
    successRate: 99.85,
    latencyMs: 210,
    failureSpikePct: 0.4,
    affectedMerchants: 0,
    hourlyVolume: 195000,
    errorDominant: 'NONE',
    lastUpdated: '4s ago'
  },
  {
    id: 'gw_paytm_upi',
    name: 'Paytm UPI Stack',
    type: 'UPI Infrastructure',
    status: 'HEALTHY',
    successRate: 99.78,
    latencyMs: 240,
    failureSpikePct: 1.1,
    affectedMerchants: 4,
    hourlyVolume: 420000,
    errorDominant: 'USER_CANCELLED',
    lastUpdated: '3s ago'
  },
  {
    id: 'gw_rzp_smart',
    name: 'Razorpay Smart Recovery Engine',
    type: 'Internal Routing Service',
    status: 'HEALTHY',
    successRate: 99.98,
    latencyMs: 45,
    failureSpikePct: 0.0,
    affectedMerchants: 0,
    hourlyVolume: 1540000,
    errorDominant: 'NONE',
    lastUpdated: 'Live'
  }
];

export const failureAnomalies = [
  {
    id: 'anom_101',
    severity: 'CRITICAL',
    title: 'SBI Card OTP 3DS Delivery Timeout Spike',
    description: 'SBI 3D-Secure SMS gateway latency has exceeded 3,800ms, causing massive OTP expiration for credit card authorizations.',
    affectedMerchants: 310,
    impactedTransactions: 14200,
    estimatedRevenueImpact: 42500000,
    detectedAt: '2026-08-21T16:30:00',
    confidenceScore: 98,
    recommendedAction: 'Automated Route Reroute: Direct SBI card transactions to Visa Direct Tokenized 1-Click Auth.',
    heatmapRegion: 'National / SBI Card Stack',
    status: 'MITIGATING'
  },
  {
    id: 'anom_102',
    severity: 'WARNING',
    title: 'HDFC Corporate NetBanking Session Drops',
    description: 'Intermittent 504 Gateway Timeouts detected on HDFC Corporate portal 2FA authentication steps.',
    affectedMerchants: 142,
    impactedTransactions: 3100,
    estimatedRevenueImpact: 18400000,
    detectedAt: '2026-08-21T17:05:00',
    confidenceScore: 91,
    recommendedAction: 'Apply 12-minute Smart Retry queue and nudge high-ticket clients to NEFT/RTGS express payment.',
    heatmapRegion: 'HDFC Corporate API Hub',
    status: 'INVESTIGATING'
  }
];

export const merchantSegmentsData = [
  { segment: 'E-commerce & Retail', merchantCount: 1840, volumeShare: '42%', avgSuccessRate: 99.81, riskAmount: 18400000 },
  { segment: 'SaaS & Subscriptions', merchantCount: 1120, volumeShare: '28%', avgSuccessRate: 99.88, riskAmount: 9200000 },
  { segment: 'Digital Goods & Gaming', merchantCount: 940, volumeShare: '18%', avgSuccessRate: 99.74, riskAmount: 14500000 },
  { segment: 'Travel & Hospitality', merchantCount: 520, volumeShare: '8%', avgSuccessRate: 99.65, riskAmount: 21000000 },
  { segment: 'EdTech & Utilities', merchantCount: 400, volumeShare: '4%', avgSuccessRate: 99.89, riskAmount: 3100000 }
];

export const systemFlowNodes = [
  { id: 'node_cust', label: 'End Consumer', category: 'USER', tps: 1842, status: 'NORMAL' },
  { id: 'node_merch', label: 'Merchant SDK / API', category: 'INGRESS', tps: 1842, status: 'NORMAL' },
  { id: 'node_rzp', label: 'Razorpay Gateway Router', category: 'CORE', tps: 1842, status: 'NORMAL' },
  { id: 'node_bank_hdfc', label: 'HDFC NetBanking', category: 'BANK', tps: 420, status: 'DEGRADED', latency: '1420ms' },
  { id: 'node_bank_sbi', label: 'SBI Card OTP', category: 'BANK', tps: 680, status: 'OUTAGE', latency: '3850ms' },
  { id: 'node_bank_icici', label: 'ICICI UPI Engine', category: 'BANK', tps: 742, status: 'HEALTHY', latency: '180ms' },
  { id: 'node_recover_ai', label: 'RecoverAI Engine', category: 'INTELLIGENCE', tps: 340, status: 'ACTIVE_RECOVERY' },
  { id: 'node_fallback', label: 'Smart Fallback Route', category: 'RECOVERY', tps: 285, status: 'SUCCESS' }
];

export const internalAnalytics = {
  hourlyTPS: [
    { time: '12:00', tps: 1420, successRate: 99.91 },
    { time: '13:00', tps: 1680, successRate: 99.88 },
    { time: '14:00', tps: 1790, successRate: 99.85 },
    { time: '15:00', tps: 1910, successRate: 99.80 },
    { time: '16:00', tps: 1880, successRate: 99.72 },
    { time: '17:00', tps: 1842, successRate: 99.82 }
  ],
  bankSuccessComparison: [
    { bank: 'ICICI UPI', successRate: 99.91, volume: '840K txns' },
    { bank: 'Axis Bank', successRate: 99.85, volume: '195K txns' },
    { bank: 'Paytm Stack', successRate: 99.78, volume: '420K txns' },
    { bank: 'HDFC Bank', successRate: 94.20, volume: '124K txns' },
    { bank: 'SBI Card', successRate: 82.50, volume: '285K txns' }
  ]
};
