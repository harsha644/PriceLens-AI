import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';
import { DemoBadge } from '../components/DemoBadge';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import {
  MessageSquareText,
  Star,
  ShieldAlert,
  Upload,
  Send,
  PlusCircle,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Sparkles,
} from 'lucide-react';

export const ReviewAnalysisPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { demoMode } = useAuth();
  const productId = searchParams.get('id');

  const [products, setProducts] = useState([]);
  const [selectedProductId, setSelectedProductId] = useState(productId || '');
  const [analysis, setAnalysis] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('insights'); // insights | ingest

  // Manual Review Form State
  const [manualReview, setManualReview] = useState({
    reviewer_name: '',
    review_title: '',
    review_text: '',
    rating: 5,
    is_verified_purchase: true,
  });

  // CSV Upload State
  const [csvFile, setCsvFile] = useState(null);
  const [ingestStatus, setIngestStatus] = useState({ error: '', success: '', loading: false });

  useEffect(() => {
    api.get(`/api/catalog/?include_demo=${demoMode}`).then((res) => {
      setProducts(res.data || []);
      if (!selectedProductId && res.data?.length > 0) {
        setSelectedProductId(productId || res.data[0].id);
      }
    }).catch(() => {});
  }, [demoMode, productId]);

  const loadAnalysisAndReviews = async (id) => {
    if (!id) return;
    setLoading(true);
    try {
      const [anaRes, revRes] = await Promise.all([
        api.get(`/api/reviews/${id}/analysis/?include_demo=${demoMode}`),
        api.get(`/api/reviews/${id}/?include_demo=${demoMode}`),
      ]);
      setAnalysis(anaRes.data);
      setReviews(revRes.data || []);
    } catch (err) {
      console.error('Error loading review analysis:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedProductId) {
      loadAnalysisAndReviews(selectedProductId);
    }
  }, [selectedProductId, demoMode]);

  const handleProductChange = (e) => {
    const newId = e.target.value;
    setSelectedProductId(newId);
    setSearchParams({ id: newId });
  };

  const handleManualSubmit = async (e) => {
    e.preventDefault();
    if (!manualReview.review_text.trim()) return;

    setIngestStatus({ error: '', success: '', loading: true });
    try {
      await api.post(`/api/reviews/${selectedProductId}/`, {
        ...manualReview,
        rating: Number(manualReview.rating),
      });
      setIngestStatus({ error: '', success: 'Review submitted and NLP analysis refreshed!', loading: false });
      setManualReview({ reviewer_name: '', review_title: '', review_text: '', rating: 5, is_verified_purchase: true });
      loadAnalysisAndReviews(selectedProductId);
    } catch (err) {
      setIngestStatus({
        error: err.response?.data?.error || 'Failed to submit review.',
        success: '',
        loading: false,
      });
    }
  };

  const handleCsvUpload = async (e) => {
    e.preventDefault();
    if (!csvFile) return;

    setIngestStatus({ error: '', success: '', loading: true });
    try {
      const formData = new FormData();
      formData.append('file', csvFile);
      formData.append('is_demo', 'false');

      const res = await api.post(`/api/reviews/${selectedProductId}/upload-csv/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setIngestStatus({
        error: '',
        success: res.data.message || 'CSV imported successfully!',
        loading: false,
      });
      setCsvFile(null);
      loadAnalysisAndReviews(selectedProductId);
    } catch (err) {
      setIngestStatus({
        error: err.response?.data?.error || 'Failed to parse and import CSV.',
        success: '',
        loading: false,
      });
    }
  };

  // Prepare chart data
  const sentimentData = [
    { name: 'Positive', value: analysis?.sentiment_distribution?.positive || 0, color: '#10B981' },
    { name: 'Neutral', value: analysis?.sentiment_distribution?.neutral || 0, color: '#64748B' },
    { name: 'Negative', value: analysis?.sentiment_distribution?.negative || 0, color: '#EF4444' },
  ];

  const ratingData = [
    { stars: '5★', count: analysis?.rating_distribution?.['5'] || 0 },
    { stars: '4★', count: analysis?.rating_distribution?.['4'] || 0 },
    { stars: '3★', count: analysis?.rating_distribution?.['3'] || 0 },
    { stars: '2★', count: analysis?.rating_distribution?.['2'] || 0 },
    { stars: '1★', count: analysis?.rating_distribution?.['1'] || 0 },
  ];

  return (
    <div className="space-y-8">
      {/* Page Title & Picker */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">NLP Review & Sentiment Intelligence</h1>
          <p className="text-sm text-slate-500 mt-1">
            Auditing reviews via VADER + TextBlob, TF-IDF cosine similarity, and rating-sentiment alignment
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

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200 gap-4">
        <button
          onClick={() => setActiveTab('insights')}
          className={`pb-3 text-sm font-bold flex items-center gap-2 border-b-2 transition ${
            activeTab === 'insights'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Sparkles className="w-4 h-4" /> Sentiment & Pattern Insights
        </button>
        <button
          onClick={() => setActiveTab('ingest')}
          className={`pb-3 text-sm font-bold flex items-center gap-2 border-b-2 transition ${
            activeTab === 'ingest'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <PlusCircle className="w-4 h-4" /> Ingest Reviews (CSV / Manual)
        </button>
      </div>

      {activeTab === 'insights' && (
        <div className="space-y-8">
          {/* Summary Stat Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Total Analyzed</span>
              <p className="text-3xl font-black text-slate-900 mt-1">{analysis?.total_reviews || 0}</p>
              <p className="text-xs text-slate-500 mt-1">Verified customer entries</p>
            </div>

            <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Average Rating</span>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-3xl font-black text-slate-900">{analysis?.average_rating || '0.0'}</span>
                <Star className="w-6 h-6 text-amber-500 fill-amber-500" />
              </div>
              <p className="text-xs text-slate-500 mt-1">Normalized across stars</p>
            </div>

            <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Positive Sentiment</span>
              <p className="text-3xl font-black text-emerald-600 mt-1">
                {analysis?.sentiment_distribution?.positive || 0}%
              </p>
              <p className="text-xs text-slate-500 mt-1">VADER compound &gt;= +0.05</p>
            </div>

            <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Potential Indicators</span>
              <p className="text-3xl font-black text-amber-600 mt-1">
                {(analysis?.suspicious_indicators || []).length}
              </p>
              <p className="text-xs text-slate-500 mt-1">Patterns flagged for review</p>
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Sentiment Pie Chart */}
            <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm">
              <h3 className="font-bold text-slate-900 text-sm mb-4">Sentiment Distribution (%)</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={sentimentData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={55}
                      outerRadius={85}
                      paddingAngle={4}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {sentimentData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Rating Distribution Bar Chart */}
            <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm">
              <h3 className="font-bold text-slate-900 text-sm mb-4">Star Rating Distribution</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={ratingData} layout="vertical" margin={{ left: 20, right: 30 }}>
                    <XAxis type="number" />
                    <YAxis dataKey="stars" type="category" />
                    <Tooltip />
                    <Bar dataKey="count" fill="#3B82F6" radius={[0, 8, 8, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Keywords & Suspicious Pattern Indicators */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Keywords */}
            <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
              <h3 className="font-bold text-slate-900 text-sm">Key Themes & Keywords (NLTK Filtered)</h3>
              <div>
                <span className="text-xs font-bold text-emerald-700 block mb-2">Top Positive Expressions:</span>
                <div className="flex flex-wrap gap-2">
                  {(analysis?.top_positive_words || []).length > 0 ? (
                    analysis.top_positive_words.map((w, i) => (
                      <span key={i} className="px-3 py-1 bg-emerald-50 text-emerald-800 text-xs font-semibold rounded-lg border border-emerald-200">
                        {w.word} ({w.count})
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-slate-400">None detected</span>
                  )}
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100">
                <span className="text-xs font-bold text-rose-700 block mb-2">Top Negative Expressions:</span>
                <div className="flex flex-wrap gap-2">
                  {(analysis?.top_negative_words || []).length > 0 ? (
                    analysis.top_negative_words.map((w, i) => (
                      <span key={i} className="px-3 py-1 bg-rose-50 text-rose-800 text-xs font-semibold rounded-lg border border-rose-200">
                        {w.word} ({w.count})
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-slate-400">None detected</span>
                  )}
                </div>
              </div>
            </div>

            {/* Suspicious Patterns */}
            <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-amber-600" /> Potential Pattern Indicators
                </h3>
                <span className="text-[11px] text-slate-400">Strictly statistical flags</span>
              </div>

              {(analysis?.suspicious_indicators || []).length > 0 ? (
                <div className="space-y-3">
                  {analysis.suspicious_indicators.map((ind, i) => (
                    <div
                      key={i}
                      className={`p-4 rounded-2xl border text-xs leading-relaxed flex items-start gap-3 ${
                        ind.severity === 'high'
                          ? 'bg-rose-50 border-rose-200 text-rose-800'
                          : 'bg-amber-50 border-amber-200 text-amber-800'
                      }`}
                    >
                      <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                      <div>
                        <span className="font-bold uppercase tracking-wider block mb-0.5">
                          {ind.type.replace(/_/g, ' ')}
                        </span>
                        <span>{ind.detail}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-8 text-center text-slate-400">
                  <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                  <p className="text-xs font-semibold">No high-risk suspicious text repetition or timing anomalies detected.</p>
                </div>
              )}
            </div>
          </div>

          {/* Raw Reviews Stream */}
          <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
            <h3 className="font-bold text-slate-900 text-sm">Customer Reviews ({reviews.length})</h3>
            <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
              {reviews.map((r) => (
                <div key={r.id} className="p-4 rounded-2xl bg-slate-50 border border-slate-100 text-sm space-y-1.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-800">{r.reviewer_name}</span>
                      {r.is_verified_purchase && (
                        <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                          Verified Purchase
                        </span>
                      )}
                      {r.is_demo && <DemoBadge />}
                    </div>
                    <div className="flex items-center gap-1 font-bold text-amber-500 text-xs">
                      <Star className="w-3.5 h-3.5 fill-amber-500" />
                      <span>{r.rating}★</span>
                    </div>
                  </div>
                  {r.review_title && <p className="font-bold text-slate-800 text-xs">{r.review_title}</p>}
                  <p className="text-xs text-slate-600 leading-relaxed">{r.review_text}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Review Ingestion Tab */}
      {activeTab === 'ingest' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Manual Review Paste */}
          <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-6">
            <div>
              <h3 className="font-bold text-slate-900 text-base">Manual Review Submission</h3>
              <p className="text-xs text-slate-500 mt-1">Paste customer review text to test sentiment scoring and mismatch checks.</p>
            </div>

            <form onSubmit={handleManualSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Reviewer Name
                </label>
                <input
                  type="text"
                  value={manualReview.reviewer_name}
                  onChange={(e) => setManualReview({ ...manualReview, reviewer_name: e.target.value })}
                  placeholder="Anonymous or customer name"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Star Rating (1 to 5)
                </label>
                <select
                  value={manualReview.rating}
                  onChange={(e) => setManualReview({ ...manualReview, rating: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm outline-none focus:border-indigo-500"
                >
                  <option value={5}>5 Stars - Excellent</option>
                  <option value={4}>4 Stars - Good</option>
                  <option value={3}>3 Stars - Average</option>
                  <option value={2}>2 Stars - Below Average</option>
                  <option value={1}>1 Star - Terrible</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Review Title
                </label>
                <input
                  type="text"
                  value={manualReview.review_title}
                  onChange={(e) => setManualReview({ ...manualReview, review_title: e.target.value })}
                  placeholder="e.g. Battery backup is outstanding"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Review Content *
                </label>
                <textarea
                  required
                  rows={4}
                  value={manualReview.review_text}
                  onChange={(e) => setManualReview({ ...manualReview, review_text: e.target.value })}
                  placeholder="Type or paste the full review text here..."
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm outline-none focus:border-indigo-500"
                />
              </div>

              <button
                type="submit"
                disabled={ingestStatus.loading}
                className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm shadow transition flex items-center justify-center gap-2"
              >
                <Send className="w-4 h-4" /> Submit & Refresh Analysis
              </button>
            </form>
          </div>

          {/* CSV File Upload */}
          <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-6 flex flex-col justify-between">
            <div className="space-y-4">
              <div>
                <h3 className="font-bold text-slate-900 text-base">Bulk Ingestion via CSV</h3>
                <p className="text-xs text-slate-500 mt-1">
                  Upload exported review datasets (columns: review_text, rating, reviewer_name, review_title).
                </p>
              </div>

              {ingestStatus.error && (
                <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs">
                  {ingestStatus.error}
                </div>
              )}

              {ingestStatus.success && (
                <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  {ingestStatus.success}
                </div>
              )}

              <form onSubmit={handleCsvUpload} className="space-y-4">
                <div className="border-2 border-dashed border-slate-200 hover:border-indigo-500 rounded-2xl p-8 text-center bg-slate-50/50">
                  <input
                    type="file"
                    accept=".csv"
                    onChange={(e) => setCsvFile(e.target.files?.[0] || null)}
                    className="w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
                  />
                  <p className="text-xs text-slate-400 mt-2">Only .csv files up to 5MB supported</p>
                </div>

                <button
                  type="submit"
                  disabled={!csvFile || ingestStatus.loading}
                  className="w-full py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-sm shadow transition flex items-center justify-center gap-2 disabled:opacity-40"
                >
                  <Upload className="w-4 h-4" /> Import CSV File
                </button>
              </form>
            </div>

            <div className="p-4 rounded-2xl bg-indigo-50 border border-indigo-100 text-xs text-indigo-900 space-y-1">
              <span className="font-bold">Affiliate API Disclaimer:</span>
              <p className="text-[11px] leading-relaxed text-indigo-700">
                Official Amazon PA-API and Flipkart Affiliate APIs do not expose full user review text due to marketplace terms. PriceLens AI enables transparent CSV and user review ingestion to run comprehensive NLP sentiment analytics locally.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
