import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';
import { formatINR } from '../utils/formatters';
import { ConnectorBadge } from '../components/ConnectorBadge';
import { DemoBadge } from '../components/DemoBadge';
import {
  Search,
  TrendingDown,
  Layers,
  Sparkles,
  MessageSquareText,
  Camera,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react';

export const Dashboard = () => {
  const { user, demoMode } = useAuth();
  const navigate = useNavigate();

  const [searchQuery, setSearchQuery] = useState('');
  const [connectors, setConnectors] = useState({});
  const [topRecommendations, setTopRecommendations] = useState([]);
  const [recentProducts, setRecentProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDashboardData = async () => {
      setLoading(true);
      try {
        const [connRes, recRes, prodRes] = await Promise.all([
          api.get('/api/marketplaces/status/').catch(() => ({ data: {} })),
          api.get(`/api/recommendations/top/?include_demo=${demoMode}`).catch(() => ({ data: [] })),
          api.get(`/api/catalog/?include_demo=${demoMode}`).catch(() => ({ data: [] })),
        ]);
        setConnectors(connRes.data);
        setTopRecommendations(recRes.data || []);
        setRecentProducts(prodRes.data?.slice(0, 4) || []);
      } catch (err) {
        console.error('Failed to load dashboard:', err);
      } finally {
        setLoading(false);
      }
    };
    loadDashboardData();
  }, [demoMode]);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/products?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  return (
    <div className="space-y-8">
      {/* Welcome & Quick Search Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-sky-900 via-indigo-900 to-slate-900 text-white p-8 sm:p-10 shadow-xl shadow-sky-950/10">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 text-sky-300 text-xs font-semibold uppercase tracking-wider mb-4 border border-white/10">
            <Sparkles className="w-3.5 h-3.5" /> Welcome back, {user?.full_name?.split(' ')[0] || user?.username}
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
            Find, Compare & Analyze Any Product
          </h1>
          <p className="mt-2 text-slate-300 text-sm sm:text-base leading-relaxed">
            Real-time price comparisons for Amazon India and Flipkart, NLP review sentiment audits, and automated buy ratings.
          </p>

          <form onSubmit={handleSearch} className="mt-6 flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search Samsung, iPhone 15, Sony WH-1000XM5..."
                className="w-full pl-12 pr-4 py-3.5 rounded-2xl bg-white text-slate-800 placeholder-slate-400 text-sm font-medium focus:ring-4 focus:ring-sky-500/30 outline-none transition shadow-lg"
              />
            </div>
            <button
              type="submit"
              className="px-6 py-3.5 rounded-2xl bg-sky-500 hover:bg-sky-400 font-bold text-white text-sm transition shadow-lg shadow-sky-500/30 flex items-center gap-2 flex-shrink-0"
            >
              Search
            </button>
          </form>
        </div>
      </div>

      {/* Connector Health Status Strip */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-sky-600" /> Marketplace Connector Status
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Strictly using official affiliate APIs. Unconfigured connectors return transparent status instead of invented data.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {Object.keys(connectors).length > 0 ? (
              Object.entries(connectors).map(([code, conn]) => (
                <ConnectorBadge
                  key={code}
                  marketplace={conn.name}
                  status={conn.status}
                  reason={conn.reason}
                />
              ))
            ) : (
              <>
                <ConnectorBadge marketplace="Amazon India" status="unavailable" reason="Credentials not configured" />
                <ConnectorBadge marketplace="Flipkart" status="unavailable" reason="Credentials not configured" />
              </>
            )}
          </div>
        </div>
      </div>

      {/* Quick Action Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Link
          to="/products"
          className="p-5 rounded-2xl bg-white border border-slate-200 hover:border-sky-500/40 hover:shadow-md transition group"
        >
          <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center mb-3 group-hover:scale-105 transition">
            <Search className="w-5 h-5" />
          </div>
          <h4 className="font-bold text-slate-900 text-sm">Product Search</h4>
          <p className="text-xs text-slate-500 mt-1">Browse catalog, filter specs & compare models</p>
        </Link>

        <Link
          to="/upload"
          className="p-5 rounded-2xl bg-white border border-slate-200 hover:border-indigo-500/40 hover:shadow-md transition group"
        >
          <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-3 group-hover:scale-105 transition">
            <Camera className="w-5 h-5" />
          </div>
          <h4 className="font-bold text-slate-900 text-sm">Image Upload & Match</h4>
          <p className="text-xs text-slate-500 mt-1">RapidFuzz spec matching & manual confirmation</p>
        </Link>

        <Link
          to="/compare"
          className="p-5 rounded-2xl bg-white border border-slate-200 hover:border-amber-500/40 hover:shadow-md transition group"
        >
          <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center mb-3 group-hover:scale-105 transition">
            <Layers className="w-5 h-5" />
          </div>
          <h4 className="font-bold text-slate-900 text-sm">Marketplace Comparison</h4>
          <p className="text-xs text-slate-500 mt-1">Side-by-side pricing, discounts & sellers</p>
        </Link>

        <Link
          to="/reviews"
          className="p-5 rounded-2xl bg-white border border-slate-200 hover:border-emerald-500/40 hover:shadow-md transition group"
        >
          <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-3 group-hover:scale-105 transition">
            <MessageSquareText className="w-5 h-5" />
          </div>
          <h4 className="font-bold text-slate-900 text-sm">Review Analysis</h4>
          <p className="text-xs text-slate-500 mt-1">VADER & TextBlob NLP sentiment audit</p>
        </Link>
      </div>

      {/* Top Recommendations Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-indigo-600" /> Top Ranked Product Deals
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">Calculated using multi-factor normalized scoring</p>
          </div>
          <Link to="/recommendations" className="text-xs font-bold text-sky-600 hover:text-sky-500 flex items-center gap-1">
            View All <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[1, 2].map((i) => (
              <div key={i} className="h-44 rounded-2xl bg-white border border-slate-200 animate-pulse p-6" />
            ))}
          </div>
        ) : topRecommendations.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {topRecommendations.slice(0, 4).map((rec) => (
              <div
                key={rec.product_id}
                className="bg-white rounded-2xl border border-slate-200 p-6 hover:shadow-lg hover:border-indigo-300 transition flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-lg">
                      Deal Score: {rec.score}/100
                    </span>
                    <span className="text-xs font-bold text-slate-700 bg-slate-100 px-2.5 py-1 rounded-lg">
                      {rec.marketplace}
                    </span>
                  </div>
                  <h3 className="font-bold text-slate-900 text-base mb-1">{rec.product_name}</h3>
                  <p className="text-xl font-extrabold text-emerald-600 mb-3">{formatINR(rec.price)}</p>
                  <p className="text-xs text-slate-600 leading-relaxed bg-slate-50 p-3 rounded-xl border border-slate-100">
                    {rec.explanation}
                  </p>
                </div>

                <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between">
                  <Link
                    to={`/compare?id=${rec.product_id}`}
                    className="text-xs font-bold text-sky-600 hover:text-sky-700 flex items-center gap-1"
                  >
                    Compare Pricing <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                  <Link
                    to={`/reviews?id=${rec.product_id}`}
                    className="text-xs font-bold text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
                  >
                    Audit Reviews <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center text-slate-500">
            <p className="text-sm">No recommendations available yet. Toggle "Demo Data" on top to view sample seeded products.</p>
          </div>
        )}
      </div>

      {/* Catalog Preview */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-900">Featured Catalog Items</h2>
          <Link to="/products" className="text-xs font-bold text-sky-600 hover:text-sky-500 flex items-center gap-1">
            Browse All <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {recentProducts.map((p) => (
            <div key={p.id} className="bg-white rounded-2xl border border-slate-200 p-5 flex flex-col justify-between hover:shadow-md transition">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-bold text-slate-500 uppercase">{p.brand}</span>
                  {p.is_demo && <DemoBadge />}
                </div>
                <h4 className="font-bold text-slate-900 text-sm mb-1 line-clamp-1">{p.name}</h4>
                <p className="text-xs text-slate-500 mb-3">
                  {[p.variant, p.ram, p.storage, p.colour].filter(Boolean).join(' · ') || p.category}
                </p>
              </div>
              <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                <Link
                  to={`/compare?id=${p.id}`}
                  className="text-xs font-bold text-sky-600 hover:underline"
                >
                  Compare
                </Link>
                <Link
                  to={`/history?id=${p.id}`}
                  className="text-xs font-bold text-indigo-600 hover:underline"
                >
                  Price Chart
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
