import React, { useState } from 'react';
import { ChildInput, NutrientSummary, AssessResponse } from './lib/types';
import { assessChild } from './lib/api';
import { IntakeForm } from './pages/IntakeForm';
import { MealLogger } from './pages/MealLogger';
import { ParentView } from './pages/ParentView';
import { ClinicianView } from './pages/ClinicianView';
import { HeartPulse, User, ShieldAlert, Utensils, ClipboardList, Ruler } from 'lucide-react';

type ViewMode = 'intake' | 'parent' | 'clinician';

export const App: React.FC = () => {
  const [viewMode, setViewMode] = useState<ViewMode>('intake');
  const [childData, setChildData] = useState<ChildInput | null>(null);
  const [nutrientSummary, setNutrientSummary] = useState<NutrientSummary | null>(null);
  const [assessment, setAssessment] = useState<AssessResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'anthropometrics' | 'meals'>('anthropometrics');

  const openView = (mode: ViewMode) => {
    if (mode !== 'intake' && !assessment) {
      alert('Please run an assessment first via the intake form.');
      return;
    }
    setViewMode(mode);
    window.scrollTo({ top: 0 });
  };

  const navItems: { mode: ViewMode; label: string; short: string; icon: React.ReactNode }[] = [
    { mode: 'intake', label: 'Intake & Meals', short: 'Intake', icon: <ClipboardList className="w-5 h-5 sm:w-3.5 sm:h-3.5" /> },
    { mode: 'parent', label: 'Parent View', short: 'Parent', icon: <User className="w-5 h-5 sm:w-3.5 sm:h-3.5" /> },
    { mode: 'clinician', label: 'Clinician Audit', short: 'Clinician', icon: <ShieldAlert className="w-5 h-5 sm:w-3.5 sm:h-3.5" /> },
  ];

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
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs pt-[env(safe-area-inset-top)]">
        <div className="max-w-5xl mx-auto px-4 h-14 sm:h-16 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="p-2 bg-emerald-600 text-white rounded-xl shadow-xs shrink-0">
              <HeartPulse className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <span className="font-bold text-sm tracking-tight text-slate-900 block leading-tight truncate">
                <span className="sm:hidden">NutriScan</span>
                <span className="hidden sm:inline">Trust-First AI Nutrition Risk System</span>
              </span>
              <span className="text-[11px] text-slate-500 block truncate">
                <span className="sm:hidden">Child nutrition risk checks</span>
                <span className="hidden sm:inline">TY Mini Project • Hand-Rolled Fuzzy Logic + Auditable Trace</span>
              </span>
            </div>
          </div>

          {/* View tabs: top bar on tablets/laptops; phones use the bottom bar below */}
          <nav className="hidden sm:flex items-center gap-1 bg-slate-100 p-1 rounded-2xl text-xs font-semibold shrink-0">
            {navItems.map((item) => (
              <button
                key={item.mode}
                onClick={() => openView(item.mode)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl transition-all ${
                  viewMode === item.mode
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {item.icon} {item.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Main Content Area (extra bottom space on phones for the tab bar) */}
      <main className="flex-1 max-w-5xl w-full mx-auto px-4 pt-4 pb-28 sm:py-8">
        {viewMode === 'intake' && (
          <div className="space-y-4 sm:space-y-6">
            {/* Step navigation tabs */}
            <div className="flex justify-center">
              <div className="grid grid-cols-2 sm:inline-flex w-full sm:w-auto bg-slate-200/80 p-1 rounded-2xl text-xs font-semibold gap-1">
                <button
                  onClick={() => setActiveTab('anthropometrics')}
                  className={`flex items-center justify-center gap-1.5 px-3 sm:px-4 py-2.5 sm:py-2 rounded-xl transition-all ${
                    activeTab === 'anthropometrics'
                      ? 'bg-white text-slate-900 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <Ruler className="w-3.5 h-3.5 shrink-0" />
                  <span className="sm:hidden">1. Child Details</span>
                  <span className="hidden sm:inline">1. Child Anthropometrics (WHO Standards)</span>
                </button>
                <button
                  onClick={() => setActiveTab('meals')}
                  className={`flex items-center justify-center gap-1.5 px-3 sm:px-4 py-2.5 sm:py-2 rounded-xl transition-all ${
                    activeTab === 'meals'
                      ? 'bg-white text-slate-900 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <Utensils className="w-3.5 h-3.5 shrink-0" />
                  <span className="sm:hidden">2. Meals</span>
                  <span className="hidden sm:inline">2. Indian Dishes Meal Log (20,000 Dataset)</span>
                  {nutrientSummary && (
                    <span className="w-2 h-2 rounded-full bg-emerald-500 ml-1 shrink-0" />
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

      {/* Footer (tablets/laptops; on phones the bottom tab bar takes this space) */}
      <footer className="hidden sm:block border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-400">
        Trust-First AI Nutrition Risk System • Explainable Fuzzy Inference with Auditable Trace Architecture
      </footer>

      {/* Bottom tab bar on phones, like a native app */}
      <nav className="sm:hidden fixed bottom-0 inset-x-0 z-30 bg-white/95 backdrop-blur border-t border-slate-200 pb-[env(safe-area-inset-bottom)]">
        <div className="grid grid-cols-3">
          {navItems.map((item) => {
            const active = viewMode === item.mode;
            const locked = item.mode !== 'intake' && !assessment;
            return (
              <button
                key={item.mode}
                onClick={() => openView(item.mode)}
                className={`flex flex-col items-center gap-0.5 py-2.5 text-[11px] font-semibold transition-colors ${
                  active ? 'text-emerald-700' : locked ? 'text-slate-300' : 'text-slate-500'
                }`}
              >
                {item.icon}
                {item.short}
              </button>
            );
          })}
        </div>
      </nav>
    </div>
  );
};
