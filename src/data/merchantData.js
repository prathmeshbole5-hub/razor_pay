// Merchant Specific Mock Data Store for Apex Retail Pvt Ltd
export const merchantProfile = {
  merchantId: 'merch_apex_9082',
  businessName: 'Apex Retail Pvt Ltd',
  legalName: 'Apex Online Retail Enterprises India Pvt Ltd',
  email: 'finance@apexretail.in',
  phone: '+91 98765 43210',
  businessType: 'E-commerce & Retail',
  monthlyVolume: 14500000,
  currency: 'INR',
  joinedDate: '2024-01-15',
  apiKeyMasked: 'rzp_live_9a8B****42xY',
  webhookUrl: 'https://api.apexretail.in/v1/webhooks/recoverai',
  preferences: {
    autoRetryEnabled: true,
    maxRetryAttempts: 3,
    smartFallbackRoute: true,
    whatsappRecoveryMsg: true,
    emailRecoveryNudge: true,
    highValueThreshold: 25000
  }
};

export const merchantStats = {
  revenueAtRisk: 1245000,
  failedCountAtRisk: 24,
  revenueRecovered: 4280000,
  recoveryRate: 74.2,
  recoveryRateTrend: '+3.8%',
  activeCasesCount: 14,
  averageRecoveryTime: '18 mins'
};

export const timeframePerformanceData = {
  '7D': [
    { date: 'Mon', atRisk: 180000, recovered: 142000, failureCount: 8 },
    { date: 'Tue', atRisk: 210000, recovered: 168000, failureCount: 10 },
    { date: 'Wed', atRisk: 145000, recovered: 120000, failureCount: 6 },
    { date: 'Thu', atRisk: 290000, recovered: 235000, failureCount: 14 },
    { date: 'Fri', atRisk: 310000, recovered: 248000, failureCount: 15 },
    { date: 'Sat', atRisk: 195000, recovered: 160000, failureCount: 9 },
    { date: 'Sun', atRisk: 115000, recovered: 98000, failureCount: 5 }
  ],
  '30D': [
    { date: 'Week 1', atRisk: 920000, recovered: 710000, failureCount: 42 },
    { date: 'Week 2', atRisk: 1150000, recovered: 890000, failureCount: 54 },
    { date: 'Week 3', atRisk: 840000, recovered: 670000, failureCount: 38 },
    { date: 'Week 4', atRisk: 1370000, recovered: 1010000, failureCount: 61 }
  ],
  '3M': [
    { date: 'Jun', atRisk: 3800000, recovered: 2850000, failureCount: 180 },
    { date: 'Jul', atRisk: 4200000, recovered: 3200000, failureCount: 205 },
    { date: 'Aug', atRisk: 4440000, recovered: 3280000, failureCount: 212 }
  ],
  '6M': [
    { date: 'Mar', atRisk: 3100000, recovered: 2200000, failureCount: 150 },
    { date: 'Apr', atRisk: 3500000, recovered: 2600000, failureCount: 165 },
    { date: 'May', atRisk: 3700000, recovered: 2750000, failureCount: 172 },
    { date: 'Jun', atRisk: 3800000, recovered: 2850000, failureCount: 180 },
    { date: 'Jul', atRisk: 4200000, recovered: 3200000, failureCount: 205 },
    { date: 'Aug', atRisk: 4440000, recovered: 3280000, failureCount: 212 }
  ]
};

export const merchantAIInsight = {
  id: 'insight_901',
  title: 'Network Timeout Spike Detected in HDFC UPI',
  description: 'Payment failures caused by bank gateway timeouts have increased by 18% over the past 24 hours.',
  recommendation: 'Schedule smart retry after a 12-minute cool-down window and offer 1-click UPI Deep Link fallback.',
  potentialRecovery: 124500,
  affectedPaymentsCount: 7,
  confidenceScore: 94,
  actionText: 'Review Affected Cases'
};

