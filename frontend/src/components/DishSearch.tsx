import React, { useState, useEffect } from 'react';
import { Dish, MealEntry } from '../lib/types';
import { searchDishes, getDishCategories } from '../lib/api';
import { Search, Plus, Utensils } from 'lucide-react';

interface DishSearchProps {
  onAddMeal: (meal: MealEntry) => void;
}

export const DishSearch: React.FC<DishSearchProps> = ({ onAddMeal }) => {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');
  const [categories, setCategories] = useState<string[]>([]);
  const [results, setResults] = useState<Dish[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedDish, setSelectedDish] = useState<Dish | null>(null);
  const [servings, setServings] = useState(1.0);
  const [servingSizeG, setServingSizeG] = useState(100.0);

  useEffect(() => {
    getDishCategories()
      .then(setCategories)
      .catch(() => {});
  }, []);

  useEffect(() => {
    const handler = setTimeout(() => {
      if (query.trim().length > 1 || category) {
        setLoading(true);
        searchDishes(query, category, 15)
          .then((res) => {
            setResults(res);
            setLoading(false);
          })
          .catch(() => setLoading(false));
      } else {
        setResults([]);
      }
    }, 250);

    return () => clearTimeout(handler);
  }, [query, category]);

  const handleAdd = () => {
    if (!selectedDish) return;
    onAddMeal({
      dish_id: selectedDish.record_id,
      dish_name: selectedDish.dish_name,
      servings,
      serving_size_g: servingSizeG,
    });
    setSelectedDish(null);
    setServings(1.0);
  };

  return (
    <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 space-y-4">
      <div className="flex items-center gap-2">
        <Utensils className="w-5 h-5 text-emerald-600" />
        <h3 className="font-semibold text-slate-800 text-sm">
          Indian Dishes Database (20,000 Verified Dishes)
        </h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="md:col-span-2 relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search e.g. Bajra Roti, Dal Tadka, Khichdi, Idli..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
          />
        </div>

        <div>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="w-full py-2 px-3 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 bg-white"
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading && <div className="text-xs text-slate-400">Searching 20,000 dishes...</div>}

      {/* Results Dropdown / List */}
      {results.length > 0 && !selectedDish && (
        <div className="max-h-56 overflow-y-auto border border-slate-100 rounded-xl divide-y divide-slate-100">
          {results.map((dish) => (
            <div
              key={dish.record_id}
              onClick={() => setSelectedDish(dish)}
              className="p-3 hover:bg-slate-50 cursor-pointer flex items-center justify-between text-xs transition-colors"
            >
              <div>
                <div className="font-semibold text-slate-800">{dish.dish_name}</div>
                <div className="text-slate-400 text-[11px]">
                  {dish.category} • {dish.cooking_method}
                </div>
              </div>
              <div className="text-right">
                <div className="font-medium text-slate-700">{dish.energy_kcal} kcal</div>
                <div className="text-slate-400 text-[11px]">{dish.protein_g}g Protein</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Selected Dish Portions */}
      {selectedDish && (
        <div className="bg-emerald-50/60 p-4 rounded-xl border border-emerald-100 space-y-3">
          <div className="flex justify-between items-start">
            <div>
              <div className="font-semibold text-sm text-emerald-950">
                {selectedDish.dish_name}
              </div>
              <div className="text-xs text-emerald-700">
                {selectedDish.category} • Base: {selectedDish.base_ingredient}
              </div>
            </div>
            <button
              onClick={() => setSelectedDish(null)}
              className="text-xs text-slate-400 hover:text-slate-600"
            >
              Cancel
            </button>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <label className="block text-slate-600 font-medium mb-1">Portion Servings</label>
              <input
                type="number"
                step="0.5"
                min="0.5"
                max="10"
                value={servings}
                onChange={(e) => setServings(parseFloat(e.target.value) || 1.0)}
                className="w-full px-3 py-1.5 border border-emerald-200 rounded-lg bg-white"
              />
            </div>
            <div>
              <label className="block text-slate-600 font-medium mb-1">Serving Grams</label>
              <input
                type="number"
                step="10"
                min="20"
                max="500"
                value={servingSizeG}
                onChange={(e) => setServingSizeG(parseFloat(e.target.value) || 100.0)}
                className="w-full px-3 py-1.5 border border-emerald-200 rounded-lg bg-white"
              />
            </div>
          </div>

          <button
            onClick={handleAdd}
            className="w-full flex items-center justify-center gap-1.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold shadow-sm transition-colors"
          >
            <Plus className="w-4 h-4" /> Add to Child's Meal Log
          </button>
        </div>
      )}
    </div>
  );
};
