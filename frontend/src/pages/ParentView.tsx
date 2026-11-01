import React from 'react';
import { AssessResponse, MealLogRecord } from '../lib/types';
import { RiskBadge } from '../components/RiskBadge';
import { MealHistory } from '../components/MealHistory';
import { Sparkles, HeartHandshake, ArrowRight, ShieldCheck, Salad, Utensils } from 'lucide-react';

interface ParentViewProps {
  assessment: AssessResponse;
  mealLogs: MealLogRecord[];
  ageMonths: number;
  onNewAssessment?: () => void;
  onLogMeals?: () => void;
}

// Engine field names -> words a parent understands
const NUTRIENT_WORDS: Record<string, string> = {
  protein: 'protein (dal, curd, paneer, eggs, sprouts)',
  iron: 'iron (green leafy vegetables, ragi, jaggery, rajma)',
  protein_pct_rda: 'protein',
  iron_pct_rda: 'iron',
  sugar_g: 'sweets and sugary drinks',
  gi_score: 'quick-digesting foods like white bread and sweets',
  nova_score: 'packaged and processed snacks',
};

const word = (field: string) => NUTRIENT_WORDS[field] || field.replace(/_/g, ' ');

export const ParentView: React.FC<ParentViewProps> = ({
  assessment,
  mealLogs,
  ageMonths,
  onNewAssessment,
  onLogMeals,
}) => {
  const { trace, explanation } = assessment;
  const dietary = trace.dietary_risk;
  const foodNotes = [
    ...(dietary?.nutrient_gaps || []).map((f) => `A little more ${word(f)} would help.`),
    ...(dietary?.excess_nutrients || []).map((f) => `Try a little less ${word(f)}.`),
  ];

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-br from-emerald-500 to-teal-600 rounded-3xl p-6 text-white shadow-lg shadow-emerald-500/10 space-y-3">
        <div className="flex justify-between items-start">
          <span className="text-xs font-semibold uppercase tracking-wider bg-white/20 px-3 py-1 rounded-full backdrop-blur-sm">
            Child Nutrition Summary
          </span>
          <span className="text-xs opacity-80">
            ID: {trace.child_id}
          </span>
        </div>

        <h1 className="text-2xl font-bold tracking-tight">
          Every Child's Growth is a Journey
        </h1>
        <p className="text-xs text-emerald-50 leading-relaxed max-w-lg">
          We combine medical growth standards with everyday nutrition guidance to support
          your family with calm, actionable next steps.
        </p>
      </div>

      {/* Primary Communication Card */}
      <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-100 space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4">
          <div>
            <div className="text-xs text-slate-400 font-medium">Growth Health Status</div>
            <div className="mt-1">
              <RiskBadge level={trace.final_risk_level} />
            </div>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-emerald-700 bg-emerald-50 px-3 py-1.5 rounded-full font-medium">
            <ShieldCheck className="w-4 h-4" /> Clinically Audited Trace
          </div>
        </div>

        {/* Supportive Message */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-slate-800 font-semibold text-sm">
            <HeartHandshake className="w-5 h-5 text-emerald-600" />
            <h3>Personalized Nutrition Guidance</h3>
          </div>
          <p className="text-slate-600 text-sm leading-relaxed bg-slate-50 p-4 rounded-2xl border border-slate-100">
            {explanation.parent_message}
          </p>
        </div>

        {/* Suggested Next Step */}
        <div className="bg-amber-50/70 border border-amber-200/80 rounded-2xl p-5 space-y-2">
          <div className="flex items-center gap-2 text-amber-900 font-semibold text-sm">
            <Sparkles className="w-5 h-5 text-amber-600" />
            <h3>Small, Positive Step for Today</h3>
          </div>
          <p className="text-amber-800 text-xs leading-relaxed">
            {explanation.suggested_next_step}
          </p>
        </div>

        {/* Food notes from the logged meals */}
        {dietary && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-slate-800 font-semibold text-sm">
              <Salad className="w-5 h-5 text-emerald-600" />
              <h3>What We Noticed in the Meals</h3>
            </div>
            {foodNotes.length > 0 ? (
              <ul className="space-y-1.5">
                {foodNotes.map((note) => (
                  <li key={note} className="text-xs text-slate-600 bg-slate-50 border border-slate-100 rounded-xl px-3 py-2">
                    {note}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-slate-600 bg-emerald-50/60 border border-emerald-100 rounded-xl px-3 py-2">
                The meals look well balanced. Keep it up!
              </p>
            )}
          </div>
        )}

        {/* Calming Action Buttons */}
        <div className="pt-2 flex flex-col sm:flex-row gap-3">
          {onLogMeals && (
            <button
              onClick={onLogMeals}
              className="flex-1 flex items-center justify-center gap-2 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-2xl text-xs font-semibold transition-colors shadow-sm"
            >
              <Utensils className="w-4 h-4" /> Log Today's Meals
            </button>
          )}
          {onNewAssessment && (
            <button
              onClick={onNewAssessment}
              className="flex-1 flex items-center justify-center gap-2 py-3 bg-slate-900 hover:bg-slate-800 text-white rounded-2xl text-xs font-semibold transition-colors shadow-sm"
            >
              Update Measurements <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      <MealHistory
        mealLogs={mealLogs}
        ageMonths={ageMonths}
        title="Meals Used in This Check"
        emptyText="No meals were logged for this check yet. Log today's meals to get food-specific guidance."
      />
    </div>
  );
};
