import {
  ChildInput,
  NutrientSummary,
  AssessResponse,
  Dish,
  MealEntry,
  MealLogResponse,
  ChildHistoryItem,
} from './types';

const BASE_URL = '/api';

export async function assessChild(
  child: ChildInput,
  nutrientSummary?: NutrientSummary | null
): Promise<AssessResponse> {
  const response = await fetch(`${BASE_URL}/assess`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      child,
      nutrient_summary: nutrientSummary || null,
    }),
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(err || 'Failed to assess child risk');
  }

  return response.json();
}

export async function searchDishes(
  query = '',
  category = '',
  limit = 25
): Promise<Dish[]> {
  const params = new URLSearchParams();
  if (query) params.append('q', query);
  if (category) params.append('category', category);
  if (limit) params.append('limit', String(limit));

  const response = await fetch(`${BASE_URL}/dishes/search?${params.toString()}`);
  if (!response.ok) {
    throw new Error('Failed to search dishes');
  }

  return response.json();
}

export async function getDishCategories(): Promise<string[]> {
  const response = await fetch(`${BASE_URL}/dishes/categories`);
  if (!response.ok) {
    throw new Error('Failed to fetch categories');
  }

  return response.json();
}

export async function logMeals(
  childId: string,
  meals: MealEntry[],
  date?: string
): Promise<MealLogResponse> {
  const response = await fetch(`${BASE_URL}/meal-log`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      child_id: childId,
      meals,
      date,
    }),
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(err || 'Failed to log meals');
  }

  return response.json();
}

export async function overrideRisk(
  traceId: number,
  newRiskLevel: string,
  reason: string
): Promise<any> {
  const response = await fetch(`${BASE_URL}/clinician/override`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      trace_id: traceId,
      new_risk_level: newRiskLevel,
      reason,
    }),
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(err || 'Failed to submit override');
  }

  return response.json();
}

export async function getChildHistory(childId: string): Promise<ChildHistoryItem[]> {
  const response = await fetch(`${BASE_URL}/child/${encodeURIComponent(childId)}/history`);
  if (!response.ok) {
    throw new Error('Failed to fetch child history');
  }

  return response.json();
}

export async function getChildTrace(childId: string, timestamp: string): Promise<any> {
  const response = await fetch(
    `${BASE_URL}/child/${encodeURIComponent(childId)}/trace/${encodeURIComponent(timestamp)}`
  );
  if (!response.ok) {
    throw new Error('Failed to fetch child trace');
  }

  return response.json();
}
