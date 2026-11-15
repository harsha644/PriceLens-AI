import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';
import { formatINR } from '../utils/formatters';
import { ConnectorBadge } from '../components/ConnectorBadge';
import { DemoBadge } from '../components/DemoBadge';
import {
  Layers,
  TrendingDown,
  ExternalLink,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Truck,
  Star,
  Award,
  ArrowRight,
  TrendingUp,
} from 'lucide-react';

export const MarketplaceComparison = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { demoMode } = useAuth();
  const productId = searchParams.get('id');

  const [products, setProducts] = useState([]);
  const [selectedProductId, setSelectedProductId] = useState(productId || '');
  const [comparison, setComparison] = useState(null);
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
        .get(`/api/marketplaces/compare/${selectedProductId}/?include_demo=${demoMode}`)
        .then((res) => {
          setComparison(res.data);
        })
        .catch((err) => console.error('Failed to load comparison:', err))
        .finally(() => setLoading(false));
    }
  }, [selectedProductId, demoMode]);

  const handleProductChange = (e) => {
    const newId = e.target.value;
    setSelectedProductId(newId);
    setSearchParams({ id: newId });
  };

  const product = comparison?.product;
  const listings = comparison?.listings || [];
  const connectors = comparison?.connector_status || {};
  const summary = comparison?.summary || {};

  const amazonListing = listings.find((l) => l.marketplace_code === 'amazon_in');
  const flipkartListing = listings.find((l) => l.marketplace_code === 'flipkart');

  return (
    <div className="space-y-8">
      {/* Header and Product Picker */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Amazon India vs Flipkart Comparison</h1>
          <p className="text-sm text-slate-500 mt-1">Real-time side-by-side pricing, discounts, ratings, and connector transparency</p>
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

      {/* Connectors Banner */}
      <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-600">
          Marketplace Feed Status:
        </span>
        <div className="flex flex-wrap items-center gap-2">
          {Object.entries(connectors).map(([code, conn]) => (
            <ConnectorBadge key={code} marketplace={conn.name} status={conn.status} reason={conn.reason} />
          ))}
        </div>
      </div>

      {loading ? (
        <div className="h-96 rounded-2xl bg-white border border-slate-200 animate-pulse p-8" />
      ) : product ? (
        <div className="space-y-8">
          {/* Summary Metric Ribbon */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Lowest Price</span>
              <p className="text-2xl font-black text-emerald-600 mt-1">
                {summary.lowest_price ? formatINR(summary.lowest_price) : 'N/A'}
              </p>
              <p className="text-xs text-slate-500 mt-1">Across all confirmed listings</p>
            </div>

            <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Potential Savings</span>
              <p className="text-2xl font-black text-indigo-600 mt-1">
                {summary.max_savings ? formatINR(summary.max_savings) : '₹0'}
              </p>
              <p className="text-xs text-slate-500 mt-1">Spread between highest & lowest</p>
            </div>

            <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Best Pick</span>
              <p className="text-base font-extrabold text-slate-800 mt-1 truncate">
                {summary.best_deal ? summary.best_deal.marketplace_name : 'None'}
              </p>
              <p className="text-xs text-emerald-600 font-semibold mt-1">Optimal price & availability</p>
            </div>

            <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Catalog Mode</span>
              <div className="mt-1 flex items-center gap-2">
                {product.is_demo ? <DemoBadge size="md" /> : <span className="text-xs font-bold text-slate-700">Verified Live Data</span>}
              </div>
              <p className="text-xs text-slate-500 mt-1">Demo flags strictly separated</p>
            </div>
          </div>

          {/* Side-by-Side Comparison Columns */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Amazon India Card */}
            <div className="bg-white rounded-3xl border-2 border-amber-200 shadow-sm overflow-hidden flex flex-col justify-between">
              <div className="p-6 sm:p-8 space-y-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="px-3 py-1.5 rounded-xl bg-amber-500 text-white font-extrabold text-sm tracking-wide shadow-sm">
                      Amazon India
                    </div>
                    {amazonListing?.current_price === summary.lowest_price && (
                      <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                        <Award className="w-3.5 h-3.5" /> Best Price
                      </span>
                    )}
                  </div>
                  {amazonListing?.is_demo && <DemoBadge />}
                </div>

                {amazonListing ? (
                  <>
                    <div>
                      <h3 className="font-bold text-slate-900 text-lg leading-snug">{amazonListing.title}</h3>
                      <p className="text-xs text-slate-400 mt-1">Product ID: {amazonListing.marketplace_product_id}</p>
                    </div>

                    <div className="flex items-baseline gap-3">
                      <span className="text-3xl font-black text-slate-900">{formatINR(amazonListing.current_price)}</span>
                      {amazonListing.original_price && (
                        <span className="text-sm font-semibold text-slate-400 line-through">
                          {formatINR(amazonListing.original_price)}
                        </span>
                      )}
                      {amazonListing.discount_percent > 0 && (
                        <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-md">
                          {amazonListing.discount_percent}% OFF
                        </span>
                      )}
                    </div>

                    <div className="space-y-3 pt-4 border-t border-slate-100 text-sm">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-slate-500 font-medium">Customer Rating:</span>
                        <div className="flex items-center gap-1 font-bold text-slate-800">
                          <Star className="w-4 h-4 text-amber-500 fill-amber-500" />
                          <span>{amazonListing.rating}★</span>
                          <span className="text-xs text-slate-400 font-normal">({amazonListing.rating_count} ratings)</span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-xs text-slate-500 font-medium">Seller:</span>
                        <span className="font-semibold text-slate-800 text-xs">{amazonListing.seller_name || 'Amazon Cloudtail / Appario'}</span>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-xs text-slate-500 font-medium">Availability:</span>
                        <span className={`inline-flex items-center gap-1 text-xs font-bold ${amazonListing.is_available ? 'text-emerald-700' : 'text-rose-600'}`}>
                          {amazonListing.is_available ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
                          {amazonListing.is_available ? 'In Stock' : 'Currently Unavailable'}
                        </span>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-xs text-slate-500 font-medium">Delivery:</span>
                        <span className="text-xs font-semibold text-slate-700 flex items-center gap-1">
                          <Truck className="w-3.5 h-3.5 text-slate-400" /> {amazonListing.shipping_info || 'Free Prime Shipping'}
                        </span>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="p-8 text-center text-slate-400 space-y-2">
                    <p className="text-sm font-semibold">No active Amazon India listing found for this product.</p>
                    <p className="text-xs">Live connector requires active Amazon PA-API Associate credentials.</p>
                  </div>
                )}
              </div>

              {amazonListing && (
                <div className="p-6 bg-slate-50 border-t border-slate-100">
                  <a
                    href={amazonListing.product_url}
                    target="_blank"
                    rel="noreferrer"
                    className="w-full py-3 px-4 rounded-xl bg-amber-500 hover:bg-amber-600 font-bold text-white text-sm transition shadow flex items-center justify-center gap-2"
                  >
                    View on Amazon India <ExternalLink className="w-4 h-4" />
                  </a>
                </div>
              )}
            </div>

            {/* Flipkart Card */}
            <div className="bg-white rounded-3xl border-2 border-sky-200 shadow-sm overflow-hidden flex flex-col justify-between">
              <div className="p-6 sm:p-8 space-y-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="px-3 py-1.5 rounded-xl bg-blue-600 text-white font-extrabold text-sm tracking-wide shadow-sm">
                      Flipkart
                    </div>
                    {flipkartListing?.current_price === summary.lowest_price && (
                      <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                        <Award className="w-3.5 h-3.5" /> Best Price
                      </span>
                    )}
                  </div>
                  {flipkartListing?.is_demo && <DemoBadge />}
                </div>

                {flipkartListing ? (
                  <>
                    <div>
                      <h3 className="font-bold text-slate-900 text-lg leading-snug">{flipkartListing.title}</h3>
                      <p className="text-xs text-slate-400 mt-1">Product ID: {flipkartListing.marketplace_product_id}</p>
                    </div>

                    <div className="flex items-baseline gap-3">
                      <span className="text-3xl font-black text-slate-900">{formatINR(flipkartListing.current_price)}</span>
                      {flipkartListing.original_price && (
                        <span className="text-sm font-semibold text-slate-400 line-through">
                          {formatINR(flipkartListing.original_price)}
                        </span>
                      )}
                      {flipkartListing.discount_percent > 0 && (
                        <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-md">
                          {flipkartListing.discount_percent}% OFF
                        </span>
                      )}
                    </div>

                    <div className="space-y-3 pt-4 border-t border-slate-100 text-sm">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-slate-500 font-medium">Customer Rating:</span>
                        <div className="flex items-center gap-1 font-bold text-slate-800">
                          <Star className="w-4 h-4 text-blue-500 fill-blue-500" />
                          <span>{flipkartListing.rating}★</span>
                          <span className="text-xs text-slate-400 font-normal">({flipkartListing.rating_count} ratings)</span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-xs text-slate-500 font-medium">Seller:</span>
                        <span className="font-semibold text-slate-800 text-xs">{flipkartListing.seller_name || 'OmniTechRetail'}</span>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-xs text-slate-500 font-medium">Availability:</span>
                        <span className={`inline-flex items-center gap-1 text-xs font-bold ${flipkartListing.is_available ? 'text-emerald-700' : 'text-rose-600'}`}>
                          {flipkartListing.is_available ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
                          {flipkartListing.is_available ? 'In Stock' : 'Currently Unavailable'}
                        </span>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-xs text-slate-500 font-medium">Delivery:</span>
                        <span className="text-xs font-semibold text-slate-700 flex items-center gap-1">
                          <Truck className="w-3.5 h-3.5 text-slate-400" /> {flipkartListing.shipping_info || 'Free Express Delivery'}
                        </span>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="p-8 text-center text-slate-400 space-y-2">
                    <p className="text-sm font-semibold">No active Flipkart listing found for this product.</p>
                    <p className="text-xs">Live connector requires active Flipkart Affiliate API credentials.</p>
                  </div>
                )}
              </div>

              {flipkartListing && (
                <div className="p-6 bg-slate-50 border-t border-slate-100">
                  <a
                    href={flipkartListing.product_url}
                    target="_blank"
                    rel="noreferrer"
                    className="w-full py-3 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 font-bold text-white text-sm transition shadow flex items-center justify-center gap-2"
                  >
                    View on Flipkart <ExternalLink className="w-4 h-4" />
                  </a>
                </div>
              )}
            </div>
          </div>

          {/* Quick jump actions */}
          <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
            <Link
              to={`/reviews?id=${product.id}`}
              className="px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm shadow transition flex items-center gap-2"
            >
              Analyze Customer Reviews <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to={`/history?id=${product.id}`}
              className="px-6 py-3 rounded-xl bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 font-bold text-sm transition flex items-center gap-2"
            >
              View 30-Day Price Fluctuations <TrendingDown className="w-4 h-4" />
            </Link>
          </div>
        </div>
      ) : (
        <div className="p-12 bg-white rounded-2xl border border-slate-200 text-center text-slate-500">
          No product selected. Please select a product above.
        </div>
      )}
    </div>
  );
};
