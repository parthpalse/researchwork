import React, { useEffect, useState } from 'react';
import { ChildInput, NutrientSummary, AssessResponse, MealEntry, MealLogRecord, Me, ChildListItem } from './lib/types';
import { assessChild, saveChild, logMeals, getChildOverview, listChildren } from './lib/api';
import { IntakeForm } from './pages/IntakeForm';
import { MealLogger } from './pages/MealLogger';
import { ParentView } from './pages/ParentView';
import { ClinicianView } from './pages/ClinicianView';
import { ChildrenList } from './components/ChildrenList';
import { HeartPulse, User, ShieldAlert, Utensils, ClipboardList, Ruler, LogOut } from 'lucide-react';

type ViewMode = 'intake' | 'parent' | 'clinician';

// Remember the last child per account on this device, so a refresh does not lose them
const lastChildKey = (userId: string) => `nutriscan:lastChildId:${userId}`;

function readLastChildId(userId: string): string {
  try {
    return localStorage.getItem(lastChildKey(userId)) || '';
  } catch {
    return '';
  }
}

function rememberChildId(userId: string, childId: string) {
  try {
    localStorage.setItem(lastChildKey(userId), childId);
  } catch {
    // storage blocked (private mode): the app still works, it just won't remember
  }
}

interface AppProps {
  me: Me;
  onSignOut: () => void;
}

