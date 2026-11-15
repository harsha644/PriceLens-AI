import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';
import {
  UploadCloud,
  CheckCircle2,
  AlertCircle,
  Camera,
  Layers,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';

export const ImageUpload = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { demoMode } = useAuth();

  const preselectedId = searchParams.get('id');

  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [products, setProducts] = useState([]);
  const [targetProductId, setTargetProductId] = useState(preselectedId || '');
  const [isPrimary, setIsPrimary] = useState(true);
  const [confirmed, setConfirmed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    api.get(`/api/catalog/?include_demo=${demoMode}`).then((res) => {
      setProducts(res.data || []);
      if (!targetProductId && res.data?.length > 0) {
        setTargetProductId(preselectedId || res.data[0].id);
      }
    }).catch(() => {});
  }, [demoMode, preselectedId]);

  const handleFileChange = (e) => {
    setError('');
    setSuccess('');
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate size (< 5MB)
    if (file.size > 5 * 1024 * 1024) {
      setError('File size exceeds 5MB limit. Please choose a smaller image.');
      return;
    }

    // Validate extension
    const allowed = ['image/jpeg', 'image/png', 'image/webp'];
    if (!allowed.includes(file.type)) {
      setError('Only JPG, JPEG, PNG, and WebP formats are allowed.');
      return;
    }

    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const handleUploadAndConfirm = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('Please select an image file first.');
      return;
    }
    if (!targetProductId) {
      setError('Please select a target product to attach this image to.');
      return;
    }
    if (!confirmed) {
      setError('Manual user confirmation is required. Please check the confirmation box.');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const formData = new FormData();
      formData.append('image', selectedFile);
      formData.append('product_id', targetProductId);
      formData.append('is_primary', isPrimary ? 'true' : 'false');
      formData.append('confirmed_by_user', 'true');

      await api.post('/api/catalog/upload-image/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setSuccess('Image successfully validated, confirmed, and attached to the product!');
      setTimeout(() => {
        navigate(`/compare?id=${targetProductId}`);
      }, 1500);
    } catch (err) {
      setError(err.response?.data?.image?.[0] || err.response?.data?.error || 'Failed to upload and attach image.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Product Image Upload & Confirmation</h1>
        <p className="text-sm text-slate-500 mt-1">
          Upload local product photos with strict validation. Images are attached strictly upon manual user verification.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-rose-500" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm flex items-start gap-3">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0 mt-0.5 text-emerald-600" />
          <span>{success}</span>
        </div>
      )}

      <form onSubmit={handleUploadAndConfirm} className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 space-y-6 shadow-sm">
        {/* Target Product Selection */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
            Target Product to Attach Image
          </label>
          <select
            value={targetProductId}
            onChange={(e) => setTargetProductId(e.target.value)}
            className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-white text-sm text-slate-800 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20"
          >
            <option value="">-- Choose a Product --</option>
            {products.map((p) => (
              <option key={p.id} value={p.id}>
                {p.brand} - {p.name} ({[p.variant, p.ram, p.storage].filter(Boolean).join(', ')})
              </option>
            ))}
          </select>
          <p className="text-xs text-slate-400 mt-1.5 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            No paid vision AI: you manually confirm which product the photo belongs to.
          </p>
        </div>

        {/* Drag and Drop Upload Area */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
            Select Photo (JPG, PNG, WebP &bull; Max 5MB)
          </label>
          <div className="relative border-2 border-dashed border-slate-300 hover:border-sky-500 rounded-2xl p-8 text-center bg-slate-50/50 transition">
            <input
              type="file"
              accept=".jpg,.jpeg,.png,.webp"
              onChange={handleFileChange}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            <div className="flex flex-col items-center justify-center space-y-3">
              <div className="w-12 h-12 rounded-2xl bg-sky-50 text-sky-600 flex items-center justify-center">
                <UploadCloud className="w-6 h-6" />
              </div>
              <div>
                <p className="text-sm font-bold text-slate-700">Click or drag & drop to choose an image</p>
                <p className="text-xs text-slate-400 mt-0.5">High resolution, clear angle recommended</p>
              </div>
            </div>
          </div>
        </div>

        {/* Image Preview & Settings */}
        {previewUrl && (
          <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 flex flex-col sm:flex-row items-center gap-6">
            <img
              src={previewUrl}
              alt="Preview"
              className="w-32 h-32 object-cover rounded-xl border border-slate-200 shadow-sm"
            />
            <div className="space-y-3 flex-1 text-sm">
              <div>
                <p className="font-bold text-slate-800">{selectedFile?.name}</p>
                <p className="text-xs text-slate-500">{(selectedFile?.size / (1024 * 1024)).toFixed(2)} MB &bull; {selectedFile?.type}</p>
              </div>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isPrimary}
                  onChange={(e) => setIsPrimary(e.target.checked)}
                  className="w-4 h-4 rounded text-sky-600 focus:ring-sky-500 border-slate-300"
                />
                <span className="text-xs font-semibold text-slate-700">Set as Primary Product Photo</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer bg-white p-3 rounded-xl border border-sky-200">
                <input
                  type="checkbox"
                  checked={confirmed}
                  onChange={(e) => setConfirmed(e.target.checked)}
                  className="w-4 h-4 rounded text-sky-600 focus:ring-sky-500 border-slate-300"
                />
                <span className="text-xs font-bold text-sky-900">
                  I manually confirm this image matches the chosen product model & variant.
                </span>
              </label>
            </div>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading || !selectedFile || !targetProductId || !confirmed}
          className="w-full py-3.5 px-4 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-bold text-sm transition shadow-lg shadow-sky-600/25 flex items-center justify-center gap-2 disabled:opacity-40"
        >
          {loading ? (
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <>
              Confirm & Attach Image <CheckCircle2 className="w-4 h-4" />
            </>
          )}
        </button>
      </form>
    </div>
  );
};
