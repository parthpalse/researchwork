# Trust-First AI Nutrition Risk System — Tasks

## Component 1: Project Scaffold & Data Models
- [x] `pyproject.toml` with all dependencies
- [x] `.env.example`
- [x] `config/thresholds.yaml` — all fuzzy boundaries + expert CFs
- [x] `config/rda_children.yaml` — ICMR/WHO RDA for ages 4-10
- [x] `src/models/child.py` — ChildInput, ChildRecord
- [x] `src/models/trace.py` — TraceObject, RuleFired, FuzzificationResult
- [x] `src/models/meal.py` — MealEntry, MealLog, NutrientSummary
- [x] `src/models/explanation.py` — LLMExplanation

## Component 2: Fuzzy Logic Engine
- [x] `src/engine/fuzzy.py` — triangular/trapezoidal membership functions
- [x] `src/engine/rules.py` — rule base + firing + MYCIN combination
- [x] `src/engine/zscore.py` — WHO z-score lookup (LMS method, 65-120cm)
- [x] `src/engine/dietary.py` — meal nutrient aggregation + RDA comparison
- [x] `src/engine/trace_builder.py` — full pipeline orchestrator

## Component 3: LLM Explanation Layer
- [x] `src/llm/prompts.py` — fixed system prompt (non-punitive)
- [x] `src/llm/explainer.py` — Claude API + exponential backoff + template fallback

## Component 4: API Layer
- [x] `src/main.py` — FastAPI app with batch loading for 20k dishes
- [x] `src/api/assess.py` — POST /api/assess
- [x] `src/api/history.py` — GET /api/child/{id}/history
- [x] `src/api/clinician.py` — POST /api/clinician/override
- [x] `src/api/meals.py` — POST /api/meal-log + GET /api/dishes/search + GET /api/dishes/categories
- [x] `src/api/trace.py` — GET /api/child/{id}/trace/{ts}

## Component 5: Database
- [x] `src/db/connection.py` — aiosqlite connection manager
- [x] `db/migrations/001_create_children.sql`
- [x] `db/migrations/002_create_traces.sql`
- [x] `db/migrations/003_create_meal_logs.sql`
- [x] `db/migrations/004_create_dishes.sql`

## Component 6: Frontend
- [x] Vite + React + TS + Tailwind scaffold
- [x] `src/lib/types.ts` + `src/lib/api.ts`
- [x] `IntakeForm.tsx` (WHO physical measurements)
- [x] `MealLogger.tsx` + `DishSearch.tsx` (20,000 Indian dishes autocomplete)
- [x] `ParentView.tsx` + `RiskBadge.tsx` (supportive, warm tone)
- [x] `ClinicianView.tsx` + `TraceViewer.tsx` (audit trace, rules fired, override)
- [x] `NutrientChart.tsx` (ICMR RDA comparisons)
- [x] `App.tsx` (view tabs)

## Component 7: Tests
- [x] `tests/test_fuzzy.py` (all passing)
- [x] `tests/test_rules.py` (all passing)
- [x] `tests/test_zscore.py` (all passing)
- [x] `tests/test_dietary.py` (all passing)
- [x] `tests/test_trace.py` (all passing)
- [x] `tests/test_api.py` (all passing)

## Final
- [x] README.md
- [x] Run all tests green (19 of 19 tests passed)
- [ ] Verify frontend build
