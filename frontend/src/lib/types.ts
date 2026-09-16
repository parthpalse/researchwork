export type GrowthTrend = 'improving' | 'stable' | 'declining';
export type Sex = 'M' | 'F';

export interface WeightReading {
  date: string;
  weight_kg: number;
}

export interface ChildInput {
  child_id: string;
  age_months: number;
  sex: Sex;
  weight_kg: number;
  height_cm: number;
  muac_cm: number;
  growth_trend: GrowthTrend;
  recent_weight_history?: WeightReading[];
}

export interface MealEntry {
  dish_id: string;
  dish_name: string;
  servings: number;
  serving_size_g: number;
}

export interface NutrientSummary {
  total_energy_kcal: number;
  total_protein_g: number;
  total_fat_g: number;
  total_carbs_g: number;
  total_fiber_g: number;
  total_sugar_g: number;
  total_calcium_mg: number;
  total_iron_mg: number;
  total_zinc_mg: number;
  total_vitamin_c_mg: number;
  total_thiamin_mg: number;
  total_folate_mcg: number;
  avg_glycemic_index: number;
  nova_breakdown: Record<string | number, number>;
}

export interface RuleFired {
  rule_id: string;
  antecedents: Record<string, string>;
  strength: number;
  expert_cf: number;
  conclusion_category: string;
  conclusion_level: string;
}

export interface CombinedConfidence {
  high: number;
  moderate: number;
  low: number;
}

export interface DietaryRisk {
  nutrient_gaps: string[];
  excess_nutrients: string[];
  nova_breakdown: Record<string, number>;
  avg_glycemic_index?: number | null;
}

export interface TraceMetadata {
  weight_for_height_z?: number;
  muac_risk_band?: string;
  [key: string]: any;
}

export interface TraceObject {
  child_id: string;
  timestamp: string;
  fuzzification: Record<string, Record<string, number>>;
  rules_fired: RuleFired[];
  combined_confidence: CombinedConfidence;
  dietary_risk?: DietaryRisk | null;
  final_risk_level: string;
  final_confidence: number;
  _metadata?: TraceMetadata;
}

export interface LLMExplanation {
  parent_message: string;
  suggested_next_step: string;
  clinician_note: string;
}

export interface AssessResponse {
  trace_id: number;
  trace: TraceObject;
  explanation: LLMExplanation;
}

export interface ChildHistoryItem {
  timestamp: string;
  final_risk_level: string;
  final_confidence: number;
  has_override: boolean;
}

export interface Dish {
  record_id: string;
  dish_name: string;
  base_ingredient?: string;
  category?: string;
  cooking_method?: string;
  fat_medium_used?: string;
  energy_kcal: number;
  protein_g: number;
  total_fat_g?: number;
  carbohydrate_g?: number;
  dietary_fiber_g?: number;
  sugars_g?: number;
  glycemic_index?: number;
  glycemic_index_est?: number;
  nova_group?: number;
}

export interface MealLogResponse {
  child_id: string;
  date: string;
  meals_count: number;
  nutrient_summary: NutrientSummary;
}
