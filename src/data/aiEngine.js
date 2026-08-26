// RecoverAI Rule-Based Intelligence & Recommendation Engine Simulation

export function analyzePaymentFailure(payment) {
  const reason = (payment.failureReason || '').toLowerCase();
  const amount = payment.amount || 0;
  
  if (reason.includes('timeout') || reason.includes('gateway')) {
    return {
      recommendedStrategy: 'Smart Cool-down Retry',
      retryDelayMinutes: 12,
      recoveryProbability: 92,
      aiConfidence: 94,
      explanation: 'Bank gateway is experiencing high packet latency. A 12-minute cool-down window allows server queues to clear.',
      actionType: 'AUTO_RETRY'
    };
  } else if (reason.includes('limit') || reason.includes('insufficient')) {
    return {
      recommendedStrategy: 'WhatsApp 1-Click Payment Link + Partial Pay',
      retryDelayMinutes: 0,
      recoveryProbability: 85,
      aiConfidence: 88,
      explanation: 'Account transaction limit hit. Delivering a instant WhatsApp link allows customer to use alternate UPI or EMI.',
      actionType: 'CUSTOMER_NUDGE'
    };
  } else if (reason.includes('otp') || reason.includes('auth')) {
    return {
      recommendedStrategy: 'Express Checkout / SMS 2FA Nudge',
      retryDelayMinutes: 5,
      recoveryProbability: 89,
      aiConfidence: 91,
      explanation: 'Authentication dropoff detected. Customer did not receive OTP within 60s.',
      actionType: 'SMS_NUDGE'
    };
  } else if (reason.includes('risk') || reason.includes('decline')) {
    return {
      recommendedStrategy: 'Switch to Secondary Issuer Route / Tokenized EMI',
      retryDelayMinutes: 0,
      recoveryProbability: 74,
      aiConfidence: 80,
      explanation: 'Issuer bank anti-fraud flag triggered for high transaction value.',
      actionType: 'ROUTE_FALLBACK'
    };
  }

  return {
    recommendedStrategy: 'Standard Automated Retry',
    retryDelayMinutes: 30,
    recoveryProbability: 78,
    aiConfidence: 82,
    explanation: 'General transient network failure detected.',
    actionType: 'AUTO_RETRY'
  };
}

export function generateAICopilotResponse(question, merchantStats, failedPayments) {
  const query = question.toLowerCase();

  if (query.includes('why') || query.includes('increase') || query.includes('spike')) {
    return {
      text: "Based on real-time diagnostic analysis across your recent transactions, **38% of payment failures** are currently driven by **HDFC NetBanking & SBI Card 3DS Timeouts** during peak 16:00–17:00 traffic.",
      metrics: [
        { label: 'Dominant Issue', value: 'Bank Gateway Timeout' },
        { label: 'Impacted Revenue', value: '₹4,85,000' },
        { label: 'AI Recovery Rate', value: '82.1% via Smart Cool-down' }
      ],
      recommendation: "Enable automated 12-minute cool-down retries. RecoverAI predicts this will recover **₹1,24,500** of your current at-risk funds automatically.",
      suggestedAction: "Apply Recommended Strategy"
    };
  }

  if (query.includes('strategy') || query.includes('best') || query.includes('working')) {
    return {
      text: "**Smart Cool-down Retry** is currently your top performing recovery engine strategy, achieving an **82.1% conversion rate** across 112 attempts.",
      metrics: [
        { label: 'Top Strategy', value: 'Smart Cool-down' },
        { label: 'Conversion Rate', value: '82.1%' },
        { label: 'Total Recovered', value: '₹24,50,000' }
      ],
      recommendation: "Combine Smart Cool-down retries with instant WhatsApp payment link fallback for transactions exceeding ₹10,000.",
      suggestedAction: "Configure Recovery Rules"
    };
  }

  if (query.includes('how much') || query.includes('revenue') || query.includes('risk') || query.includes('still')) {
    return {
      text: "You currently have **₹12,45,000 at risk** across 24 failed transactions. Our AI recovery pipeline estimates **₹9,24,000 (74.2%)** is highly recoverable within 2 hours.",
      metrics: [
        { label: 'Current Revenue at Risk', value: '₹12,45,000' },
        { label: 'Estimated Recoverable', value: '₹9,24,000' },
        { label: 'Active Pipeline Cases', value: '14 Cases' }
      ],
      recommendation: "Execute pending retries for 4 high-value orders (over ₹30,000) that experienced temporary bank timeouts.",
      suggestedAction: "Execute Pending Retries"
    };
  }

  return {
    text: "RecoverAI continuously analyzes payment gateway telemetry, bank authorization codes, and customer interaction history for Apex Retail Pvt Ltd.",
    metrics: [
      { label: 'Total Recovered', value: '₹42,80,000' },
      { label: 'Overall Recovery Rate', value: '74.2%' },
      { label: 'Avg Recovery Time', value: '18 mins' }
    ],
    recommendation: "You can ask me questions like: 'Why did my payment failures increase?', 'Which recovery strategy is working best?', or 'How much revenue can still be recovered?'",
    suggestedAction: "View Failed Payments"
  };
}
