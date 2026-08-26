import React, { useState, useEffect } from 'react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { timeframePerformanceData } from '../../data/merchantData';
import { Card } from '../../shared/components/Card';
import { getMerchantAnalytics } from '../../api/merchantApi';
import { CURRENT_MERCHANT_ID } from '../../config/currentMerchant';

export default function PerformanceChart() {
  const [timeframe, setTimeframe] = useState('7D');
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadAnalytics() {
      try {
        const res = await getMerchantAnalytics(CURRENT_MERCHANT_ID);
        const paymentTrendMap = {};
        (res?.payment_trend || []).forEach((pt) => {
          paymentTrendMap[pt.date] = pt.total_volume;
        });

        const merged = (res?.recovery_trend || []).map((rt) => {
          const totalVol = paymentTrendMap[rt.date] || 0;
          const recovered = rt.recovered_volume || 0;
          return {
            date: rt.date,
            recovered: recovered,
            atRisk: Math.max(0, roundTwo(totalVol - recovered))
          };
        });

        if (merged && merged.length > 0) {
          setChartData(merged);
        } else {
          setChartData(timeframePerformanceData[timeframe] || []);
        }
      } catch (err) {
        console.error('Failed to load performance chart analytics:', err);
        setChartData(timeframePerformanceData[timeframe] || []);
      } finally {
        setLoading(false);
      }
    }
    loadAnalytics();
  }, [timeframe]);

  function roundTwo(num) {
    return Math.round((num + Number.EPSILON) * 100) / 100;
  }

  const timeframes = ['7D', '30D', '3M', '6M'];

  const formatCurrency = (val) => {
    if (val >= 100000) return `₹${(val / 100000).toFixed(1)}L`;
    if (val >= 1000) return `₹${(val / 1000).toFixed(0)}k`;
    return `₹${val}`;
  };

  const dataToDisplay = chartData.length > 0 ? chartData : (timeframePerformanceData[timeframe] || []);

  return (
    <Card
      header={
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 w-full">
          <div>
            <h3 className="text-base font-bold text-white">Revenue At Risk vs. Recovered</h3>
            <p className="text-xs text-slate-400">Interactive financial recovery visualization across dataset timelines</p>
          </div>
          <div className="flex items-center bg-slate-950 p-1 rounded-xl border border-slate-800">
            {timeframes.map((tf) => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                  timeframe === tf
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>
      }
      hover={false}
    >
      <div className="h-72 w-full pt-4">
        {loading ? (
          <div className="h-full w-full bg-slate-950/40 rounded-xl animate-pulse flex items-center justify-center text-xs text-slate-500">
            Loading chart data...
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={dataToDisplay} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorRecovered" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="colorAtRisk" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#f43f5e" stopOpacity={0.0} />
                </linearGradient>
              </defs>

              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
              <YAxis stroke="#64748b" fontSize={11} tickLine={false} tickFormatter={formatCurrency} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#334155',
                  borderRadius: '12px',
                  color: '#fff',
                  fontSize: '12px'
                }}
                formatter={(val) => [`₹${Number(val).toLocaleString('en-IN')}`, '']}
              />
              <Area
                type="monotone"
                dataKey="recovered"
                name="Recovered Revenue"
                stroke="#10b981"
                strokeWidth={3}
                fillOpacity={1}
                fill="url(#colorRecovered)"
              />
              <Area
                type="monotone"
                dataKey="atRisk"
                name="Revenue At Risk"
                stroke="#f43f5e"
                strokeWidth={2}
                strokeDasharray="4 4"
                fillOpacity={1}
                fill="url(#colorAtRisk)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="flex items-center justify-center gap-6 mt-4 pt-3 border-t border-slate-800/80 text-xs">
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-emerald-500" />
          <span className="text-slate-300 font-medium">Recovered Revenue</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-rose-500" />
          <span className="text-slate-300 font-medium">Revenue At Risk</span>
        </div>
      </div>
    </Card>
  );
}
