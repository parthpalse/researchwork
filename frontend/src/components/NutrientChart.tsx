import React from 'react';
import { NutrientSummary } from '../lib/types';

interface NutrientChartProps {
  nutrientSummary: NutrientSummary;
  ageMonths: number;
}

export const NutrientChart: React.FC<NutrientChartProps> = ({ nutrientSummary, ageMonths }) => {
  // Approximate standard Indian ICMR daily values for ages 4-10
  const isOlder = ageMonths >= 73;
  const targetEnergy = isOlder ? 1700 : 1360;
  const targetProtein = isOlder ? 23.0 : 16.0;
  const targetIron = isOlder ? 15.0 : 11.0;
  const targetSugarMax = 30.0; // WHO maximum free sugars benchmark

  const energyPct = Math.min(Math.round((nutrientSummary.total_energy_kcal / targetEnergy) * 100), 150);
  const proteinPct = Math.min(Math.round((nutrientSummary.total_protein_g / targetProtein) * 100), 150);
  const ironPct = Math.min(Math.round((nutrientSummary.total_iron_mg / targetIron) * 100), 150);
  const sugarPct = Math.min(Math.round((nutrientSummary.total_sugar_g / targetSugarMax) * 100), 150);

  const getBarColor = (pct: number, isNegative = false) => {
    if (isNegative) {
      return pct > 100 ? 'bg-amber-400' : 'bg-emerald-500';
    }
    if (pct < 60) return 'bg-amber-400';
    if (pct <= 120) return 'bg-emerald-500';
    return 'bg-blue-400';
  };

  return (
    <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-800">Daily Nutritional Snapshot (ICMR RDA)</h3>
        <span className="text-xs text-slate-500">Ages {isOlder ? '7–10' : '4–6'} Target</span>
      </div>

      <div className="space-y-3 text-xs">
        {/* Energy */}
        <div>
          <div className="flex justify-between mb-1">
            <span className="font-medium text-slate-700">Energy (Calories)</span>
            <span className="text-slate-500">
              {nutrientSummary.total_energy_kcal} / {targetEnergy} kcal ({energyPct}%)
            </span>
          </div>
          <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
            <div
              className={`h-full ${getBarColor(energyPct)} transition-all duration-500`}
              style={{ width: `${Math.min(energyPct, 100)}%` }}
            />
          </div>
        </div>

        {/* Protein */}
        <div>
          <div className="flex justify-between mb-1">
            <span className="font-medium text-slate-700">Protein</span>
            <span className="text-slate-500">
              {nutrientSummary.total_protein_g} / {targetProtein} g ({proteinPct}%)
            </span>
          </div>
          <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
            <div
              className={`h-full ${getBarColor(proteinPct)} transition-all duration-500`}
              style={{ width: `${Math.min(proteinPct, 100)}%` }}
            />
          </div>
        </div>

        {/* Iron */}
        <div>
          <div className="flex justify-between mb-1">
            <span className="font-medium text-slate-700">Iron</span>
            <span className="text-slate-500">
              {nutrientSummary.total_iron_mg} / {targetIron} mg ({ironPct}%)
            </span>
          </div>
          <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
            <div
              className={`h-full ${getBarColor(ironPct)} transition-all duration-500`}
              style={{ width: `${Math.min(ironPct, 100)}%` }}
            />
          </div>
        </div>

        {/* Sugar */}
        <div>
          <div className="flex justify-between mb-1">
            <span className="font-medium text-slate-700">Free Sugars (WHO Upper Limit)</span>
            <span className="text-slate-500">
              {nutrientSummary.total_sugar_g} / {targetSugarMax} g ({sugarPct}%)
            </span>
          </div>
          <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
            <div
              className={`h-full ${getBarColor(sugarPct, true)} transition-all duration-500`}
              style={{ width: `${Math.min(sugarPct, 100)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Glycemic Index & NOVA info */}
      <div className="pt-3 border-t border-slate-100 grid grid-cols-2 gap-2 text-center text-xs">
        <div className="bg-slate-50 p-2 rounded-lg">
          <div className="text-slate-400 text-[10px] uppercase font-semibold">Avg Glycemic Index</div>
          <div className="font-bold text-slate-700 text-sm mt-0.5">
            {nutrientSummary.avg_glycemic_index > 0 ? nutrientSummary.avg_glycemic_index : 'N/A'}
          </div>
        </div>
        <div className="bg-slate-50 p-2 rounded-lg">
          <div className="text-slate-400 text-[10px] uppercase font-semibold">Minimally Processed (NOVA 1)</div>
          <div className="font-bold text-slate-700 text-sm mt-0.5">
            {nutrientSummary.nova_breakdown?.[1] || nutrientSummary.nova_breakdown?.['1'] || 0}%
          </div>
        </div>
      </div>
    </div>
  );
};
