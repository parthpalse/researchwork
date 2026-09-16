# Feature Plan: Food Identification from Camera

**Author:** Auto-generated implementation plan  
**For:** Parth Palse  
**Date:** 2026-09-16  
**Status:** Proposed  

---

## Overview

Add a feature where the user can **click/upload a photo of food** and the system
automatically identifies the dish(es), matches them against the **20,000 Indian
dishes database**, and returns full nutritional information — ready to log into
the Meal Logger.

---

## Tool Choice: Google Gemini Vision (Free Tier)

| Detail              | Value                                    |
|:--------------------|:-----------------------------------------|
| Model               | `gemini-2.0-flash`                       |
| Rate limit          | 15 requests/min                          |
| Daily limit         | ~1,500 requests/day                      |
| Cost                | **$0 (free tier)**                       |
| API key source      | https://aistudio.google.com/             |
| Python SDK          | `google-genai` (lightweight, official)   |

No paid API key required. Gemini free tier is more than enough for this project.

---

## Architecture

```
User clicks photo / uploads image
            │
            ▼
  [Frontend: FoodCamera.tsx]
  Captures image → base64 encode
            │
            ▼
  POST /api/identify-food  { image_base64: "..." }
            │
            ▼
  [Backend: src/api/identify.py]
  Sends image to Gemini Vision API with prompt:
    "Identify all Indian dishes visible in this image.
     Return a JSON array of dish names."
            │
            ▼
  [Backend: src/engine/food_match.py]
  Takes Gemini's dish name guesses
  → Block by category (Cereals, Pulses, etc.)
  → rapidfuzz match within blocks against 20k dishes DB
  → Return top matches with full nutrient data
            │
            ▼
  Response: { identified: ["Dal Tadka", ...], matches: [{dish + nutrients}] }
            │
            ▼
  [Frontend: MealLogger.tsx]
  Auto-populates meal list with matched dishes
  User can confirm/edit before logging
```

---

## Files to Create / Modify

### Backend

| Action   | File                          | What it does                                                      |
|:---------|:------------------------------|:------------------------------------------------------------------|
| **NEW**  | `src/api/identify.py`         | `POST /api/identify-food` endpoint. Accepts base64 image, calls Gemini Vision, runs fuzzy match, returns matched dishes with nutrients. |
| **NEW**  | `src/engine/food_match.py`    | Pure logic module. Takes raw dish name strings from Gemini → blocks candidates by category → `rapidfuzz.process.extract` within each block → returns ranked matches. No O(n²). |
| MODIFY   | `src/main.py`                 | Register the new `identify` router: `app.include_router(identify.router)` |
| MODIFY   | `pyproject.toml`              | Add dependencies: `google-genai>=1.0.0`, `rapidfuzz>=3.6.0`      |
| MODIFY   | `.env.example`                | Add `GEMINI_API_KEY=`                                             |
| MODIFY   | `config/thresholds.yaml`      | Add `food_identification.min_confidence: 0.60` threshold          |

### Frontend

| Action   | File                              | What it does                                                      |
|:---------|:----------------------------------|:------------------------------------------------------------------|
| **NEW**  | `src/components/FoodCamera.tsx`   | Camera capture button + file upload. Shows image preview. Sends base64 to `/api/identify-food`. Displays identified dishes for user confirmation. |
| MODIFY   | `src/pages/MealLogger.tsx`        | Wire FoodCamera component. When dishes are identified, auto-add them to the meal entry list. |
| MODIFY   | `src/lib/api.ts`                  | Add `identifyFood(imageBase64: string)` API client function.      |
| MODIFY   | `src/lib/types.ts`                | Add `FoodIdentificationResult` interface.                         |

### Tests

| Action   | File                          | What it does                                                      |
|:---------|:------------------------------|:------------------------------------------------------------------|
| **NEW**  | `tests/test_food_match.py`    | Unit tests for `food_match.py`: mocked Gemini responses → verify fuzzy matching returns correct dishes from DB. Tests edge cases: blurry/unrecognized food, multiple dishes in one image, partial name matches. |

---

## Key Implementation Rules

1. **Gemini API call must have retry + backoff + timeout** — same pattern as `src/llm/explainer.py`. Use `httpx` with exponential backoff + jitter. Never a bare request in a loop.
2. **Fuzzy matching must NOT be O(n²)** — block candidates by `category` column first, then `rapidfuzz.process.extract` within each block. The DB has 20k+ rows.
3. **Image stays client-side after identification** — do not persist uploaded images to disk or database.
4. **Confidence threshold in YAML config** — `config/thresholds.yaml`, never hardcoded. Dishes below the threshold are shown as "possible match" with lower confidence.
5. **Gemini API key from env var only** — `GEMINI_API_KEY` in `.env`, never hardcoded.
6. **Graceful fallback** — if Gemini API is down or key missing, return a clear error and let the user fall back to manual dish search (which already works).

---

## API Contract

### Request
```
POST /api/identify-food
Content-Type: application/json

{
  "image_base64": "<base64-encoded image string>"
}
```

### Response
```json
{
  "identified_names": ["Dal Tadka", "Jeera Rice", "Papad"],
  "matches": [
    {
      "identified_name": "Dal Tadka",
      "confidence": 0.92,
      "dish": {
        "record_id": "IND-004521",
        "dish_name": "Dal Tadka (Toor Dal) (Tempered in Ghee) [Home-Style]",
        "category": "Pulses/Legumes",
        "energy_kcal": 186.3,
        "protein_g": 9.8,
        "total_fat_g": 6.2,
        "carbohydrate_g": 22.1
      }
    }
  ],
  "unmatched": ["Papad"]
}
```

---

## Getting Started

```bash
# 1. Get a free Gemini API key
#    Go to https://aistudio.google.com/ → Create API Key

# 2. Add key to backend/.env
echo "GEMINI_API_KEY=your-key-here" >> backend/.env

# 3. Install new dependencies
cd backend
uv pip install -e ".[dev]"

# 4. Run tests
python -m pytest tests/test_food_match.py -v

# 5. Start backend & frontend (same as before)
```
