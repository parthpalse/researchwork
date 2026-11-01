import React, { useEffect, useRef, useState } from 'react';
import { FoodAlert, FoodScanResult, MealEntry, MealTotals, ScanDish } from '../lib/types';
import { identifyFood, getScanSummary } from '../lib/api';
import { Camera, Upload, Loader2, Sparkles, Info, Plus, X } from 'lucide-react';

// Photos are shrunk before upload: faster scans and well under the server's size limit
const MAX_IMAGE_SIDE = 640;
const JPEG_QUALITY = 0.8;

interface FoodCameraProps {
  ageMonths: number;
  onAddMeals: (meals: MealEntry[]) => void;
}

interface ScanRow {
  key: string;
  foodName: string;
  dish: ScanDish;
  grams: number;
  selected: boolean;
  confidence: number;
  possibleMatch: boolean;
}

function resizeImage(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      const scale = Math.min(1, MAX_IMAGE_SIDE / Math.max(img.width, img.height));
      const canvas = document.createElement('canvas');
      canvas.width = Math.round(img.width * scale);
      canvas.height = Math.round(img.height * scale);
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        URL.revokeObjectURL(url);
        reject(new Error('Could not read this photo.'));
        return;
      }
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(url);
      resolve(canvas.toDataURL('image/jpeg', JPEG_QUALITY));
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error('This photo format is not supported. Please use a JPG or PNG.'));
    };
    img.src = url;
  });
}

function rowsFromResult(result: FoodScanResult): ScanRow[] {
  const rows: ScanRow[] = [];
  result.items.forEach((item, i) => {
    item.components.forEach((comp, j) => {
      if (!comp.dish) return;
      rows.push({
        key: `${i}-${j}`,
        foodName: item.name,
        dish: comp.dish,
        grams: comp.grams,
        selected: true,
        confidence: comp.confidence,
        possibleMatch: comp.possible_match,
      });
    });
  });
  return rows;
}

const AlertCard: React.FC<{ alert: FoodAlert }> = ({ alert }) => {
  const isAllergen = alert.type === 'allergen';
  return (
    <div
      className={`flex gap-2 p-2.5 rounded-xl text-xs ${
        isAllergen ? 'bg-sky-50 text-sky-900' : 'bg-amber-50 text-amber-900'
      }`}
    >
      <Info className="w-4 h-4 shrink-0 mt-0.5" />
      <span>{alert.message}</span>
    </div>
  );
};

