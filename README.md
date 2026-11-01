# Trust-First AI Nutrition Risk System

**TY Mini Project (EXCP, K. J. Somaiya)**  
*Scope: Ages 4–10, Parent-facing meal guidance with clinical risk flagging and auditable fuzzy logic.*

---

## 🌟 Core Architecture & Novelty

```
[Child Intake Form] ────┐
(Age, Weight, Height,   │
 MUAC, Growth Trend)    ▼
                   [WHO Z-Score Engine] (LMS Method)
                        │
[20,000 Indian Dishes] ─┼───────────────► [Fuzzification Layer]
 (Meal logs, Nutrients, │                  (Triangular & Trapezoidal MFs)
  GI, NOVA Class)       ▼                           │
                   [Dietary Engine]                 ▼
                  (ICMR RDA Comparison)    [Fuzzy Rule Engine]
                                           (MYCIN Certainty Factors)
                                                    │
                                                    ▼
                                            [Trace Object] ◄── Auditable JSON Artifact
                                                    │
                                                    ├──► [Clinician Audit View + Override]
                                                    │
                                                    ▼
                                         [LLM Explanation Layer]
                                         (Claude API with Fallback)
                                                    │
                                                    ▼
                                           [Warm Parent View]
```

### Key Engineering Principles
1. **The LLM Explanation Layer NEVER receives raw scores or raw inputs** — only the structured, validated **Trace Object**.
2. **Hand-Rolled Explainable Fuzzy Inference**: Transparent triangular and trapezoidal membership functions and MYCIN combination rule instead of black-box ML.
3. **Dual Risk Evaluation**:
   - **Anthropometric Risk**: WHO Weight-for-Height Z-score + Mid-Upper Arm Circumference (MUAC) + Growth Trend.
   - **Dietary Risk**: Actual consumed dishes mapped against a **20,000 Indian Dishes database** and ICMR 2020 Recommended Dietary Allowances (RDA).
4. **Non-Punitive Communication**: LLM prompt strictly enforces warm, supportive tone without red/green blaming or confidence numbers shown to parents.
5. **Full Clinical Traceability**: Clinicians can inspect every rule fired, firing strength, antecedent membership, and record overrides with justification logging.

---

## 📁 Repository Structure

```
research/
├── backend/
│   ├── config/
│   │   ├── thresholds.yaml        # Fuzzy boundaries & expert Certainty Factors (no magic numbers)
│   │   └── rda_children.yaml      # ICMR 2020 RDA tables for ages 4-10
│   ├── data/
│   │   └── indian_dishes.csv      # Master database of 20,000 Indian dishes
│   ├── db/
│   │   └── migrations/            # Raw SQL forward-only migrations
│   ├── src/
│   │   ├── api/                   # FastAPI endpoints (assess, history, clinician, meals, trace)
│   │   ├── db/                    # aiosqlite connection manager
│   │   ├── engine/                # Pure logic: fuzzy, rules, WHO z-score, dietary, trace_builder
│   │   ├── llm/                   # Claude API integration with exponential backoff & template fallback
│   │   ├── models/                # Pydantic v2 data models
│   │   └── main.py                # App entrypoint with batch dataset loading
│   └── tests/                     # Comprehensive pytest test suite (100% passing)
│
└── frontend/
    ├── src/
    │   ├── components/            # RiskBadge, NutrientChart, DishSearch, TraceViewer
    │   ├── lib/                   # API client and TypeScript interfaces
    │   ├── pages/                 # IntakeForm, MealLogger, ParentView, ClinicianView
    │   ├── App.tsx                # Main view router
    │   └── main.tsx
    ├── package.json
    └── vite.config.ts
```

---

## 🚀 Quickstart Guide

### 1. Backend Setup & Testing

```bash
cd backend

# Run all pure-logic & integration tests
python -m pytest tests/ -v

# Run the backend server
python -m uvicorn src.main:app --reload --port 8000
```

API docs will be available at: `http://localhost:8000/docs`

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```

Dashboard will be live at: `http://localhost:5173`

---

## 📷 Food Scanner (photo → dishes → nutrients)

In the **Meal Logger** tab, *Scan a Meal Photo* lets a parent take or upload a photo.
Gemini (free tier) describes each food as a base ingredient + cooking method + fat +
grams, chosen from the dataset's own lists; the backend matches each part to one of the
20,000 dishes (blocked by ingredient, `rapidfuzz`), then returns calories, macros and
child-specific alerts (added sugar, sodium, low protein, allergens). The parent checks
and edits the portions before adding them to the meal log. Photos are never stored.

- Setup: put a free key from https://aistudio.google.com/ in `backend/.env` as `GEMINI_API_KEY=`.
- Endpoints: `POST /api/identify-food`, `POST /api/scan-summary`.
- Settings, limits and allergen map: `backend/config/food_scanner.yaml`.
- Free tier quota is small (`gemini-2.5-flash`: 20 requests/day); the scanner falls back
  to `gemini-2.5-flash-lite` automatically when rate-limited.
- Measured on 15 real photos: main dish named correctly 15/15, median latency ~5 s.
  Details, limitations and roadmap: [FOOD_SCANNER_PROGRESS.md](FOOD_SCANNER_PROGRESS.md).

---

## 🔬 Evaluation & Testing Summary

Run `pytest` in `backend/` to verify:
- `test_fuzzy.py`: Triangular, trapezoidal, left-shoulder, right-shoulder, and categorical fuzzification.
- `test_rules.py`: Firing strengths, antecedent evaluation, MYCIN CF combination.
- `test_zscore.py`: WHO LMS weight-for-height z-score calculation and MUAC classification.
- `test_dietary.py`: Multi-dish nutrient aggregation, ICMR RDA percentages, weighted GI, and NOVA classification.
- `test_trace.py`: End-to-end trace assembly for healthy vs. severe risk children.
- `test_api.py`: FastAPI endpoints for health check, assessment, trace history, and clinician override.
- `test_food_match.py`: Ingredient blocking, fuzzy ingredient match, cooking-method fallback, real-dataset roti match.
- `test_food_alerts.py`: Meal totals, added-sugar vs natural sugar, age-specific sodium/sugar/protein alerts, allergens.
- `test_food_vision.py`: Gemini client with mocked HTTP — retries, backoff, model fallback on 429, key handling.
- `test_identify.py`: Food scanner endpoints with mocked Gemini and dish DB — validation, matching, alerts.
