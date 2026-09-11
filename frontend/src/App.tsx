import React, { useState } from 'react';
import { ChildInput, NutrientSummary, AssessResponse } from './lib/types';
import { assessChild } from './lib/api';
import { IntakeForm } from './pages/IntakeForm';
import { MealLogger } from './pages/MealLogger';
import { ParentView } from './pages/ParentView';
import { ClinicianView } from './pages/ClinicianView';
import { HeartPulse, User, ShieldAlert, Utensils } from 'lucide-react';

type ViewMode = 'intake' | 'parent' | 'clinician';

export const App: React.FC = () => {
  const [viewMode, setViewMode] = useState<ViewMode>('intake');
  const [childData, setChildData] = useState<ChildInput | null>(null);
  const [nutrientSummary, setNutrientSummary] = useState<NutrientSummary | null>(null);
  const [assessment, setAssessment] = useState<AssessResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'anthropometrics' | 'meals'>('anthropometrics');

  const handleIntakeSubmit = async (data: ChildInput) => {
    setChildData(data);
    setLoading(true);
    try {
      const res = await assessChild(data, nutrientSummary);
      setAssessment(res);
      setViewMode('parent');
    } catch (err) {
      console.error(err);
      alert('Error running assessment. Please check backend connection.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Top Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
        <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-emerald-600 text-white rounded-xl shadow-xs">
              <HeartPulse className="w-5 h-5" />
            </div>
            <div>
              <span className="font-bold text-sm tracking-tight text-slate-900 block leading-tight">
                Trust-First AI Nutrition Risk System
              </span>
              <span className="text-[11px] text-slate-500 block">
                TY Mini Project • Hand-Rolled Fuzzy Logic + Auditable Trace
              </span>
            </div>
          </div>

          {/* View Mode Tabs */}
          <nav className="flex items-center gap-1 bg-slate-100 p-1 rounded-2xl text-xs font-semibold">
            <button
              onClick={() => setViewMode('intake')}
              className={`px-3 py-1.5 rounded-xl transition-all ${
                viewMode === 'intake'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Intake & Meals
            </button>
            <button
              onClick={() => {
                if (assessment) setViewMode('parent');
                else alert('Please run an assessment first via the intake form.');
              }}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl transition-all ${
                viewMode === 'parent'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <User className="w-3.5 h-3.5" /> Parent View
            </button>
            <button
              onClick={() => {
                if (assessment) setViewMode('clinician');
                else alert('Please run an assessment first via the intake form.');
              }}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl transition-all ${
                viewMode === 'clinician'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <ShieldAlert className="w-3.5 h-3.5" /> Clinician Audit
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-5xl w-full mx-auto px-4 py-8">
        {viewMode === 'intake' && (
          <div className="space-y-6">
            {/* Step navigation tabs */}
            <div className="flex justify-center">
              <div className="inline-flex bg-slate-200/80 p-1 rounded-2xl text-xs font-semibold gap-1">
                <button
                  onClick={() => setActiveTab('anthropometrics')}
                  className={`flex items-center gap-1.5 px-4 py-2 rounded-xl transition-all ${
                    activeTab === 'anthropometrics'
                      ? 'bg-white text-slate-900 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  1. Child Anthropometrics (WHO Standards)
                </button>
                <button
                  onClick={() => setActiveTab('meals')}
                  className={`flex items-center gap-1.5 px-4 py-2 rounded-xl transition-all ${
                    activeTab === 'meals'
                      ? 'bg-white text-slate-900 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <Utensils className="w-3.5 h-3.5" /> 2. Indian Dishes Meal Log (20,000 Dataset)
                  {nutrientSummary && (
                    <span className="w-2 h-2 rounded-full bg-emerald-500 ml-1" />
                  )}
                </button>
              </div>
            </div>

            {activeTab === 'anthropometrics' && (
              <div className="max-w-xl mx-auto">
                <IntakeForm
                  onSubmit={handleIntakeSubmit}
                  loading={loading}
                />
              </div>
            )}

            {activeTab === 'meals' && (
              <div className="max-w-2xl mx-auto">
                <MealLogger
                  childId={childData?.child_id || 'CH-001'}
                  ageMonths={childData?.age_months || 60}
                  onSummaryReady={(s) => setNutrientSummary(s)}
                />
              </div>
            )}
          </div>
        )}

        {viewMode === 'parent' && assessment && (
          <ParentView
            assessment={assessment}
            onNewAssessment={() => setViewMode('intake')}
          />
        )}

        {viewMode === 'clinician' && assessment && (
          <ClinicianView
            assessment={assessment}
            onBackToIntake={() => setViewMode('intake')}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-400">
        Trust-First AI Nutrition Risk System • Explainable Fuzzy Inference with Auditable Trace Architecture
      </footer>
    </div>
  );
};