export const FoodCamera: React.FC<FoodCameraProps> = ({ ageMonths, onAddMeals }) => {
  const cameraInput = useRef<HTMLInputElement>(null);
  const uploadInput = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<FoodScanResult | null>(null);
  const [rows, setRows] = useState<ScanRow[]>([]);
  const [totals, setTotals] = useState<MealTotals | null>(null);
  const [alerts, setAlerts] = useState<FoodAlert[]>([]);
  const [rowsEdited, setRowsEdited] = useState(false);

  // Recalculate totals and alerts on the server after the parent edits the list
  useEffect(() => {
    if (!rowsEdited) return;
    const handler = setTimeout(() => {
      const items = rows
        .filter((r) => r.selected && r.grams > 0)
        .map((r) => ({ dish_id: r.dish.record_id, grams: r.grams }));
      if (items.length === 0) {
        setTotals(null);
        setAlerts([]);
        return;
      }
      getScanSummary(items, ageMonths)
        .then((res) => {
          setTotals(res.totals);
          setAlerts(res.alerts);
        })
        .catch(() => {});
    }, 400);
    return () => clearTimeout(handler);
  }, [rows, rowsEdited, ageMonths]);

  const handleFile = async (file: File | undefined) => {
    if (!file) return;
    setError(null);
    setResult(null);
    setRows([]);
    setRowsEdited(false);
    setScanning(true);
    try {
      const dataUrl = await resizeImage(file);
      setPreview(dataUrl);
      const res = await identifyFood(dataUrl.split(',')[1], 'image/jpeg', ageMonths);
      setResult(res);
      setRows(rowsFromResult(res));
      setTotals(res.totals);
      setAlerts(res.alerts);
      if (!res.is_food) {
        setError("We couldn't see any food in this photo. Try a closer, brighter picture.");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong. Please try again.');
    } finally {
      setScanning(false);
    }
  };

  const updateRow = (key: string, change: Partial<ScanRow>) => {
    setRows((prev) => prev.map((r) => (r.key === key ? { ...r, ...change } : r)));
    setRowsEdited(true);
  };

  const handleAdd = () => {
    const meals: MealEntry[] = rows
      .filter((r) => r.selected && r.grams > 0)
      .map((r) => ({
        dish_id: r.dish.record_id,
        dish_name: r.dish.dish_name,
        servings: 1,
        serving_size_g: r.grams,
      }));
    if (meals.length === 0) return;
    onAddMeals(meals);
    handleReset();
  };

  const handleReset = () => {
    setPreview(null);
    setResult(null);
    setRows([]);
    setTotals(null);
    setAlerts([]);
    setError(null);
    setRowsEdited(false);
  };

  const selectedCount = rows.filter((r) => r.selected && r.grams > 0).length;

  return (
    <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-emerald-600" />
          <h3 className="font-semibold text-slate-800 text-sm">Scan a Meal Photo</h3>
        </div>
        {(preview || result) && !scanning && (
          <button onClick={handleReset} className="text-slate-400 hover:text-slate-600 p-1" title="Clear">
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      <input
        ref={cameraInput}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={(e) => {
          handleFile(e.target.files?.[0]);
          e.target.value = '';
        }}
      />
      <input
        ref={uploadInput}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="hidden"
        onChange={(e) => {
          handleFile(e.target.files?.[0]);
          e.target.value = '';
        }}
      />

      {!preview && (
        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={() => cameraInput.current?.click()}
            className="flex items-center justify-center gap-2 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold shadow-sm transition-colors"
          >
            <Camera className="w-4 h-4" /> Take Photo
          </button>
          <button
            onClick={() => uploadInput.current?.click()}
            className="flex items-center justify-center gap-2 py-3 border border-emerald-200 text-emerald-700 hover:bg-emerald-50 rounded-xl text-xs font-semibold transition-colors"
          >
            <Upload className="w-4 h-4" /> Upload Photo
          </button>
        </div>
      )}

      {preview && (
        <div className="flex gap-4 items-start">
          <img src={preview} alt="Meal" className="w-28 h-28 object-cover rounded-xl border border-slate-100" />
          <div className="flex-1 text-xs text-slate-500 space-y-1">
            {scanning && (
              <div className="flex items-center gap-2 text-emerald-700 font-medium">
                <Loader2 className="w-4 h-4 animate-spin" /> Looking at the food...
              </div>
            )}
            {result && result.is_food && (
              <>
                <div className="text-slate-700 font-medium">
                  Found {result.items.length} food{result.items.length === 1 ? '' : 's'}. Please check
                  the matches and portion sizes.
                </div>
                <div className="text-[11px] text-slate-400">
                  {result.model} · {(result.latency_ms / 1000).toFixed(1)} s · portions are estimates
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {error && <div className="text-xs text-rose-700 bg-rose-50 p-2.5 rounded-xl">{error}</div>}

      {rows.length > 0 && (
        <div className="divide-y divide-slate-100 border border-slate-100 rounded-xl">
          {rows.map((row) => (
            <div key={row.key} className="p-3 flex items-center gap-3 text-xs">
              <input
                type="checkbox"
                checked={row.selected}
                onChange={(e) => updateRow(row.key, { selected: e.target.checked })}
                className="accent-emerald-600"
              />
              <div className="flex-1 min-w-0">
                <div className="font-semibold text-slate-800">
                  {row.foodName}
                  {row.possibleMatch && (
                    <span className="ml-2 px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 text-[10px] font-medium">
                      please check
                    </span>
                  )}
                </div>
                <div className="text-slate-400 text-[11px] truncate" title={row.dish.dish_name}>
                  {row.dish.dish_name}
                </div>
              </div>
              <div className="text-right text-slate-500 w-16">
                {Math.round((row.dish.energy_kcal * row.grams) / 100)} kcal
              </div>
              <div className="flex items-center gap-1">
                <input
                  type="number"
                  min="5"
                  max="600"
                  step="5"
                  value={row.grams}
                  onChange={(e) => updateRow(row.key, { grams: parseFloat(e.target.value) || 0 })}
                  className="w-16 px-2 py-1 border border-slate-200 rounded-lg text-right"
                />
                <span className="text-slate-400">g</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {result && result.unmatched.length > 0 && (
        <div className="text-[11px] text-slate-500">
          Not in our dish database yet: <span className="font-medium">{result.unmatched.join(', ')}</span>. You
          can add a similar dish using the search below.
        </div>
      )}

      {totals && selectedCount > 0 && (
        <div className="grid grid-cols-4 gap-2 text-center">
          {[
            ['Energy', `${Math.round(totals.energy_kcal)} kcal`],
            ['Protein', `${totals.protein_g} g`],
            ['Sugar', `${totals.sugar_g} g`],
            ['Sodium', `${Math.round(totals.sodium_mg)} mg`],
          ].map(([label, value]) => (
            <div key={label} className="bg-slate-50 rounded-xl py-2">
              <div className="text-[11px] text-slate-400">{label}</div>
              <div className="text-xs font-semibold text-slate-700">{value}</div>
            </div>
          ))}
        </div>
      )}

      {alerts.length > 0 && selectedCount > 0 && (
        <div className="space-y-2">
          {alerts.map((a, i) => (
            <AlertCard key={`${a.type}-${a.allergen ?? i}`} alert={a} />
          ))}
        </div>
      )}

      {rows.length > 0 && (
        <button
          onClick={handleAdd}
          disabled={selectedCount === 0}
          className="w-full flex items-center justify-center gap-1.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold shadow-sm transition-colors disabled:opacity-50"
        >
          <Plus className="w-4 h-4" /> Add {selectedCount} item{selectedCount === 1 ? '' : 's'} to Child's Meal Log
        </button>
      )}
    </div>
  );
};