export const merchantFailedPayments = [
  {
    id: 'pay_Nz9K28xL901',
    customer: 'Vikram Malhotra',
    email: 'v.malhotra@gmail.com',
    phone: '+91 98201 11223',
    amount: 34999,
    method: 'Credit Card',
    gateway: 'HDFC Card Gateway',
    bank: 'HDFC Bank',
    failureReason: 'Bank Timeout (3D Secure Timeout)',
    errorCode: 'GATEWAY_TIMEOUT',
    status: 'IN_RECOVERY',
    attempts: 1,
    timestamp: '2026-08-21T17:15:00',
    aiConfidence: 92,
    aiRecommendation: 'Retry in 15 mins via ICICI Smart Fallback',
    timeline: [
      { time: '17:15:00', event: 'Initial Transaction Failed (Bank Timeout)', type: 'error' },
      { time: '17:15:02', event: 'AI Diagnostics: HDFC 3DS Server Congested', type: 'info' },
      { time: '17:15:05', event: 'Smart Recovery Strategy Queued: 15m Cool-down Retry', type: 'success' }
    ]
  },
  {
    id: 'pay_Lp8M11vK402',
    customer: 'Ananya Sharma',
    email: 'ananya.s@outlook.com',
    phone: '+91 97112 44556',
    amount: 18500,
    method: 'UPI Direct',
    gateway: 'ICICI UPI Gateway',
    bank: 'SBI',
    failureReason: 'Insufficient Funds / Daily Limit Exceeded',
    errorCode: 'UPI_LIMIT_EXCEEDED',
    status: 'ACTION_REQUIRED',
    attempts: 2,
    timestamp: '2026-08-21T16:48:00',
    aiConfidence: 85,
    aiRecommendation: 'Send WhatsApp 1-Click Payment Link with Partial Pay option',
    timeline: [
      { time: '16:48:00', event: 'Initial UPI Transaction Failed (Limit Exceeded)', type: 'error' },
      { time: '16:50:00', event: 'Auto-retry attempted (Failed)', type: 'warning' },
      { time: '16:50:04', event: 'AI Suggestion: Nudge customer via WhatsApp link', type: 'info' }
    ]
  },
  {
    id: 'pay_Kq7N44tY803',
    customer: 'Rohan Gupta',
    email: 'rohan.g@techcorp.io',
    phone: '+91 99887 66554',
    amount: 52000,
    method: 'NetBanking',
    gateway: 'Axis NetBanking',
    bank: 'Axis Bank',
    failureReason: 'Session Expired during 2FA',
    errorCode: 'NETBANKING_AUTH_DROP',
    status: 'RECOVERED',
    attempts: 1,
    timestamp: '2026-08-21T15:30:00',
    aiConfidence: 98,
    aiRecommendation: 'Smart Auto-retry executed via secondary route',
    timeline: [
      { time: '15:30:00', event: 'Netbanking Session Dropped', type: 'error' },
      { time: '15:32:00', event: 'Auto-retried via Razorpay Express Checkout Link', type: 'info' },
      { time: '15:34:12', event: 'Payment Successfully Recovered (₹52,000)', type: 'success' }
    ]
  },
  {
    id: 'pay_Wp3Q99mR104',
    customer: 'Meera Deshmukh',
    email: 'meera.d@yahoo.co.in',
    phone: '+91 98450 12345',
    amount: 12400,
    method: 'Debit Card',
    gateway: 'SBI Card Gateway',
    bank: 'State Bank of India',
    failureReason: 'OTP Authentication Timeout',
    errorCode: 'OTP_EXPIRED',
    status: 'IN_RECOVERY',
    attempts: 1,
    timestamp: '2026-08-21T14:20:00',
    aiConfidence: 89,
    aiRecommendation: 'Prompt SMS OTP resend and offer UPI QR Code',
    timeline: [
      { time: '14:20:00', event: 'OTP Expired on Bank Page', type: 'error' },
      { time: '14:21:00', event: 'AI Triggered WhatsApp Payment Reminder', type: 'info' }
    ]
  },
  {
    id: 'pay_Xz2R77kP205',
    customer: 'Siddharth Nair',
    email: 'snair@designstudio.com',
    phone: '+91 98920 33445',
    amount: 84000,
    method: 'Credit Card (EMI)',
    gateway: 'HDFC Card Gateway',
    bank: 'HDFC Bank',
    failureReason: 'Card Limit Lock / Risk Block',
    errorCode: 'BANK_RISK_DECLINE',
    status: 'ACTION_REQUIRED',
    attempts: 1,
    timestamp: '2026-08-21T13:10:00',
    aiConfidence: 78,
    aiRecommendation: 'Recommend EMI on alternate card or Netbanking',
    timeline: [
      { time: '13:10:00', event: 'Risk Blocked by Issuer Bank', type: 'error' },
      { time: '13:11:00', event: 'Customer support flag created', type: 'warning' }
    ]
  },
  {
    id: 'pay_Ab5C66vM306',
    customer: 'Pooja Verma',
    email: 'pooja.verma@gmail.com',
    phone: '+91 97441 55667',
    amount: 6750,
    method: 'UPI AutoPay',
    gateway: 'Razorpay UPI Hub',
    bank: 'PhonePe / YES Bank',
    failureReason: 'Mandate Execution Timeout',
    errorCode: 'MANDATE_TIMEOUT',
    status: 'RECOVERED',
    attempts: 2,
    timestamp: '2026-08-21T11:45:00',
    aiConfidence: 96,
    aiRecommendation: 'Retry mandate at off-peak banking window (11:45 AM)',
    timeline: [
      { time: '08:00:00', event: 'Mandate failed during early morning peak', type: 'error' },
      { time: '11:45:00', event: 'Smart Off-peak Retry Executed Successfully', type: 'success' }
    ]
  }
];

