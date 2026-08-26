/**
 * RecoverAI Hackathon Demo & Presentation Configuration
 * Centralizes real dataset records and step-by-step presentation flow for demonstration.
 */

export const DEMO_MERCHANT_ID = 'm_1004';
export const DEMO_PAYMENT_ID = 'pay_104421';
export const DEMO_MERCHANT_NAME = 'CloudMart';

export const DEMO_STEPS = [
  {
    step: 1,
    title: 'Merchant Dashboard — Revenue at Risk',
    portal: 'merchant',
    tab: 'dashboard',
    narration: 'RecoverAI tracks live payment volume, success rates, and total revenue at risk (₹12.5L ecosystem risk) in real time.',
    highlight: 'Revenue at Risk & Global Success Rate'
  },
  {
    step: 2,
    title: 'Payment Denials & Failure Inspection',
    portal: 'merchant',
    tab: 'denials',
    narration: `Inspect real failed payment payloads from the dataset. Click any failed payment (e.g. #${DEMO_PAYMENT_ID}) to analyze root cause.`,
    highlight: 'Failed Transactions Payload Table'
  },
  {
    step: 3,
    title: 'AI Recovery Diagnostics & ML Model Prediction',
    portal: 'merchant',
    tab: 'denials',
    narration: `Our trained RandomForest ML model predicts a 59.28% recovery probability for payment #${DEMO_PAYMENT_ID} without data leakage.`,
    highlight: 'ML Recovery Probability & Confidence Score'
  },
  {
    step: 4,
    title: 'Root Cause & AI Recommended Action',
    portal: 'merchant',
    tab: 'cases',
    narration: 'The Root Cause Engine identifies "Customer Checkout Drop-off" and recommends "OTP Reminder" with an expected recovery probability of 50.2%.',
    highlight: 'AI Root Cause & Strategy Recommendation'
  },
  {
    step: 5,
    title: 'Razorpay Internal Operations Command Center',
    portal: 'internal',
    tab: 'overview',
    narration: 'Switching to Razorpay Internal Operations Portal: Monitors ecosystem gateway telemetries, active incidents, and bank error spikes.',
    highlight: 'Bank & Gateway Telemetry Grid'
  },
  {
    step: 6,
    title: 'System Architecture & Data Flow',
    portal: 'internal',
    tab: 'flow',
    narration: 'Dual-Portal Architecture: Strict merchant domain isolation on client endpoints + Ecosystem-wide operational intelligence for Razorpay ops.',
    highlight: 'RecoverAI Pipeline Architecture'
  }
];
