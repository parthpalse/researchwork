import React, { useState } from 'react';
import { ChildInput, GrowthTrend, Sex } from '../lib/types';
import { Baby, Activity, Scale, Ruler, HeartPulse } from 'lucide-react';

interface IntakeFormProps {
  initialValues?: Partial<ChildInput>;
  onSubmit: (data: ChildInput) => void;
  loading?: boolean;
}

export const IntakeForm: React.FC<IntakeFormProps> = ({
  initialValues,
  onSubmit,
  loading = false,
}) => {
  const [childId, setChildId] = useState(initialValues?.child_id || `CH-${Math.floor(1000 + Math.random() * 9000)}`);
  const [ageMonths, setAgeMonths] = useState(initialValues?.age_months || 60);
  const [sex, setSex] = useState<Sex>(initialValues?.sex || 'M');
  const [weightKg, setWeightKg] = useState(initialValues?.weight_kg || 16.5);
  const [heightCm, setHeightCm] = useState(initialValues?.height_cm || 105.0);
  const [muacCm, setMuacCm] = useState(initialValues?.muac_cm || 13.5);
  const [growthTrend, setGrowthTrend] = useState<GrowthTrend>(initialValues?.growth_trend || 'stable');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      child_id: childId,
      age_months: Number(ageMonths),
      sex,
      weight_kg: Number(weightKg),
      height_cm: Number(heightCm),
      muac_cm: Number(muacCm),
      growth_trend: growthTrend,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white p-6 rounded-3xl shadow-sm border border-slate-100 space-y-6">
      <div className="flex items-center gap-3 border-b border-slate-100 pb-4">
        <div className="p-2.5 bg-emerald-50 text-emerald-600 rounded-2xl">
          <Baby className="w-6 h-6" />
        </div>
        <div>
          <h2 className="text-base font-bold text-slate-800">Child Assessment Intake</h2>
          <p className="text-xs text-slate-500">
            Ages 4–10 years (48–120 months) • Standardized WHO Anthropometrics
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
        {/* Child ID */}
        <div>
          <label className="block font-medium text-slate-700 mb-1">Child Patient ID</label>
          <input
            type="text"
            required
            value={childId}
            onChange={(e) => setChildId(e.target.value)}
            className="w-full px-3 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
          />
        </div>

        {/* Age */}
        <div>
          <label className="block font-medium text-slate-700 mb-1">
            Age (Months: 48–120, i.e. 4–10 yrs)
          </label>
          <input
            type="number"
            min="48"
            max="120"
            required
            value={ageMonths}
            onChange={(e) => setAgeMonths(Number(e.target.value))}
            className="w-full px-3 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
          />
          <span className="text-[11px] text-slate-400">
            approx. {(ageMonths / 12).toFixed(1)} years old
          </span>
        </div>

        {/* Sex */}
        <div>
          <label className="block font-medium text-slate-700 mb-1">Biological Sex</label>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => setSex('M')}
              className={`py-2 text-center rounded-xl font-semibold border transition-all ${
                sex === 'M'
                  ? 'bg-emerald-50 text-emerald-800 border-emerald-300 shadow-sm'
                  : 'bg-white text-slate-600 border-slate-200'
              }`}
            >
              Male (Boy)
            </button>
            <button
              type="button"
              onClick={() => setSex('F')}
              className={`py-2 text-center rounded-xl font-semibold border transition-all ${
                sex === 'F'
                  ? 'bg-emerald-50 text-emerald-800 border-emerald-300 shadow-sm'
                  : 'bg-white text-slate-600 border-slate-200'
              }`}
            >
              Female (Girl)
            </button>
          </div>
        </div>

        {/* Growth Trend */}
        <div>
          <label className="block font-medium text-slate-700 mb-1">Recent Growth Trend</label>
          <select
            value={growthTrend}
            onChange={(e) => setGrowthTrend(e.target.value as GrowthTrend)}
            className="w-full px-3 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 bg-white"
          >
            <option value="improving">Improving (Gaining steadily)</option>
            <option value="stable">Stable (Consistent weight)</option>
            <option value="declining">Declining (Losing or plateauing)</option>
          </select>
        </div>

        {/* Height */}
        <div>
          <label className="flex items-center gap-1.5 font-medium text-slate-700 mb-1">
            <Ruler className="w-3.5 h-3.5 text-slate-400" /> Height (cm)
          </label>
          <input
            type="number"
            step="0.5"
            min="65"
            max="150"
            required
            value={heightCm}
            onChange={(e) => setHeightCm(Number(e.target.value))}
            className="w-full px-3 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
          />
        </div>

        {/* Weight */}
        <div>
          <label className="flex items-center gap-1.5 font-medium text-slate-700 mb-1">
            <Scale className="w-3.5 h-3.5 text-slate-400" /> Weight (kg)
          </label>
          <input
            type="number"
            step="0.1"
            min="5"
            max="60"
            required
            value={weightKg}
            onChange={(e) => setWeightKg(Number(e.target.value))}
            className="w-full px-3 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
          />
        </div>

        {/* MUAC */}
        <div className="md:col-span-2">
          <label className="flex items-center gap-1.5 font-medium text-slate-700 mb-1">
            <Activity className="w-3.5 h-3.5 text-slate-400" /> Mid-Upper Arm Circumference (MUAC in cm)
          </label>
          <input
            type="number"
            step="0.1"
            min="8"
            max="25"
            required
            value={muacCm}
            onChange={(e) => setMuacCm(Number(e.target.value))}
            className="w-full px-3 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
          />
          <div className="flex gap-4 mt-1.5 text-[11px] text-slate-500">
            <span>&lt; 11.5 cm: Priority</span>
            <span>11.5–12.5 cm: Observation</span>
            <span>&gt; 12.5 cm: Steady</span>
          </div>
        </div>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full flex items-center justify-center gap-2 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-2xl text-xs shadow-md shadow-emerald-600/10 transition-colors disabled:opacity-50"
      >
        <HeartPulse className="w-4 h-4" />
        {loading ? 'Evaluating Risk Profile...' : 'Run Nutrition Risk Assessment'}
      </button>
    </form>
  );
};
