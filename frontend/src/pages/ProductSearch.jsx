import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';
import { DemoBadge } from '../components/DemoBadge';
import {
  Search,
  Filter,
  Layers,
  MessageSquareText,
  TrendingDown,
  Camera,
  Package,
} from 'lucide-react';

export const ProductSearch = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { demoMode } = useAuth();

  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [category, setCategory] = useState(searchParams.get('category') || '');
  const [brand, setBrand] = useState(searchParams.get('brand') || '');
  const [categories, setCategories] = useState([]);
  const [brands, setBrands] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Load category and brand filters
    api.get('/api/catalog/categories/').then((res) => {
      setCategories(res.data.categories || []);
      setBrands(res.data.brands || []);
    }).catch(() => {});
  }, []);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const q = searchParams.get('q') || '';
      const cat = searchParams.get('category') || '';
      const br = searchParams.get('brand') || '';

      const res = await api.get(
        `/api/catalog/?q=${encodeURIComponent(q)}&category=${encodeURIComponent(cat)}&brand=${encodeURIComponent(br)}&include_demo=${demoMode}`
      );
      setProducts(res.data || []);
    } catch (err) {
      console.error('Error fetching products:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, [searchParams, demoMode]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    const params = {};
    if (query.trim()) params.q = query.trim();
    if (category) params.category = category;
    if (brand) params.brand = brand;
    setSearchParams(params);
  };

  const handleReset = () => {
    setQuery('');
    setCategory('');
    setBrand('');
    setSearchParams({});
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Product Search & Catalog</h1>
        <p className="text-sm text-slate-500 mt-1">Browse, filter, and compare smartphone, laptop, and electronics listings</p>
      </div>

      {/* Filter / Search Bar */}
      <form onSubmit={handleSearchSubmit} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-5 h-5 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by product name, model number, brand, variant..."
              className="w-full pl-11 pr-4 py-2.5 rounded-xl border border-slate-200 focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 outline-none text-sm"
            />
          </div>

          <div className="flex gap-2">
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="px-3 py-2.5 rounded-xl border border-slate-200 bg-white text-sm text-slate-700 outline-none focus:border-sky-500"
            >
              <option value="">All Categories</option>
              {categories.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>

            <select
              value={brand}
              onChange={(e) => setBrand(e.target.value)}
              className="px-3 py-2.5 rounded-xl border border-slate-200 bg-white text-sm text-slate-700 outline-none focus:border-sky-500"
            >
              <option value="">All Brands</option>
              {brands.map((b) => (
                <option key={b} value={b}>{b}</option>
              ))}
            </select>

            <button
              type="submit"
              className="px-5 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-bold text-sm shadow-sm transition"
            >
              Filter
            </button>
            {(query || category || brand) && (
              <button
                type="button"
                onClick={handleReset}
                className="px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 text-sm font-semibold transition"
              >
                Reset
              </button>
            )}
          </div>
        </div>
      </form>

      {/* Results Header */}
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
          Found {products.length} Products
        </span>
        {demoMode && (
          <span className="text-xs text-purple-600 font-semibold bg-purple-50 px-2.5 py-1 rounded-full border border-purple-200">
            Including Demo Catalog Items
          </span>
        )}
      </div>

      {/* Product Grid */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-64 rounded-2xl bg-white border border-slate-200 animate-pulse p-6" />
          ))}
        </div>
      ) : products.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {products.map((p) => (
            <div
              key={p.id}
              className="bg-white rounded-2xl border border-slate-200 p-6 flex flex-col justify-between hover:shadow-lg hover:border-sky-400 transition"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-bold uppercase tracking-wider text-sky-700 bg-sky-50 px-2.5 py-1 rounded-md">
                    {p.brand}
                  </span>
                  {p.is_demo && <DemoBadge />}
                </div>

                <h3 className="font-bold text-slate-900 text-base mb-1 line-clamp-2">{p.name}</h3>

                <div className="space-y-1.5 my-3 text-xs text-slate-600 bg-slate-50 p-3 rounded-xl border border-slate-100">
                  <p><span className="font-semibold text-slate-500">Model:</span> {p.model || 'Standard'} {p.model_number ? `(${p.model_number})` : ''}</p>
                  <p><span className="font-semibold text-slate-500">Variant:</span> {[p.variant, p.ram, p.storage, p.colour].filter(Boolean).join(' · ') || 'Default'}</p>
                  <p><span className="font-semibold text-slate-500">Category:</span> {p.category}</p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-4 border-t border-slate-100 grid grid-cols-2 gap-2">
                <Link
                  to={`/compare?id=${p.id}`}
                  className="py-2 px-3 rounded-xl bg-sky-50 hover:bg-sky-100 text-sky-700 font-bold text-xs flex items-center justify-center gap-1.5 transition"
                >
                  <Layers className="w-3.5 h-3.5" /> Compare
                </Link>
                <Link
                  to={`/reviews?id=${p.id}`}
                  className="py-2 px-3 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold text-xs flex items-center justify-center gap-1.5 transition"
                >
                  <MessageSquareText className="w-3.5 h-3.5" /> Reviews
                </Link>
                <Link
                  to={`/history?id=${p.id}`}
                  className="py-2 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs flex items-center justify-center gap-1.5 transition"
                >
                  <TrendingDown className="w-3.5 h-3.5" /> History
                </Link>
                <Link
                  to={`/upload?id=${p.id}`}
                  className="py-2 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs flex items-center justify-center gap-1.5 transition"
                >
                  <Camera className="w-3.5 h-3.5" /> Add Image
                </Link>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-500 space-y-3">
          <Package className="w-10 h-10 text-slate-300 mx-auto" />
          <h4 className="font-bold text-slate-700">No products match your criteria</h4>
          <p className="text-xs max-w-sm mx-auto">
            Try adjusting your search query, clearing category/brand filters, or toggling "Demo Data" on the top right.
          </p>
        </div>
      )}
    </div>
  );
};
