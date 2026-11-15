import React from 'react';
import { AlertCircle, CheckCircle2 } from 'lucide-react';

export const ConnectorBadge = ({ marketplace, status, reason }) => {
  const isAvailable = status === 'available';

  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold border ${
        isAvailable
          ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
          : 'bg-amber-50 text-amber-800 border-amber-200'
      }`}
      title={reason || (isAvailable ? 'Connector active' : 'Connector credentials not configured')}
    >
      {isAvailable ? (
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
      ) : (
        <AlertCircle className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" />
      )}
      <span className="font-bold">{marketplace}:</span>
      <span className="truncate max-w-xs">{isAvailable ? 'Live Affiliate Connected' : (reason || 'unavailable – credentials not configured')}</span>
    </div>
  );
};