export const App: React.FC<AppProps> = ({ me, onSignOut }) => {
  const [viewMode, setViewMode] = useState<ViewMode>('intake');
  const [childData, setChildData] = useState<ChildInput | null>(null);
  const [meals, setMeals] = useState<MealEntry[]>([]);
  const [nutrientSummary, setNutrientSummary] = useState<NutrientSummary | null>(null);
  const [mealLogs, setMealLogs] = useState<MealLogRecord[]>([]);
  const [assessment, setAssessment] = useState<AssessResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [childList, setChildList] = useState<ChildListItem[]>([]);
  const [childListLoading, setChildListLoading] = useState(true);
  const [newChildCount, setNewChildCount] = useState(0);
  const [activeTab, setActiveTab] = useState<'anthropometrics' | 'meals'>('anthropometrics');

  const isClinician = me.role === 'clinician';

  const refreshChildList = () => {
    listChildren()
      .then(setChildList)
      .catch(() => {})
      .finally(() => setChildListLoading(false));
  };

  const openView = (mode: ViewMode) => {
    if (mode !== 'intake' && !assessment) {
      alert('Please run an assessment first: enter child details, add meals, then Run Assessment.');
      return;
    }
    setViewMode(mode);
    window.scrollTo({ top: 0 });
  };

  const loadChild = async (childId: string) => {
    const overview = await getChildOverview(childId);
    setChildData(overview.child);
    setMealLogs(overview.meal_logs);
    setAssessment(overview.latest_assessment);
    setNutrientSummary(null);
    setMeals([]);
    rememberChildId(me.user_id, childId);
    return overview;
  };

  // Load the children list, and reopen the last child after a refresh (silently)
  useEffect(() => {
    refreshChildList();
    const lastId = readLastChildId(me.user_id);
    if (lastId) loadChild(lastId).catch(() => {});
  }, [me.user_id]);

  const handleNewChild = () => {
    setChildData(null);
    setMeals([]);
    setMealLogs([]);
    setAssessment(null);
    setNutrientSummary(null);
    setError(null);
    setNewChildCount((n) => n + 1); // fresh form with a new random Child ID
    setActiveTab('anthropometrics');
  };

  const handleOpenChild = async (childId: string) => {
    setError(null);
    setLoading(true);
    try {
      const overview = await loadChild(childId);
      if (overview.latest_assessment) {
        setViewMode('parent');
      } else {
        setActiveTab('meals');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not open this child.');
    } finally {
      setLoading(false);
    }
  };

  // Step 1: save the child, then continue to meals (no assessment yet)
  const handleSaveDetails = async (data: ChildInput) => {
    setError(null);
    setLoading(true);
    try {
      await saveChild(data);
      if (childData?.child_id !== data.child_id) {
        setMeals([]);
        setMealLogs([]);
        setAssessment(null);
        setNutrientSummary(null);
      }
      setChildData(data);
      rememberChildId(me.user_id, data.child_id);
      refreshChildList();
      setActiveTab('meals');
      window.scrollTo({ top: 0 });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not save the child details.');
    } finally {
      setLoading(false);
    }
  };

  const handleMealsChange = (next: MealEntry[]) => {
    setMeals(next);
    setNutrientSummary(null); // list changed: last calculated summary no longer matches
  };

  // Step 2: save today's meals (if any) and run the assessment with them
  const handleRunAssessment = async () => {
    if (!childData) return;
    setError(null);
    setLoading(true);
    try {
      let summary: NutrientSummary | null = null;
      if (meals.length > 0) {
        summary = (await logMeals(childData.child_id, meals)).nutrient_summary;
      }
      const result = await assessChild(childData, summary);
      const overview = await getChildOverview(childData.child_id);
      setAssessment(result);
      setMealLogs(overview.meal_logs);
      setNutrientSummary(summary);
      setMeals([]);
      refreshChildList();
      setViewMode('parent');
      window.scrollTo({ top: 0 });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not run the assessment. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Parent view shows the meals used in this assessment (none if it was measurements-only)
  const mealsForAssessment = assessment?.trace.dietary_risk ? mealLogs.slice(0, 1) : [];

  // Parents never see the clinician audit; clinicians see all three
  const navItems: { mode: ViewMode; label: string; short: string; icon: React.ReactNode }[] = [
    { mode: 'intake', label: 'Intake & Meals', short: 'Intake', icon: <ClipboardList className="w-5 h-5 sm:w-3.5 sm:h-3.5" /> },
    { mode: 'parent', label: 'Parent View', short: 'Parent', icon: <User className="w-5 h-5 sm:w-3.5 sm:h-3.5" /> },
    ...(isClinician
      ? [{ mode: 'clinician' as ViewMode, label: 'Clinician Audit', short: 'Clinician', icon: <ShieldAlert className="w-5 h-5 sm:w-3.5 sm:h-3.5" /> }]
      : []),
  ];

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
                <span className="capitalize">{me.role}</span> · {me.email}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
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
          <button
            onClick={onSignOut}
            className="flex items-center gap-1.5 p-2 sm:px-3 sm:py-2 text-xs font-semibold text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded-xl transition-colors"
            title="Sign out"
          >
            <LogOut className="w-4 h-4" />
            <span className="hidden sm:inline">Sign out</span>
          </button>
          </div>
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

            {error && (
              <div className="max-w-xl mx-auto text-xs text-rose-700 bg-rose-50 border border-rose-100 p-3 rounded-xl">
                {error}
              </div>
            )}

            {activeTab === 'anthropometrics' && (
              <div className="max-w-xl mx-auto space-y-4">
                {/* Parent: own children. Clinician: all patients */}
                <ChildrenList
                  role={me.role}
                  items={childList}
                  activeChildId={childData?.child_id ?? null}
                  loading={childListLoading}
                  onOpen={handleOpenChild}
                  onNewChild={handleNewChild}
                />

                <IntakeForm
                  key={childData?.child_id ?? `new-child-${newChildCount}`}
                  initialValues={childData ?? undefined}
                  onSubmit={handleSaveDetails}
                  loading={loading}
                  submitLabel="Save & Continue to Meals"
                  loadingLabel="Saving..."
                />
              </div>
            )}

            {activeTab === 'meals' && (
              <div className="max-w-2xl mx-auto">
                {childData ? (
                  <div className="space-y-4">
                    <div className="text-xs text-slate-500 text-center">
                      Logging meals for <strong className="text-slate-700">{childData.child_id}</strong> ·{' '}
                      {(childData.age_months / 12).toFixed(1)} years
                    </div>
                    <MealLogger
                      ageMonths={childData.age_months}
                      meals={meals}
                      onMealsChange={handleMealsChange}
                      nutrientSummary={nutrientSummary}
                      onRunAssessment={handleRunAssessment}
                      assessing={loading}
                    />
                  </div>
                ) : (
                  <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 text-center space-y-3">
                    <p className="text-sm text-slate-600">
                      First save the child's details, so the meals are stored for the right child.
                    </p>
                    <button
                      onClick={() => setActiveTab('anthropometrics')}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold"
                    >
                      Go to Child Details
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {viewMode === 'parent' && assessment && (
          <ParentView
            key={assessment.trace_id}
            assessment={assessment}
            mealLogs={mealsForAssessment}
            ageMonths={childData?.age_months ?? 60}
            onLogMeals={() => {
              setViewMode('intake');
              setActiveTab('meals');
              window.scrollTo({ top: 0 });
            }}
            onNewAssessment={() => {
              setViewMode('intake');
              setActiveTab('anthropometrics');
              window.scrollTo({ top: 0 });
            }}
          />
        )}

        {viewMode === 'clinician' && assessment && (
          <ClinicianView
            key={assessment.trace_id}
            assessment={assessment}
            child={childData}
            mealLogs={mealLogs}
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
        <div className={`grid ${navItems.length === 3 ? 'grid-cols-3' : 'grid-cols-2'}`}>
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
