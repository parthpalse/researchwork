import React, { useState } from 'react';
import { TraceObject } from '../lib/types';
import { overrideRisk } from '../lib/api';
import { ShieldCheck, Activity, AlertCircle, CheckCircle2 } from 'lucide-react';

interface TraceViewerProps {
  trace: TraceObject;
  traceId?: number;
  onOverrideSuccess?: (newRisk: string) => void;
}

export const TraceViewer: React.FC<TraceViewerProps> = ({
  trace,
  traceId,
  onOverrideSuccess,
}) => {
  const [overrideLevel, setOverrideLevel] = useState(trace.final_risk_level || 'moderate');
  const [reason, setReason] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');

  const handleOverride = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!traceId || !reason.trim()) return;

    setSubmitting(true);
    try {
      await overrideRisk(traceId, overrideLevel, reason);
      setStatusMsg('Clinical override successfully recorded with audit log.');
      if (onOverrideSuccess) onOverrideSuccess(overrideLevel);
    } catch (err: any) {
      setStatusMsg(err.message || 'Override failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 text-slate-800">
      {/* 1. Inference Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200">
          <div className="text-xs uppercase font-semibold text-slate-400">Final Risk Level</div>
          <div className="text-xl font-bold capitalize text-slate-800 mt-1">
            {trace.final_risk_level}
          </div>
          <div className="text-xs text-slate-500 mt-0.5">
            Confidence: {(trace.final_confidence * 100).toFixed(1)}%
          </div>
        </div>

        <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200">
          <div className="text-xs uppercase font-semibold text-slate-400">WHO Weight-for-Height Z</div>
          <div className="text-xl font-bold text-slate-800 mt-1">
            {trace._metadata?.weight_for_height_z !== undefined
              ? trace._metadata.weight_for_height_z
              : 'N/A'}
          </div>
          <div className="text-xs text-slate-500 mt-0.5">
            MUAC Band: <span className="capitalize">{trace._metadata?.muac_risk_band || 'N/A'}</span>
          </div>
        </div>

        <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200">
          <div className="text-xs uppercase font-semibold text-slate-400">Audit Status</div>
          <div className="text-xl font-bold text-emerald-700 mt-1 flex items-center gap-1.5">
            <ShieldCheck className="w-5 h-5 text-emerald-600" />
            Verified Trace
          </div>
          <div className="text-xs text-slate-500 mt-0.5 truncate">
            {trace.timestamp}
          </div>
        </div>
      </div>

      {/* 2. Rules Fired Table */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="px-5 py-3.5 bg-slate-50 border-b border-slate-200 flex items-center gap-2">
          <Activity className="w-4 h-4 text-emerald-600" />
          <h4 className="font-semibold text-xs text-slate-800 uppercase tracking-wider">
            Fuzzy Inference Rules Fired ({trace.rules_fired.length})
          </h4>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/50 text-slate-500 font-medium border-b border-slate-100">
              <tr>
                <th className="py-2.5 px-4">Rule ID</th>
                <th className="py-2.5 px-4">Antecedents (Conditions)</th>
                <th className="py-2.5 px-4">Firing Strength</th>
                <th className="py-2.5 px-4">Expert CF</th>
                <th className="py-2.5 px-4">Concluded Risk</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {trace.rules_fired.map((r, i) => (
                <tr key={i} className="hover:bg-slate-50/60">
                  <td className="py-2.5 px-4 font-mono font-bold text-slate-700">{r.rule_id}</td>
                  <td className="py-2.5 px-4">
                    <div className="flex flex-wrap gap-1">
                      {Object.entries(r.antecedents).map(([k, v]) => (
                        <span
                          key={k}
                          className="bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded text-[11px]"
                        >
                          {k} is <strong>{v}</strong>
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="py-2.5 px-4 font-medium text-slate-700">{r.strength.toFixed(3)}</td>
                  <td className="py-2.5 px-4 text-slate-500">{r.expert_cf}</td>
                  <td className="py-2.5 px-4 capitalize font-semibold text-slate-800">
                    {r.conclusion_level}
                  </td>
                </tr>
              ))}
              {trace.rules_fired.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-slate-400">
                    No active risk rules triggered. Anthropometrics are within healthy ranges.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 3. Fuzzification Breakdown */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
        <h4 className="font-semibold text-xs text-slate-800 uppercase tracking-wider">
          Fuzzification Membership Degrees
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
          {Object.entries(trace.fuzzification).map(([field, sets]) => (
            <div key={field} className="bg-slate-50 p-3 rounded-xl border border-slate-100 text-xs">
              <div className="font-semibold text-slate-700 mb-1.5">{field}</div>
              <div className="space-y-1">
                {Object.entries(sets).map(([setName, deg]) => (
                  <div key={setName} className="flex justify-between items-center text-slate-500">
                    <span className="capitalize">{setName}</span>
                    <span className="font-mono font-medium text-slate-700">
                      {(deg * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 4. Clinician Override Panel */}
      {traceId && (
        <form
          onSubmit={handleOverride}
          className="bg-amber-50/50 p-5 rounded-2xl border border-amber-200 shadow-sm space-y-3"
        >
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-amber-600" />
            <h4 className="font-semibold text-sm text-slate-800">
              Clinician Diagnostic Override
            </h4>
          </div>
          <p className="text-xs text-slate-600">
            Clinicians maintain primary authority to adjust the computed risk score based on
            clinical presentation or additional symptoms. All overrides are recorded in the audit trail.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Override Risk Level
              </label>
              <select
                value={overrideLevel}
                onChange={(e) => setOverrideLevel(e.target.value)}
                className="w-full text-xs py-2 px-3 border border-slate-300 rounded-xl bg-white focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
              >
                <option value="low">Low Risk</option>
                <option value="moderate">Moderate Risk</option>
                <option value="high">High Risk</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Clinical Rationale / Justification
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Bilateral pitting edema observed during in-person exam"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                className="w-full text-xs py-2 px-3 border border-slate-300 rounded-xl bg-white focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
              />
            </div>
          </div>

          <div className="flex items-center justify-between pt-2">
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-semibold shadow-sm transition-colors disabled:opacity-50"
            >
              {submitting ? 'Saving Override...' : 'Submit Clinical Override'}
            </button>
            {statusMsg && (
              <span className="text-xs font-medium text-emerald-700 flex items-center gap-1">
                <CheckCircle2 className="w-4 h-4" /> {statusMsg}
              </span>
            )}
          </div>
        </form>
      )}
    </div>
  );
};
