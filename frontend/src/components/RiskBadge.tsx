import React from 'react';

interface RiskBadgeProps {
  level: string;
  className?: string;
  showIcon?: boolean;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ level, className = '', showIcon = true }) => {
  const norm = (level || '').toLowerCase();

  let badgeColor = 'bg-emerald-50 text-emerald-800 border-emerald-200';
  let label = 'Steady & Supportive';
  let dotColor = 'bg-emerald-500';

  if (norm === 'moderate' || norm === 'medium') {
    badgeColor = 'bg-amber-50 text-amber-800 border-amber-200';
    label = 'Careful Observation Recommended';
    dotColor = 'bg-amber-500';
  } else if (norm === 'high' || norm === 'severe') {
    badgeColor = 'bg-rose-50 text-rose-800 border-rose-200';
    label = 'Priority Support Advised';
    dotColor = 'bg-rose-500';
  }

  return (
    <span
      className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold border ${badgeColor} ${className}`}
    >
      {showIcon && <span className={`w-2 h-2 rounded-full ${dotColor}`} />}
      <span className="capitalize">{norm || 'Unknown'} Risk</span>
      <span className="text-slate-400 font-normal">| {label}</span>
    </span>
  );
};
