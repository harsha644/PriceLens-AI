import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, ShieldCheck, TrendingDown, MessageSquareText, Search, Sparkles } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const Landing = () => {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-slate-900 text-white selection:bg-sky-500 selection:text-white">
      {/* Hero Header */}
      <nav className="max-w-7xl mx-auto px-6 py-6 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-500 flex items-center justify-center text-white shadow-lg shadow-sky-500/30">
            <TrendingDown className="w-6 h-6" />
          </div>
          <span className="text-2xl font-black tracking-tight bg-gradient-to-r from-sky-400 via-indigo-300 to-white bg-clip-text text-transparent">
            PriceLens AI
          </span>
        </div>
        <div className="flex items-center gap-4">
          {user ? (
            <Link
              to="/dashboard"
              className="px-5 py-2.5 rounded-xl bg-sky-500 hover:bg-sky-400 font-bold text-white transition shadow-lg shadow-sky-500/25 flex items-center gap-2"
            >
              Dashboard <ArrowRight className="w-4 h-4" />
            </Link>
          ) : (
            <>
              <Link to="/login" className="text-slate-300 hover:text-white font-medium text-sm px-3 py-2">
                Sign In
              </Link>
              <Link
                to="/register"
                className="px-5 py-2 rounded-xl bg-sky-500 hover:bg-sky-400 font-bold text-white transition shadow-lg shadow-sky-500/25 text-sm"
              >
                Get Started
              </Link>
            </>
          )}
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-6 pt-16 pb-24 text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-sky-500/30 bg-sky-500/10 text-sky-400 text-xs font-semibold uppercase tracking-wider mb-8">
          <Sparkles className="w-4 h-4" /> Official Amazon India & Flipkart Intelligence
        </div>
        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight max-w-4xl mx-auto leading-tight">
          Smart Product Review & <span className="bg-gradient-to-r from-sky-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">Price Analyzer</span>
        </h1>
        <p className="mt-6 text-lg sm:text-xl text-slate-400 max-w-2xl mx-auto leading-relaxed">
          Compare authentic prices between Amazon India and Flipkart, inspect NLP sentiment from customer reviews, and get data-driven purchase recommendations with complete transparency.
        </p>

        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <Link
            to={user ? "/dashboard" : "/register"}
            className="px-8 py-3.5 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white font-bold text-base transition shadow-xl shadow-sky-500/20 flex items-center gap-2"
          >
            Launch PriceLens AI <ArrowRight className="w-5 h-5" />
          </Link>
          <Link
            to="/login"
            className="px-8 py-3.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 font-bold text-base transition"
          >
            Explore Live Demo
          </Link>
        </div>

        {/* Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-20 text-left">
          <div className="p-8 rounded-2xl bg-slate-800/60 border border-slate-700/60 backdrop-blur hover:border-sky-500/40 transition">
            <div className="w-12 h-12 rounded-xl bg-sky-500/10 text-sky-400 flex items-center justify-center mb-5">
              <TrendingDown className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold mb-2">Live Marketplace Comparison</h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              Real-time price tracking, discount analysis, shipping details, and seller reputations across Amazon India and Flipkart.
            </p>
          </div>

          <div className="p-8 rounded-2xl bg-slate-800/60 border border-slate-700/60 backdrop-blur hover:border-indigo-500/40 transition">
            <div className="w-12 h-12 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center mb-5">
              <MessageSquareText className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold mb-2">NLP Review Intelligence</h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              VADER & TextBlob sentiment scoring, duplicate detection, and rating-sentiment mismatch audits without expensive cloud AI APIs.
            </p>
          </div>

          <div className="p-8 rounded-2xl bg-slate-800/60 border border-slate-700/60 backdrop-blur hover:border-purple-500/40 transition">
            <div className="w-12 h-12 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center mb-5">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold mb-2">Strict Data Integrity</h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              Zero web scraping, no anti-bot bypasses. Official affiliate feeds only, with clear connector status badges and separate demo flags.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};
