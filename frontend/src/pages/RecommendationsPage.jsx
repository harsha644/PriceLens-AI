import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';
import { formatINR } from '../utils/formatters';
import { DemoBadge } from '../components/DemoBadge';
import {
  Sparkles,
  Award,
  Layers,
  MessageSquareText,
  TrendingDown,
  ArrowRight,
  Sliders,
  CheckCircle,
} from 'lucide-react';

export const RecommendationsPage = () => {
  const { demoMode } = useAuth();
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get(`/api/recommendations/top/?include_demo=${demoMode}`)
      .then((res) => {
        setRecommendations(res.data || []);
      })
      .catch((err) => console.error('Failed to load recommendations:', err))
      .finally(() => setLoading(false));
  }, [demoMode]);

  return (
    <div className="space-y-8">
      {/* Title & Engine Explanation */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">AI-Powered Product Recommendations</h1>
          <p className="text-sm text-slate-500 mt-1">
            Data-backed ranking synthesizing price competitiveness, discounts, verified ratings, and NLP review sentiment.
          </p>
        </div>
      </div>

      {/* Configured Weights Overview Ribbon */}
      <div className="p-6 rounded-3xl bg-white border border-slate-200 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
            <Sliders className="w-4 h-4 text-sky-600" /> Transparent Scoring Weights (Configured in Settings)
          </span>
          <span className="text-xs font-semibold text-emerald-600">Total: 100% Normalized</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-2">
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 text-center">
            <span className="text-[11px] text-slate-500 font-semibold block">Price Factor</span>
            <span className="text-base font-extrabold text-slate-800">30%</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 text-center">
            <span className="text-[11px] text-slate-500 font-semibold block">Discount %</span>
            <span className="text-base font-extrabold text-slate-800">15%</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 text-center">
            <span className="text-[11px] text-slate-500 font-semibold block">Rating Score</span>
            <span className="text-base font-extrabold text-slate-800">20%</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 text-center">
            <span className="text-[11px] text-slate-500 font-semibold block">NLP Sentiment</span>
            <span className="text-base font-extrabold text-slate-800">20%</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 text-center">
            <span className="text-[11px] text-slate-500 font-semibold block">Availability</span>
            <span className="text-base font-extrabold text-slate-800">10%</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 text-center">
            <span className="text-[11px] text-slate-500 font-semibold block">Seller Rep</span>
            <span className="text-base font-extrabold text-slate-800">5%</span>
          </div>
        </div>
      </div>

      {/* Recommendations Cards */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-48 rounded-3xl bg-white border border-slate-200 animate-pulse p-8" />
          ))}
        </div>
      ) : recommendations.length > 0 ? (
        <div className="space-y-6">
          {recommendations.map((rec, index) => (
            <div
              key={rec.product_id}
              className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm hover:shadow-lg transition space-y-6"
            >
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-2xl bg-indigo-50 text-indigo-700 font-black flex items-center justify-center text-lg border border-indigo-100">
                    #{index + 1}
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-slate-900">{rec.product_name}</h2>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Best Deal on <span className="font-bold text-slate-700">{rec.marketplace}</span>
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <span className="text-xs text-slate-400 font-bold block">Best Price</span>
                    <span className="text-2xl font-black text-emerald-600">{formatINR(rec.price)}</span>
                  </div>
                  <div className="px-3.5 py-2 rounded-2xl bg-indigo-600 text-white font-extrabold text-sm shadow-md shadow-indigo-600/20">
                    {rec.score} / 100
                  </div>
                </div>
              </div>

              {/* Plain Language Explanation */}
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-sm text-slate-700 leading-relaxed flex items-start gap-3">
                <Sparkles className="w-5 h-5 text-indigo-600 flex-shrink-0 mt-0.5" />
                <p>{rec.explanation}</p>
              </div>

              {/* Factor Breakdown Bars */}
              {rec.factor_breakdown && (
                <div className="space-y-2 pt-2">
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">
                    Factor Breakdown:
                  </span>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-slate-500 font-medium">Price Efficiency</span>
                        <span className="font-bold text-slate-800">{Math.round((rec.factor_breakdown.price_factor || 0) * 100)}%</span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                        <div
                          className="h-full bg-emerald-500 rounded-full"
                          style={{ width: `${(rec.factor_breakdown.price_factor || 0) * 100}%` }}
                        />
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-slate-500 font-medium">Rating Score</span>
                        <span className="font-bold text-slate-800">{Math.round((rec.factor_breakdown.rating_factor || 0) * 100)}%</span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                        <div
                          className="h-full bg-blue-500 rounded-full"
                          style={{ width: `${(rec.factor_breakdown.rating_factor || 0) * 100}%` }}
                        />
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-slate-500 font-medium">NLP Sentiment</span>
                        <span className="font-bold text-slate-800">{Math.round((rec.factor_breakdown.sentiment_factor || 0) * 100)}%</span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                        <div
                          className="h-full bg-indigo-500 rounded-full"
                          style={{ width: `${(rec.factor_breakdown.sentiment_factor || 0) * 100}%` }}
                        />
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-slate-500 font-medium">Availability</span>
                        <span className="font-bold text-slate-800">{Math.round((rec.factor_breakdown.availability_factor || 0) * 100)}%</span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                        <div
                          className="h-full bg-purple-500 rounded-full"
                          style={{ width: `${(rec.factor_breakdown.availability_factor || 0) * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Actions Footer */}
              <div className="pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Link
                    to={`/compare?id=${rec.product_id}`}
                    className="px-4 py-2 rounded-xl bg-sky-50 hover:bg-sky-100 text-sky-700 text-xs font-bold flex items-center gap-1.5 transition"
                  >
                    <Layers className="w-3.5 h-3.5" /> Full Comparison
                  </Link>
                  <Link
                    to={`/reviews?id=${rec.product_id}`}
                    className="px-4 py-2 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-bold flex items-center gap-1.5 transition"
                  >
                    <MessageSquareText className="w-3.5 h-3.5" /> Audit Reviews
                  </Link>
                </div>
                <Link
                  to={`/history?id=${rec.product_id}`}
                  className="text-xs font-bold text-slate-500 hover:text-slate-800 flex items-center gap-1"
                >
                  Inspect Price History <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="p-12 bg-white rounded-3xl border border-slate-200 text-center text-slate-500 space-y-2">
          <p className="font-bold text-slate-700">No product recommendations calculated yet.</p>
          <p className="text-xs">Ensure demo mode is turned on or add marketplace listings to generate ratings.</p>
        </div>
      )}
    </div>
  );
};
