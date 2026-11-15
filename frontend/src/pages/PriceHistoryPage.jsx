import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';
import { formatINR, formatDate } from '../utils/formatters';
import { DemoBadge } from '../components/DemoBadge';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts';
import {
  TrendingDown,
  TrendingUp,
  Calendar,
  Layers,
  ArrowDownRight,
  ArrowUpRight,
} from 'lucide-react';

export const PriceHistoryPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { demoMode } = useAuth();
  const productId = searchParams.get('id');

  const [products, setProducts] = useState([]);
  const [selectedProductId, setSelectedProductId] = useState(productId || '');
  const [historyData, setHistoryData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get(`/api/catalog/?include_demo=${demoMode}`).then((res) => {
      setProducts(res.data || []);
      if (!selectedProductId && res.data?.length > 0) {
        setSelectedProductId(productId || res.data[0].id);
      }
    }).catch(() => {});
  }, [demoMode, productId]);

  useEffect(() => {
    if (selectedProductId) {
      setLoading(true);
      api
        .get(`/api/marketplaces/price-history/${selectedProductId}/?include_demo=${demoMode}`)
        .then((res) => setHistoryData(res.data))
        .catch((err) => console.error('Error fetching price history:', err))
        .finally(() => setLoading(false));
    }
  }, [selectedProductId, demoMode]);

  const handleProductChange = (e) => {
    const newId = e.target.value;
    setSelectedProductId(newId);
    setSearchParams({ id: newId });
  };

  const stats = historyData?.stats || {};
  const series = historyData?.series || [];

  // Group by date for multi-line chart (Amazon vs Flipkart)
  const chartMap = {};
  series.forEach((pt) => {
    if (!chartMap[pt.date]) {
      chartMap[pt.date] = { date: pt.date };
    }
    if (pt.code === 'amazon_in') {
      chartMap[pt.date].Amazon = pt.price;
    } else if (pt.code === 'flipkart') {
      chartMap[pt.date].Flipkart = pt.price;
    }
  });
  const chartData = Object.values(chartMap).sort((a, b) => new Date(a.date) - new Date(b.date));

  return (
    <div className="space-y-8">
      {/* Title & Product Picker */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Historical Price Tracking</h1>
          <p className="text-sm text-slate-500 mt-1">
            Amazon India vs Flipkart price movement timeline and fluctuation benchmarks
          </p>
        </div>

        <div className="w-full md:w-auto flex items-center gap-3">
          <label className="text-xs font-bold text-slate-500 uppercase whitespace-nowrap">Product:</label>
          <select
            value={selectedProductId}
            onChange={handleProductChange}
            className="w-full md:w-72 px-3 py-2.5 rounded-xl border border-slate-200 bg-white text-sm font-semibold text-slate-800 outline-none focus:border-sky-500"
          >
            {products.map((p) => (
              <option key={p.id} value={p.id}>
                {p.brand} {p.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="h-96 rounded-3xl bg-white border border-slate-200 animate-pulse p-8" />
      ) : historyData ? (
        <div className="space-y-8">
          {/* Stat Metrics Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Current Price</span>
              <p className="text-2xl font-black text-slate-900 mt-1">
                {stats.current_price ? formatINR(stats.current_price) : 'N/A'}
              </p>
              <p className="text-xs text-slate-500 mt-1">Latest registered price</p>
            </div>

            <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Lowest Recorded</span>
                <ArrowDownRight className="w-4 h-4 text-emerald-600" />
              </div>
              <p className="text-2xl font-black text-emerald-600 mt-1">
                {stats.lowest_price ? formatINR(stats.lowest_price) : 'N/A'}
              </p>
              <p className="text-xs text-slate-500 mt-1">All-time record low</p>
            </div>

            <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Highest Recorded</span>
                <ArrowUpRight className="w-4 h-4 text-rose-600" />
              </div>
              <p className="text-2xl font-black text-slate-700 mt-1">
                {stats.highest_price ? formatINR(stats.highest_price) : 'N/A'}
              </p>
              <p className="text-xs text-slate-500 mt-1">Peak retail pricing</p>
            </div>

            <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Data Points</span>
              <p className="text-2xl font-black text-indigo-600 mt-1">{stats.total_data_points || 0}</p>
              <p className="text-xs text-slate-500 mt-1">Historical audits recorded</p>
            </div>
          </div>

          {/* Interactive Chart */}
          <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-slate-900 text-sm">30-Day Marketplace Price Trajectory</h3>
              <div className="flex items-center gap-4 text-xs font-bold">
                <span className="flex items-center gap-1.5 text-amber-600">
                  <span className="w-3 h-3 rounded-full bg-amber-500 inline-block" /> Amazon India
                </span>
                <span className="flex items-center gap-1.5 text-blue-600">
                  <span className="w-3 h-3 rounded-full bg-blue-600 inline-block" /> Flipkart
                </span>
              </div>
            </div>

            <div className="h-80 w-full pt-4">
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData} margin={{ top: 10, right: 30, left: 20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                    <XAxis dataKey="date" stroke="#94A3B8" fontSize={11} />
                    <YAxis
                      stroke="#94A3B8"
                      fontSize={11}
                      domain={['auto', 'auto']}
                      tickFormatter={(val) => `₹${(val / 1000).toFixed(0)}k`}
                    />
                    <Tooltip
                      formatter={(val) => [formatINR(val), 'Price']}
                      labelFormatter={(lbl) => `Date: ${lbl}`}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="Amazon"
                      stroke="#F59E0B"
                      strokeWidth={3}
                      dot={{ r: 4 }}
                      activeDot={{ r: 7 }}
                      connectNulls
                    />
                    <Line
                      type="monotone"
                      dataKey="Flipkart"
                      stroke="#2563EB"
                      strokeWidth={3}
                      dot={{ r: 4 }}
                      activeDot={{ r: 7 }}
                      connectNulls
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-slate-400 text-sm">
                  No price history points recorded for this product yet.
                </div>
              )}
            </div>
          </div>

          {/* Historical Log Stream */}
          <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
            <h3 className="font-bold text-slate-900 text-sm">Detailed Price History Audit Trail</h3>
            <div className="divide-y divide-slate-100 max-h-72 overflow-y-auto">
              {series.map((item, idx) => (
                <div key={idx} className="py-3 flex items-center justify-between text-sm">
                  <div className="flex items-center gap-3">
                    <Calendar className="w-4 h-4 text-slate-400" />
                    <div>
                      <span className="font-semibold text-slate-800">{item.date}</span>
                      <span className="text-xs text-slate-400 block">{item.marketplace}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="font-extrabold text-slate-900">{formatINR(item.price)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};
