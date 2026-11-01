import React from 'react';
import { MealLogRecord } from '../lib/types';
import { NutrientChart } from './NutrientChart';
import { UtensilsCrossed } from 'lucide-react';

interface MealHistoryProps {
  mealLogs: MealLogRecord[];
  ageMonths: number;
  title: string;
  emptyText: string;
  // Clinicians also see when each log was saved and older logs
  showOlderLogs?: boolean;
}

function formatWhen(iso: string): string {
  const d = new Date(iso);
  return isNaN(d.getTime()) ? iso : d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}

export const MealHistory: React.FC<MealHistoryProps> = ({
  mealLogs,
  ageMonths,
  title,
  emptyText,
  showOlderLogs = false,
}) => {
  const latest = mealLogs[0];
  const older = showOlderLogs ? mealLogs.slice(1) : [];

  return (
    <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 space-y-4">
      <div className="flex items-center gap-2">
        <UtensilsCrossed className="w-5 h-5 text-emerald-600" />
        <h3 className="font-semibold text-sm text-slate-800">{title}</h3>
      </div>

      {!latest ? (
        <p className="text-xs text-slate-400">{emptyText}</p>
      ) : (
        <>
          <div className="text-[11px] text-slate-400">Logged {formatWhen(latest.created_at)}</div>
          <div className="divide-y divide-slate-100 border border-slate-100 rounded-xl">
            {latest.meals.map((m, i) => (
              <div key={i} className="px-3 py-2 flex items-center justify-between gap-3 text-xs">
                <span className="font-medium text-slate-700 min-w-0">{m.dish_name}</span>
                <span className="text-slate-400 whitespace-nowrap shrink-0">
                  {Math.round(m.servings * m.serving_size_g)} g
                </span>
              </div>
            ))}
          </div>
        </>
      )}

      {latest?.nutrient_summary && (
        <NutrientChart nutrientSummary={latest.nutrient_summary} ageMonths={ageMonths} />
      )}

      {older.length > 0 && (
        <div className="space-y-1.5">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Earlier logs</div>
          {older.map((log) => (
            <div key={log.id} className="flex items-start justify-between gap-3 text-[11px] text-slate-500">
              <span className="min-w-0">{log.meals.map((m) => m.dish_name).join(', ')}</span>
              <span className="whitespace-nowrap shrink-0">
                {log.nutrient_summary ? `${Math.round(log.nutrient_summary.total_energy_kcal)} kcal · ` : ''}
                {formatWhen(log.created_at)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
