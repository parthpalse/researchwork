import React, { useState } from 'react';
import { MealEntry, NutrientSummary } from '../lib/types';
import { DishSearch } from '../components/DishSearch';
import { NutrientChart } from '../components/NutrientChart';
import { logMeals } from '../lib/api';
import { Trash2, CheckCircle, Apple } from 'lucide-react';

interface MealLoggerProps {
  childId: string;
  ageMonths: number;
  onSummaryReady: (summary: NutrientSummary) => void;
}

export const MealLogger: React.FC<MealLoggerProps> = ({
  childId,
  ageMonths,
  onSummaryReady,
}) => {
  const [meals, setMeals] = useState<MealEntry[]>([]);
  const [nutrientSummary, setNutrientSummary] = useState<NutrientSummary | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleAddMeal = (entry: MealEntry) => {
    setMeals((prev) => [...prev, entry]);
    setSaveSuccess(false);
  };

  const handleRemoveMeal = (index: number) => {
    setMeals((prev) => prev.filter((_, i) => i !== index));
    setSaveSuccess(false);
  };

  const handleComputeAndSave = async () => {
    if (meals.length === 0) return;
    setSaving(true);
    try {
      const res = await logMeals(childId, meals);
      setNutrientSummary(res.nutrient_summary);
      onSummaryReady(res.nutrient_summary);
      setSaveSuccess(true);
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <DishSearch onAddMeal={handleAddMeal} />

      {/* Current Meal Log Table */}
      <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Apple className="w-5 h-5 text-emerald-600" />
            <h3 className="font-semibold text-sm text-slate-800">
              Logged Meals for Assessment ({meals.length})
            </h3>
          </div>
          {meals.length > 0 && (
            <button
              onClick={handleComputeAndSave}
              disabled={saving}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs rounded-xl shadow-sm transition-colors disabled:opacity-50"
            >
              {saving ? 'Analyzing Meals...' : 'Calculate Dietary Nutrients'}
            </button>
          )}
        </div>

        {meals.length === 0 ? (
          <p className="text-xs text-slate-400 py-3 text-center">
            No dishes added yet. Search Indian dishes above to build the child's daily dietary profile.
          </p>
        ) : (
          <div className="divide-y divide-slate-100">
            {meals.map((m, idx) => (
              <div key={idx} className="py-2.5 flex items-center justify-between text-xs">
                <div>
                  <div className="font-semibold text-slate-800">{m.dish_name}</div>
                  <div className="text-slate-400 text-[11px]">
                    {m.servings} serving(s) × {m.serving_size_g}g
                  </div>
                </div>
                <button
                  onClick={() => handleRemoveMeal(idx)}
                  className="text-slate-400 hover:text-rose-500 p-1 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}

        {saveSuccess && (
          <div className="flex items-center gap-1.5 text-xs text-emerald-700 font-medium bg-emerald-50 p-2.5 rounded-xl">
            <CheckCircle className="w-4 h-4" /> Dietary nutrients calculated and linked to child intake.
          </div>
        )}
      </div>

      {nutrientSummary && (
        <NutrientChart nutrientSummary={nutrientSummary} ageMonths={ageMonths} />
      )}
    </div>
  );
};
