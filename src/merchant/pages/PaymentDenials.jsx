import React, { useState, useEffect } from 'react';
import { Search, Filter, RefreshCw, ChevronRight, SlidersHorizontal, ArrowUpDown, AlertTriangle, CreditCard } from 'lucide-react';
import Badge from '../../shared/components/Badge';
import Button from '../../shared/components/Button';
import { Card } from '../../shared/components/Card';
import PaymentDetailDrawer from '../components/PaymentDetailDrawer';
import RazorpayTestModal from '../components/RazorpayTestModal';
import { EmptyState } from '../../shared/components/EmptyState';
import { getFailedPayments } from '../../api/merchantApi';
import { CURRENT_MERCHANT_ID } from '../../config/currentMerchant';

export default function PaymentDenials() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('ALL');
  const [selectedMethod, setSelectedMethod] = useState('ALL');
  const [selectedPayment, setSelectedPayment] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [razorpayModalOpen, setRazorpayModalOpen] = useState(false);

  const [failedPayments, setFailedPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getFailedPayments(CURRENT_MERCHANT_ID);
      const mapped = (data || []).map((p) => ({
        id: p.payment_id,
        merchant_id: p.merchant_id || CURRENT_MERCHANT_ID,
        customer: `Customer (${p.payment_id.slice(-4)})`,
        email: `user_${p.payment_id.slice(-4)}@example.com`,
        amount: p.amount_inr,
        method: p.payment_method,
        gateway: p.gateway,
        failureReason: p.failure_category,
        errorCode: p.error_code,
        attempts: 1,
        status: p.retryable ? 'IN_RECOVERY' : 'ACTION_REQUIRED',
        aiRecommendation: p.retryable ? 'Automated Smart Gateway Retry' : 'Bank Verification / Alternate Method',
        aiConfidence: p.retryable ? 85 : 45,
        created_at: p.created_at,
        bank: p.gateway
      }));
      setFailedPayments(mapped);
    } catch (err) {
      console.error('Failed to fetch merchant failed payments:', err);
      setError(err.message || 'Failed to fetch failed payments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const filtered = failedPayments.filter((p) => {
    const matchesSearch =
      p.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.customer.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.failureReason.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = selectedStatus === 'ALL' || p.status === selectedStatus;
    const matchesMethod = selectedMethod === 'ALL' || p.method.includes(selectedMethod);

    return matchesSearch && matchesStatus && matchesMethod;
  });

  const handleRowClick = (payment) => {
    setSelectedPayment(payment);
    setDrawerOpen(true);
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-fadeIn p-4">
        <div className="h-16 bg-slate-900/80 border border-slate-800 rounded-2xl animate-pulse" />
        <div className="h-14 bg-slate-900/80 border border-slate-800 rounded-2xl animate-pulse" />
        <div className="h-96 bg-slate-900/80 border border-slate-800 rounded-2xl animate-pulse" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-rose-950/40 border border-rose-500/30 p-6 rounded-2xl space-y-4 animate-fadeIn">
        <div className="flex items-center gap-3 text-rose-400 font-bold">
          <AlertTriangle className="w-5 h-5" />
          <span>Failed to load failed payment records</span>
        </div>
        <p className="text-xs text-slate-300">{error}</p>
        <Button variant="outline" size="sm" onClick={loadData}>
          Retry Connection
        </Button>
      </div>
    );
  }

  const totalFailedCount = failedPayments.length;
  const totalAmountLakhs = (failedPayments.reduce((sum, item) => sum + item.amount, 0) / 100000).toFixed(1);

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white">Payment Denials & Failed Transactions</h2>
          <p className="text-xs text-slate-400">Search, analyze root causes, and trigger AI automated recovery workflows.</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <Button
            variant="primary"
            size="sm"
            icon={CreditCard}
            onClick={() => setRazorpayModalOpen(true)}
          >
            Test Razorpay Payment
          </Button>
          <Badge variant="brand" size="md">
            {totalFailedCount} Failed Records
          </Badge>
          <Badge variant="warning" size="md">
            ₹{totalAmountLakhs}L At Risk
          </Badge>
        </div>
      </div>

      {/* Control Bar: Search & Filters */}
      <Card padding="sm" hover={false}>
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
          {/* Search Box */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by Payment ID, Customer name, Email, or Reason..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 placeholder-slate-500 pl-10 pr-4 py-2.5 focus:outline-none focus:border-indigo-500 transition-colors"
            />
          </div>

          {/* Filter Dropdowns */}
          <div className="flex items-center gap-3 overflow-x-auto pb-1 md:pb-0">
            {/* Status Filter */}
            <div className="flex items-center gap-1.5 bg-slate-950 px-3 py-1.5 rounded-xl border border-slate-800 text-xs">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-slate-400">Status:</span>
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="bg-transparent text-white font-semibold focus:outline-none cursor-pointer"
              >
                <option value="ALL">All Statuses</option>
                <option value="IN_RECOVERY">In Recovery</option>
                <option value="ACTION_REQUIRED">Action Required</option>
              </select>
            </div>

            {/* Method Filter */}
            <div className="flex items-center gap-1.5 bg-slate-950 px-3 py-1.5 rounded-xl border border-slate-800 text-xs">
              <span className="text-slate-400">Method:</span>
              <select
                value={selectedMethod}
                onChange={(e) => setSelectedMethod(e.target.value)}
                className="bg-transparent text-white font-semibold focus:outline-none cursor-pointer"
              >
                <option value="ALL">All Methods</option>
                <option value="Card">Cards</option>
                <option value="UPI">UPI</option>
                <option value="NetBanking">NetBanking</option>
                <option value="Wallet">Wallet</option>
              </select>
            </div>
          </div>
        </div>
      </Card>

      {/* Main Table */}
      {filtered.length === 0 ? (
        <EmptyState
          title="No Failed Payments Found"
          description="No transaction records match your current search or filter options."
          action={
            <Button variant="outline" size="sm" onClick={() => { setSearchTerm(''); setSelectedStatus('ALL'); setSelectedMethod('ALL'); }}>
              Reset Filters
            </Button>
          }
        />
      ) : (
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider font-semibold">
                <tr>
                  <th className="py-4 px-4">Payment ID</th>
                  <th className="py-4 px-4">Customer</th>
                  <th className="py-4 px-4">Amount</th>
                  <th className="py-4 px-4">Method & Gateway</th>
                  <th className="py-4 px-4">Failure Reason</th>
                  <th className="py-4 px-4">Attempts</th>
                  <th className="py-4 px-4">Status</th>
                  <th className="py-4 px-4 text-right">AI Recommendation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {filtered.map((payment) => {
                  const statusVariant = {
                    RECOVERED: 'success',
                    IN_RECOVERY: 'brand',
                    ACTION_REQUIRED: 'warning'
                  }[payment.status] || 'default';

                  return (
                    <tr
                      key={payment.id}
                      onClick={() => handleRowClick(payment)}
                      className="hover:bg-slate-800/50 cursor-pointer transition-colors duration-150 group"
                    >
                      <td className="py-4 px-4 font-mono font-bold text-slate-100 group-hover:text-indigo-400">
                        {payment.id}
                      </td>
                      <td className="py-4 px-4">
                        <div className="font-semibold text-slate-200">{payment.customer}</div>
                        <div className="text-[10px] text-slate-400">{payment.email}</div>
                      </td>
                      <td className="py-4 px-4 font-extrabold text-white text-sm">
                        ₹{(payment.amount ?? 0).toLocaleString('en-IN')}
                      </td>
                      <td className="py-4 px-4">
                        <div className="font-medium text-slate-200">{payment.method}</div>
                        <div className="text-[10px] text-slate-400">{payment.gateway}</div>
                      </td>
                      <td className="py-4 px-4 max-w-xs">
                        <div className="text-rose-400 font-medium truncate">{payment.failureReason}</div>
                        <div className="text-[10px] text-slate-500 font-mono">{payment.errorCode}</div>
                      </td>
                      <td className="py-4 px-4 font-mono text-center">{payment.attempts}</td>
                      <td className="py-4 px-4">
                        <Badge variant={statusVariant} size="sm" dot>
                          {payment.status.replace('_', ' ')}
                        </Badge>
                      </td>
                      <td className="py-4 px-4 text-right">
                        <div className="text-indigo-300 font-medium truncate max-w-xs ml-auto">
                          {payment.aiRecommendation}
                        </div>
                        <div className="text-[10px] text-emerald-400 font-bold">
                          {payment.aiConfidence}% AI Confidence
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Detail Drawer */}
      <PaymentDetailDrawer
        payment={selectedPayment}
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />

      {/* Razorpay Test Modal */}
      <RazorpayTestModal
        isOpen={razorpayModalOpen}
        onClose={() => setRazorpayModalOpen(false)}
        merchantId={CURRENT_MERCHANT_ID}
        onInspectPayment={(pmId) => {
          setSelectedPayment({
            id: pmId,
            merchant_id: CURRENT_MERCHANT_ID,
            customer: 'Test User',
            amount: 500,
            method: 'Card',
            gateway: 'Razorpay Test Gateway',
            failureReason: 'User Abandoned',
            errorCode: 'BAD_REQUEST_ABANDONED',
            bank: 'Razorpay System',
            attempts: 1,
            status: 'ACTION_REQUIRED'
          });
          setDrawerOpen(true);
        }}
      />
    </div>
  );
}
