import React, { useState, useEffect } from 'react';
import {
  DollarSign,
  CheckCircle2,
  TrendingUp,
  RefreshCw,
  Search,
  Zap,
  Activity,
  AlertCircle,
  ChevronRight,
  AlertTriangle
} from 'lucide-react';
import { StatCard } from '../../shared/components/Card';
import Button from '../../shared/components/Button';
import Badge from '../../shared/components/Badge';
import AIInsightCard from '../components/AIInsightCard';
import PerformanceChart from '../components/PerformanceChart';
import PaymentDetailDrawer from '../components/PaymentDetailDrawer';
import LivePaymentTestCard from '../components/LivePaymentTestCard';
import LivePaymentActivityList from '../components/LivePaymentActivityList';
import {
  merchantAIInsight,
  merchantActivityFeed
} from '../../data/merchantData';
import { getMerchantDashboard, getFailedPayments } from '../../api/merchantApi';
import { CURRENT_MERCHANT_ID } from '../../config/currentMerchant';

export default function MerchantDashboard({ onNavigate }) {
  const [selectedPayment, setSelectedPayment] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const [dashboardData, setDashboardData] = useState(null);
  const [failedPayments, setFailedPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [dash, failures] = await Promise.all([
        getMerchantDashboard(CURRENT_MERCHANT_ID),
        getFailedPayments(CURRENT_MERCHANT_ID)
      ]);
      setDashboardData(dash);
      setFailedPayments(failures || []);
    } catch (err) {
      console.error('Failed to load merchant dashboard data:', err);
      setError(err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const formattedPayments = failedPayments.map((p) => ({
    id: p.payment_id,
    merchant_id: p.merchant_id || CURRENT_MERCHANT_ID,
    customer: p.customer_id ? `Customer (${p.customer_id})` : `User ${p.payment_id.slice(-4)}`,
    amount: p.amount_inr,
    method: p.payment_method,
    gateway: p.gateway,
    failureReason: p.failure_category,
    errorCode: p.error_code,
    status: p.retryable ? 'IN_RECOVERY' : 'ACTION_REQUIRED',
    created_at: p.created_at,
    attempts: 1,
    bank: p.gateway
  }));

  const filteredPayments = formattedPayments.filter(
    (p) =>
      p.customer.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.failureReason.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleOpenDrawer = (payment) => {
    setSelectedPayment(payment);
    setDrawerOpen(true);
  };

  if (loading) {
    return (
      <div className="space-y-8 animate-fadeIn p-4">
        <div className="h-24 bg-slate-900/80 border border-slate-800 rounded-2xl animate-pulse" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-slate-900/80 border border-slate-800 rounded-2xl animate-pulse" />
          ))}
        </div>
        <div className="h-80 bg-slate-900/80 border border-slate-800 rounded-2xl animate-pulse" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-rose-950/40 border border-rose-500/30 p-6 rounded-2xl space-y-4 animate-fadeIn">
        <div className="flex items-center gap-3 text-rose-400 font-bold">
          <AlertTriangle className="w-5 h-5" />
          <span>Failed to load backend dashboard data</span>
        </div>
        <p className="text-xs text-slate-300">{error}</p>
        <Button variant="outline" size="sm" onClick={loadData}>
          Retry Connection
        </Button>
      </div>
    );
  }

  const atRiskLakhs = dashboardData ? (dashboardData.revenue_at_risk / 100000).toFixed(2) : '0';

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Top Greeting Context Banner */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 p-6 rounded-2xl">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl sm:text-2xl font-extrabold text-white">Merchant Overview</h2>
            <span className="px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 text-xs font-semibold border border-indigo-500/30">
              ID: {dashboardData?.merchant_id || CURRENT_MERCHANT_ID}
            </span>
          </div>
          <p className="text-sm text-slate-300 mt-1">
            <strong className="text-rose-400 font-bold">₹{atRiskLakhs}L is currently at risk</strong> across {dashboardData?.failed_payments || 0} failed payments. RecoverAI has {dashboardData?.active_recovery_cases || 0} recovery workflows active.
          </p>
        </div>

        <Button
          variant="accent"
          size="md"
          icon={Zap}
          onClick={() => onNavigate('copilot')}
        >
          Ask AI Assistant
        </Button>
      </div>

      {/* Primary Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard
          title="Revenue At Risk"
          value={`₹${(dashboardData?.revenue_at_risk || 0).toLocaleString('en-IN')}`}
          subtitle={`${dashboardData?.failed_payments || 0} failed transactions`}
          icon={DollarSign}
          accentColor="rose"
          trend="At Risk"
          trendType="negative"
        />

        <StatCard
          title="Revenue Recovered"
          value={`₹${(dashboardData?.revenue_recovered || 0).toLocaleString('en-IN')}`}
          subtitle="Recovered by RecoverAI"
          icon={CheckCircle2}
          accentColor="emerald"
          trend="Active Recovery"
          trendType="positive"
        />

        <StatCard
          title="Recovery Rate"
          value={`${dashboardData?.recovery_rate || 0}%`}
          subtitle="Overall conversion efficiency"
          icon={TrendingUp}
          accentColor="indigo"
          trend="Calculated Rate"
          trendType="positive"
        />

        <StatCard
          title="Active Cases"
          value={`${dashboardData?.active_recovery_cases || 0} Cases`}
          subtitle="AI automated workflows"
          icon={RefreshCw}
          accentColor="cyan"
          trend={`${dashboardData?.active_recovery_cases || 0} Active`}
          trendType="neutral"
        />
      </div>

      {/* Phase 8A: Live Razorpay Test Mode Payment Card */}
      <LivePaymentTestCard onPaymentCreated={loadData} />

      {/* Live Payment Activity List */}
      <LivePaymentActivityList refreshTrigger={dashboardData} />

      {/* Revenue Visualization Section */}
      <PerformanceChart />

      {/* AI Recovery Insight Card */}
      <AIInsightCard
        insight={merchantAIInsight}
        onReviewCases={() => onNavigate('cases')}
      />

      {/* Main Content Grid: Recent Failed Payments & Live Activity Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Recent Failed Payments Table */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-base font-bold text-white">Recent Failed Payments</h3>
              <p className="text-xs text-slate-400">Click any record to inspect AI diagnostic breakdown</p>
            </div>

            <div className="flex items-center gap-3 w-full sm:w-auto">
              <div className="relative flex-1 sm:flex-none">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Filter table..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full sm:w-48 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-200 pl-8 pr-3 py-1.5 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={() => onNavigate('denials')}
              >
                View All
              </Button>
            </div>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider font-semibold">
                  <tr>
                    <th className="py-3.5 px-4">Payment ID</th>
                    <th className="py-3.5 px-4">Customer</th>
                    <th className="py-3.5 px-4">Amount</th>
                    <th className="py-3.5 px-4">Method</th>
                    <th className="py-3.5 px-4">Failure Reason</th>
                    <th className="py-3.5 px-4">Status</th>
                    <th className="py-3.5 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {filteredPayments.slice(0, 8).map((payment) => {
                    const statusVariant = {
                      RECOVERED: 'success',
                      IN_RECOVERY: 'brand',
                      ACTION_REQUIRED: 'warning'
                    }[payment.status] || 'default';

                    return (
                      <tr
                        key={payment.id}
                        onClick={() => handleOpenDrawer(payment)}
                        className="hover:bg-slate-800/50 cursor-pointer transition-colors duration-150 group"
                      >
                        <td className="py-3.5 px-4 font-mono font-semibold text-slate-200 group-hover:text-indigo-400">
                          {payment.id}
                        </td>
                        <td className="py-3.5 px-4 font-medium text-slate-200">{payment.customer}</td>
                        <td className="py-3.5 px-4 font-bold text-white">
                          ₹{payment.amount.toLocaleString('en-IN')}
                        </td>
                        <td className="py-3.5 px-4 text-slate-400">{payment.method}</td>
                        <td className="py-3.5 px-4 text-slate-300 max-w-xs truncate">
                          {payment.failureReason}
                        </td>
                        <td className="py-3.5 px-4">
                          <Badge variant={statusVariant} size="sm" dot>
                            {payment.status.replace('_', ' ')}
                          </Badge>
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <span className="inline-flex items-center text-xs font-semibold text-indigo-400 hover:text-indigo-300">
                            Inspect <ChevronRight className="w-3.5 h-3.5 ml-0.5" />
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Live Activity Stream */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-400 animate-pulse" />
              Live Activity Stream
            </h3>
            <span className="text-[10px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full font-semibold">
              Live Feed
            </span>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-xl">
            {merchantActivityFeed.map((item) => (
              <div key={item.id} className="flex items-start gap-3 pb-3 border-b border-slate-800/60 last:border-0 last:pb-0">
                <div
                  className={`p-2 rounded-xl border shrink-0 mt-0.5 ${
                    item.type === 'success'
                      ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                      : item.type === 'failure'
                      ? 'bg-rose-500/10 border-rose-500/20 text-rose-400'
                      : 'bg-indigo-500/10 border-indigo-500/20 text-indigo-400'
                  }`}
                >
                  {item.type === 'success' ? (
                    <CheckCircle2 className="w-3.5 h-3.5" />
                  ) : item.type === 'failure' ? (
                    <AlertCircle className="w-3.5 h-3.5" />
                  ) : (
                    <Zap className="w-3.5 h-3.5" />
                  )}
                </div>

                <div className="space-y-0.5 flex-1 min-w-0">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-200">{item.title}</span>
                    <span className="text-[10px] text-slate-500 font-mono">{item.time}</span>
                  </div>
                  <p className="text-xs text-slate-400 leading-snug truncate">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Payment Detail Drawer */}
      <PaymentDetailDrawer
        payment={selectedPayment}
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />
    </div>
  );
}
