import React, { useRef, useState } from 'react';
import { MealEntry, PackagedLookupResult } from '../lib/types';
import { lookupPackaged } from '../lib/api';
import { Barcode, Camera, Search, Loader2, Info, Plus } from 'lucide-react';

// The browser Barcode Detection API (Chrome on Android/macOS/ChromeOS; not all desktops)
interface DetectedBarcode {
  rawValue: string;
}
interface BarcodeDetectorLike {
  detect(source: ImageBitmapSource): Promise<DetectedBarcode[]>;
}
type BarcodeDetectorCtor = new (options?: { formats?: string[] }) => BarcodeDetectorLike;

const BarcodeDetectorApi: BarcodeDetectorCtor | undefined = (
  window as unknown as { BarcodeDetector?: BarcodeDetectorCtor }
).BarcodeDetector;

const BARCODE_FORMATS = ['ean_13', 'ean_8', 'upc_a', 'upc_e'];

interface PackagedFoodLookupProps {
  ageMonths: number;
  onAddMeal: (meal: MealEntry) => void;
}

export const PackagedFoodLookup: React.FC<PackagedFoodLookupProps> = ({ ageMonths, onAddMeal }) => {
  const photoInput = useRef<HTMLInputElement>(null);
  const [barcode, setBarcode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PackagedLookupResult | null>(null);
  const [grams, setGrams] = useState(0);

  const runLookup = async (code: string) => {
    if (!code.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await lookupPackaged(code.trim(), ageMonths);
      setResult(res);
      setGrams(res.product.serving_g);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not look up this barcode.');
    } finally {
      setLoading(false);
    }
  };

  const handlePhoto = async (file: File | undefined) => {
    if (!file || !BarcodeDetectorApi) return;
    setError(null);
    try {
      const bitmap = await createImageBitmap(file);
      const found = await new BarcodeDetectorApi({ formats: BARCODE_FORMATS }).detect(bitmap);
      if (found.length === 0) {
        setError("We couldn't read a barcode in this photo. Try a closer, sharper picture or type the number.");
        return;
      }
      setBarcode(found[0].rawValue);
      runLookup(found[0].rawValue);
    } catch {
      setError('Barcode reading failed on this device. Please type the number instead.');
    }
  };

  const handleAdd = () => {
    if (!result || grams <= 0) return;
    onAddMeal({
      dish_id: result.product.record_id,
      dish_name: result.product.dish_name,
      servings: 1,
      serving_size_g: grams,
    });
    setResult(null);
    setBarcode('');
  };

  const product = result?.product;
  const portionKcal = product ? Math.round((product.energy_kcal * grams) / 100) : 0;

  return (
    <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 space-y-4">
      <div className="flex items-center gap-2">
        <Barcode className="w-5 h-5 text-emerald-600" />
        <h3 className="font-semibold text-slate-800 text-sm">Packaged Food (Barcode)</h3>
      </div>

      <input
        ref={photoInput}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={(e) => {
          handlePhoto(e.target.files?.[0]);
          e.target.value = '';
        }}
      />

      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          runLookup(barcode);
        }}
      >
        <input
          type="text"
          inputMode="numeric"
          placeholder="Barcode number, e.g. 8901058851298"
          value={barcode}
          onChange={(e) => setBarcode(e.target.value)}
          className="flex-1 px-3 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
        />
        <button
          type="submit"
          disabled={loading || !barcode.trim()}
          className="px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold disabled:opacity-50"
          title="Look up"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
        </button>
        {BarcodeDetectorApi && (
          <button
            type="button"
            onClick={() => photoInput.current?.click()}
            className="px-3 py-2 border border-emerald-200 text-emerald-700 hover:bg-emerald-50 rounded-xl text-xs font-semibold"
            title="Scan barcode with camera"
          >
            <Camera className="w-4 h-4" />
          </button>
        )}
      </form>

      {error && <div className="text-xs text-rose-700 bg-rose-50 p-2.5 rounded-xl">{error}</div>}

      {product && result && (
        <div className="bg-emerald-50/60 p-4 rounded-xl border border-emerald-100 space-y-3">
          <div>
            <div className="font-semibold text-sm text-emerald-950">{product.dish_name}</div>
            <div className="text-[11px] text-emerald-700">
              {product.energy_kcal} kcal / 100 g · NOVA {product.nova_group} · from Open Food Facts
            </div>
          </div>

          <div className="flex items-center gap-3 text-xs">
            <label className="text-slate-600 font-medium">Amount eaten</label>
            <input
              type="number"
              min="5"
              max="1000"
              step="5"
              value={grams}
              onChange={(e) => setGrams(parseFloat(e.target.value) || 0)}
              className="w-20 px-2 py-1 border border-emerald-200 rounded-lg bg-white text-right"
            />
            <span className="text-slate-400">g</span>
            <span className="ml-auto font-semibold text-slate-700">{portionKcal} kcal</span>
          </div>

          {result.alerts.length > 0 && (
            <div className="space-y-2">
              {result.alerts.map((a, i) => (
                <div
                  key={`${a.type}-${a.allergen ?? i}`}
                  className={`flex gap-2 p-2.5 rounded-xl text-xs ${
                    a.type === 'allergen' ? 'bg-sky-50 text-sky-900' : 'bg-amber-50 text-amber-900'
                  }`}
                >
                  <Info className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{a.message}</span>
                </div>
              ))}
              <div className="text-[11px] text-slate-400">Alerts are for one serving of {product.serving_g} g.</div>
            </div>
          )}

          <button
            onClick={handleAdd}
            disabled={grams <= 0}
            className="w-full flex items-center justify-center gap-1.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold shadow-sm transition-colors disabled:opacity-50"
          >
            <Plus className="w-4 h-4" /> Add to Child's Meal Log
          </button>
        </div>
      )}
    </div>
  );
};
