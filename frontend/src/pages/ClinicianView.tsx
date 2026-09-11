import React, { useState, useEffect } from 'react';
import { AssessResponse, ChildHistoryItem } from '../lib/types';
import { TraceViewer } from '../components/TraceViewer';
import { getChildHistory } from '../lib/api';
import { Stethoscope, History, FileText, ArrowLeft } from 'lucide-react';

interface ClinicianViewProps {
  assessment: AssessResponse;
  onBackToIntake?: () => void;
}

export const ClinicianView: React.FC<ClinicianViewProps> = ({
  assessment,
  onBackToIntake,
}) => {
  const [currentTrace, setCurrentTrace] = useState(assessment.trace);
  const [history, setHistory] = useState<ChildHistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  useEffect(() => {
    if (assessment.trace.child_id) {
      setLoadingHistory(true);
      getChildHistory(assessment.trace.child_id)
        .then((items) => {
          setHistory(items);
          setLoadingHistory(false);
        })
        .catch(() => setLoadingHistory(false));
    }
  }, [assessment.trace.child_id]);

  const handleOverrideSuccess = (newRisk: string) => {
    setCurrentTrace((prev) => ({
      ...prev,
      final_risk_level: newRisk,
    }));
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-slate-900 text-white p-6 rounded-3xl shadow-md flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-slate-800 rounded-2xl text-emerald-400">
            <Stethoscope className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold">Clinician Audit & Decision Support</h1>
              <span className="bg-slate-800 text-slate-300 text-[10px] font-mono px-2 py-0.5 rounded">
                SECURE TRACE
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Child Record ID: <strong className="text-white">{assessment.trace.child_id}</strong> • Trace ID #{assessment.trace_id}
            </p>
          </div>
        </div>

        {onBackToIntake && (
          <button
            onClick={onBackToIntake}
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-semibold rounded-xl text-slate-200 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Return to Intake
          </button>
        )}
      </div>

      {/* Clinician Note Card */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-2">
        <div className="flex items-center gap-2 text-slate-800 font-semibold text-xs uppercase tracking-wider">
          <FileText className="w-4 h-4 text-emerald-600" />
          Automated Clinical Summary (Rule-Derived)
        </div>
        <div className="text-xs text-slate-700 font-mono bg-slate-50 p-3.5 rounded-xl border border-slate-100 whitespace-pre-wrap">
          {assessment.explanation.clinician_note}
        </div>
      </div>

      {/* Full Trace Viewer Component */}
      <TraceViewer
        trace={currentTrace}
        traceId={assessment.trace_id}
        onOverrideSuccess={handleOverrideSuccess}
      />

      {/* Historical Audit Trail */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
        <div className="flex items-center gap-2 text-slate-800 font-semibold text-xs uppercase tracking-wider">
          <History className="w-4 h-4 text-emerald-600" />
          Child Trace Assessment History
        </div>

        {loadingHistory ? (
          <div className="text-xs text-slate-400">Loading history logs...</div>
        ) : history.length === 0 ? (
          <div className="text-xs text-slate-400">No prior traces recorded for this child.</div>
        ) : (
          <div className="divide-y divide-slate-100 text-xs">
            {history.map((h, i) => (
              <div key={i} className="py-2.5 flex items-center justify-between">
                <div>
                  <div className="font-semibold text-slate-700 capitalize">
                    {h.final_risk_level} Risk ({(h.final_confidence * 100).toFixed(0)}% CF)
                  </div>
                  <div className="text-[11px] text-slate-400">{h.timestamp}</div>
                </div>
                <div>
                  {h.has_override ? (
                    <span className="text-[10px] bg-amber-50 text-amber-700 px-2 py-0.5 rounded font-semibold border border-amber-200">
                      Clinician Overridden
                    </span>
                  ) : (
                    <span className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-medium">
                      Unmodified Rule Engine
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
