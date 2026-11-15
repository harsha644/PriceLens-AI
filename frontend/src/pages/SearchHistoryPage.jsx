import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api/axios';
import { formatDate } from '../utils/formatters';
import {
  History,
  Search,
  Trash2,
  ArrowRight,
  Clock,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';

export const SearchHistoryPage = () => {
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState({ error: '', success: '' });

  const loadHistory = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/recommendations/history/');
      setHistory(res.data || []);
    } catch (err) {
      console.error('Error loading search history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const handleDeleteItem = async (id) => {
    try {
      await api.delete(`/api/recommendations/history/${id}/`);
      setHistory(history.filter((h) => h.id !== id));
      setMsg({ error: '', success: 'Entry deleted from history.' });
    } catch (err) {
      setMsg({ error: 'Failed to delete history item.', success: '' });
    }
  };

  const handleClearAll = async () => {
    if (!window.confirm('Clear all your search history entries?')) return;
    try {
      await api.delete('/api/recommendations/history/');
      setHistory([]);
      setMsg({ error: '', success: 'All search history cleared.' });
    } catch (err) {
      setMsg({ error: 'Failed to clear search history.', success: '' });
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Your Search History</h1>
          <p className="text-sm text-slate-500 mt-1">
            Private, user-isolated records of past queries and applied filters
          </p>
        </div>

        {history.length > 0 && (
          <button
            onClick={handleClearAll}
            className="px-4 py-2 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 text-xs font-bold transition flex items-center gap-1.5"
          >
            <Trash2 className="w-4 h-4" /> Clear All History
          </button>
        )}
      </div>

      {msg.success && (
        <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>{msg.success}</span>
        </div>
      )}

      {msg.error && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-600" />
          <span>{msg.error}</span>
        </div>
      )}

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-16 rounded-2xl bg-white border border-slate-200 animate-pulse" />
          ))}
        </div>
      ) : history.length > 0 ? (
        <div className="bg-white rounded-3xl border border-slate-200 shadow-sm divide-y divide-slate-100 overflow-hidden">
          {history.map((item) => (
            <div
              key={item.id}
              className="p-4 sm:p-5 flex items-center justify-between gap-4 hover:bg-slate-50/70 transition"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-9 h-9 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center flex-shrink-0">
                  <Search className="w-4 h-4" />
                </div>
                <div className="min-w-0">
                  <Link
                    to={`/products?q=${encodeURIComponent(item.query)}`}
                    className="font-bold text-slate-800 text-sm hover:text-sky-600 truncate block"
                  >
                    "{item.query}"
                  </Link>
                  <div className="flex items-center gap-3 text-xs text-slate-400 mt-0.5">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" /> {formatDate(item.created_at)}
                    </span>
                    {item.category && (
                      <span className="bg-slate-100 text-slate-600 px-2 py-0.5 rounded-md font-medium">
                        {item.category}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 flex-shrink-0">
                <Link
                  to={`/products?q=${encodeURIComponent(item.query)}`}
                  className="px-3 py-1.5 rounded-lg bg-sky-50 hover:bg-sky-100 text-sky-700 text-xs font-bold transition flex items-center gap-1"
                >
                  Search Again <ArrowRight className="w-3.5 h-3.5" />
                </Link>
                <button
                  onClick={() => handleDeleteItem(item.id)}
                  className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition"
                  title="Delete this query from history"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="p-12 bg-white rounded-3xl border border-slate-200 text-center text-slate-500 space-y-3">
          <History className="w-10 h-10 text-slate-300 mx-auto" />
          <h4 className="font-bold text-slate-700">No search history yet</h4>
          <p className="text-xs max-w-sm mx-auto">
            When you search for products and models in the catalog, your queries will appear here for fast re-discovery.
          </p>
        </div>
      )}
    </div>
  );
};
