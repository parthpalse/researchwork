import React from 'react';
import { ChildListItem, Role } from '../lib/types';
import { Users, Plus, ChevronRight } from 'lucide-react';

interface ChildrenListProps {
  role: Role;
  items: ChildListItem[];
  activeChildId: string | null;
  loading: boolean;
  onOpen: (childId: string) => void;
  onNewChild: () => void;
}

const RISK_STYLE: Record<string, string> = {
  low: 'bg-emerald-50 text-emerald-700',
  moderate: 'bg-amber-50 text-amber-700',
  high: 'bg-rose-50 text-rose-700',
};

export const ChildrenList: React.FC<ChildrenListProps> = ({
  role,
  items,
  activeChildId,
  loading,
  onOpen,
  onNewChild,
}) => (
  <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-100 space-y-3">
    <div className="flex items-center justify-between gap-2">
      <div className="flex items-center gap-2">
        <Users className="w-5 h-5 text-emerald-600" />
        <h3 className="font-semibold text-sm text-slate-800">
          {role === 'clinician' ? 'All Patients' : 'My Children'}
          {!loading && ` (${items.length})`}
        </h3>
      </div>
      <button
        onClick={onNewChild}
        className="flex items-center gap-1 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold"
      >
        <Plus className="w-3.5 h-3.5" /> New child
      </button>
    </div>

    {loading ? (
      <p className="text-xs text-slate-400">Loading...</p>
    ) : items.length === 0 ? (
      <p className="text-xs text-slate-400">
        {role === 'clinician' ? 'No children have been added yet.' : 'No children yet. Fill in the details below to add one.'}
      </p>
    ) : (
      <div className="divide-y divide-slate-100 max-h-64 overflow-y-auto -mx-1">
        {items.map((c) => (
          <button
            key={c.child_id}
            onClick={() => onOpen(c.child_id)}
            className={`w-full flex items-center justify-between gap-3 px-1 py-2.5 text-left text-xs rounded-lg ${
              c.child_id === activeChildId ? 'bg-emerald-50/60' : 'hover:bg-slate-50'
            }`}
          >
            <div className="min-w-0">
              <div className="font-semibold text-slate-800 truncate">{c.child_id}</div>
              <div className="text-[11px] text-slate-400">
                {(c.age_months / 12).toFixed(1)} y · {c.sex === 'M' ? 'Boy' : 'Girl'}
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              {c.latest_risk ? (
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold capitalize ${RISK_STYLE[c.latest_risk] ?? 'bg-slate-100 text-slate-600'}`}>
                  {c.latest_risk}
                </span>
              ) : (
                <span className="text-[10px] text-slate-400">Not assessed</span>
              )}
              <ChevronRight className="w-4 h-4 text-slate-300" />
            </div>
          </button>
        ))}
      </div>
    )}
  </div>
);
