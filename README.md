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

## 🔬 Evaluation & Testing Summary

Run `pytest` in `backend/` to verify:
- `test_fuzzy.py`: Triangular, trapezoidal, left-shoulder, right-shoulder, and categorical fuzzification.
- `test_rules.py`: Firing strengths, antecedent evaluation, MYCIN CF combination.
- `test_zscore.py`: WHO LMS weight-for-height z-score calculation and MUAC classification.
- `test_dietary.py`: Multi-dish nutrient aggregation, ICMR RDA percentages, weighted GI, and NOVA classification.
- `test_trace.py`: End-to-end trace assembly for healthy vs. severe risk children.
- `test_api.py`: FastAPI endpoints for health check, assessment, trace history, and clinician override.
