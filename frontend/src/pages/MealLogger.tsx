import React from 'react';
import { MealEntry, NutrientSummary } from '../lib/types';
import { DishSearch } from '../components/DishSearch';
import { FoodCamera } from '../components/FoodCamera';
import { PackagedFoodLookup } from '../components/PackagedFoodLookup';
import { NutrientChart } from '../components/NutrientChart';
import { Trash2, Apple, HeartPulse } from 'lucide-react';

interface MealLoggerProps {
  ageMonths: number;
  meals: MealEntry[];
  onMealsChange: (meals: MealEntry[]) => void;
  // Summary of the meals as last saved (null when the list changed since)
  nutrientSummary: NutrientSummary | null;
  onRunAssessment: () => void;
  assessing: boolean;
}

export const MealLogger: React.FC<MealLoggerProps> = ({
  ageMonths,
  meals,
  onMealsChange,
  nutrientSummary,
  onRunAssessment,
  assessing,
}) => {
  const handleAddMeal = (entry: MealEntry) => onMealsChange([...meals, entry]);
  const handleAddScannedMeals = (entries: MealEntry[]) => onMealsChange([...meals, ...entries]);
  const handleRemoveMeal = (index: number) => onMealsChange(meals.filter((_, i) => i !== index));

  return (
    <div className="space-y-6">
      <FoodCamera ageMonths={ageMonths} onAddMeals={handleAddScannedMeals} />

      <PackagedFoodLookup ageMonths={ageMonths} onAddMeal={handleAddMeal} />

      <DishSearch onAddMeal={handleAddMeal} />

      {/* Current Meal Log + final step */}
      <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 space-y-4">
        <div className="flex items-center gap-2">
          <Apple className="w-5 h-5 text-emerald-600" />
          <h3 className="font-semibold text-sm text-slate-800">
            Today's Meals ({meals.length})
          </h3>
        </div>

        {meals.length === 0 ? (
          <p className="text-xs text-slate-400 py-3 text-center">
            No dishes added yet. Scan a photo, enter a barcode or search dishes above. You can also
            run the assessment with body measurements only.
          </p>
        ) : (
          <div className="divide-y divide-slate-100">
            {meals.map((m, idx) => (
              <div key={idx} className="py-2.5 flex items-center justify-between gap-3 text-xs">
                <div className="min-w-0">
                  <div className="font-semibold text-slate-800">{m.dish_name}</div>
                  <div className="text-slate-400 text-[11px]">
                    {m.servings} serving(s) × {m.serving_size_g}g
                  </div>
                </div>
                <button
                  onClick={() => handleRemoveMeal(idx)}
                  className="text-slate-400 hover:text-rose-500 p-1 transition-colors shrink-0"
                  title="Remove"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}

        <button
          onClick={onRunAssessment}
          disabled={assessing}
          className="w-full flex items-center justify-center gap-2 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-2xl text-xs shadow-md shadow-emerald-600/10 transition-colors disabled:opacity-50"
        >
          <HeartPulse className="w-4 h-4" />
          {assessing
            ? 'Saving meals & evaluating...'
            : meals.length > 0
              ? `Save ${meals.length} meal${meals.length === 1 ? '' : 's'} & Run Assessment`
              : 'Run Assessment (measurements only)'}
        </button>
      </div>

      {nutrientSummary && (
        <NutrientChart nutrientSummary={nutrientSummary} ageMonths={ageMonths} />
      )}
    </div>
  );
};
