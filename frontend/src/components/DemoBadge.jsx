import React from 'react';
import { Sparkles } from 'lucide-react';

export const DemoBadge = ({ size = 'sm' }) => {
  return (
    <span
      className={`inline-flex items-center gap-1 font-semibold rounded-full border border-purple-200 bg-purple-50 text-purple-700 ${
        size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs'
      }`}
      title="This record is labelled demo data (is_demo=True)"
    >
      <Sparkles className="w-3 h-3 text-purple-500" />
      Demo Data
    </span>
  );
};