export const merchantRecoveryCases = [
  {
    caseId: 'rc_8901',
    paymentId: 'pay_Nz9K28xL901',
    customer: 'Vikram Malhotra',
    amount: 34999,
    failureReason: 'Bank Timeout (3D Secure Timeout)',
    strategy: 'Smart Delayed Retry (15m Cool-down)',
    aiConfidence: 92,
    currentStage: 2, // 0: Failed, 1: AI Analysis, 2: Retry Scheduled, 3: Customer Contacted, 4: Recovered
    stages: ['Payment Failed', 'AI Diagnostics', 'Retry Scheduled', 'Customer Contacted', 'Revenue Recovered'],
    scheduledTime: '17:30:00',
    estimatedRecoveryProb: '92%'
  },
  {
    caseId: 'rc_8902',
    paymentId: 'pay_Lp8M11vK402',
    customer: 'Ananya Sharma',
    amount: 18500,
    failureReason: 'UPI Daily Limit Exceeded',
    strategy: 'WhatsApp 1-Click Payment Link',
    aiConfidence: 85,
    currentStage: 3,
    stages: ['Payment Failed', 'AI Diagnostics', 'Retry Scheduled', 'Customer Contacted', 'Revenue Recovered'],
    scheduledTime: 'Active (Sent 10m ago)',
    estimatedRecoveryProb: '85%'
  },
  {
    caseId: 'rc_8903',
    paymentId: 'pay_Kq7N44tY803',
    customer: 'Rohan Gupta',
    amount: 52000,
    failureReason: 'Session Expired during 2FA',
    strategy: 'Express Checkout Link Fallback',
    aiConfidence: 98,
    currentStage: 4,
    stages: ['Payment Failed', 'AI Diagnostics', 'Retry Scheduled', 'Customer Contacted', 'Revenue Recovered'],
    scheduledTime: 'Completed at 15:34',
    estimatedRecoveryProb: '100%'
  },
  {
    caseId: 'rc_8904',
    paymentId: 'pay_Wp3Q99mR104',
    customer: 'Meera Deshmukh',
    amount: 12400,
    failureReason: 'OTP Authentication Timeout',
    strategy: 'SMS & WhatsApp Smart Nudge',
    aiConfidence: 89,
    currentStage: 2,
    stages: ['Payment Failed', 'AI Diagnostics', 'Retry Scheduled', 'Customer Contacted', 'Revenue Recovered'],
    scheduledTime: '17:45:00',
    estimatedRecoveryProb: '89%'
  }
];

export const merchantActivityFeed = [
  { id: 'act_1', time: '17:15', title: 'New Payment Failure', desc: '₹34,999 from Vikram Malhotra (Bank Timeout)', type: 'failure' },
  { id: 'act_2', time: '16:50', title: 'AI Diagnostics Completed', desc: 'Identified HDFC 3DS server timeout pattern', type: 'ai' },
  { id: 'act_3', time: '15:34', title: 'Payment Recovered', desc: '₹52,000 recovered for Rohan Gupta via Secondary Route', type: 'success' },
  { id: 'act_4', time: '14:21', title: 'Customer Nudge Sent', desc: 'WhatsApp 1-Click Pay link delivered to Meera Deshmukh', type: 'nudge' },
  { id: 'act_5', time: '11:45', title: 'Mandate Recovered', desc: '₹6,750 recovered via off-peak retry schedule', type: 'success' }
];

export const merchantAnalytics = {
  failureReasons: [
    { name: 'Bank Timeout', value: 38, count: 92, amount: 485000, color: '#6366f1' },
    { name: 'OTP Expiry / Dropoff', value: 24, count: 58, amount: 290000, color: '#8b5cf6' },
    { name: 'Insufficient Funds', value: 18, count: 44, amount: 210000, color: '#f59e0b' },
    { name: 'Risk / Security Decline', value: 12, count: 29, amount: 160000, color: '#f43f5e' },
    { name: 'Network Connection Error', value: 8, count: 19, amount: 100000, color: '#06b6d4' }
  ],
  methodBreakdown: [
    { name: 'UPI (GPay/PhonePe)', volume: 6400000, failures: 42, recoveryRate: 82.5 },
    { name: 'Credit Card', volume: 4800000, failures: 34, recoveryRate: 71.0 },
    { name: 'NetBanking', volume: 2100000, failures: 22, recoveryRate: 64.8 },
    { name: 'Debit Card', volume: 1200000, failures: 18, recoveryRate: 68.2 }
  ],
  strategyConversion: [
    { strategy: 'Smart Cool-down Retry', attempts: 112, recovered: 92, rate: 82.1, revenue: 2450000 },
    { strategy: 'WhatsApp 1-Click Link', attempts: 68, recovered: 51, rate: 75.0, revenue: 1120000 },
    { strategy: 'Secondary Route Switch', attempts: 45, recovered: 34, rate: 75.5, revenue: 710000 }
  ]
};
