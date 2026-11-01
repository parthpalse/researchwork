# Food Scanner — Progress & Remaining Work

Branch: `feature/food-scanner` · Started: 2026-11-02 · Target: 6–7 hours

This file is updated after every step. It says what is done, what is left,
and what is honest to claim on the slides.

---

## What we are building

Take or upload a food photo → Gemini (free tier, `gemini-2.5-flash`) describes each
food in terms of our dataset (base ingredient + cooking method + oil + grams) →
we find the closest row in the 20,000-dish database → show calories/macros,
child-specific alerts (sugar, sodium, low protein, allergens) → parent confirms →
dishes go into the Meal Logger.

### Why Gemini picks from our ingredient list
The 20k dataset is not named like "Idli" or "Roti". Every row is
**base ingredient × cooking method × oil × style**, built from only 130 base
ingredients (e.g. `Poha (Flattened Rice) (Boiled)`). So Gemini must break each food
into those parts (Roti → Wheat Atta, Griddled; Aloo Paratha → Wheat Atta + Potato).
We give Gemini the exact list of 130 ingredients and 9 cooking methods, and then
search only that ingredient's ~240 rows (no slow all-vs-all matching).

---

## Steps

| # | Step | Status |
|---|------|--------|
| 1 | Branch, config (`config/food_scanner.yaml`), sodium limits, `rapidfuzz`, `.env.example` | ✅ Done |
| 2 | `src/engine/food_match.py` — match Gemini's description to a dish row + tests (10 passing) | ✅ Done |
| 3 | `src/engine/food_alerts.py` — sugar / sodium / low-protein / allergen alerts + tests (7 passing) | ✅ Done |
| 4 | `src/llm/food_vision.py` — Gemini call (retry, backoff, timeout, rate limit) | ⏳ Next |
| 5 | `src/api/identify.py` — `POST /api/identify-food` + mocked API tests | ⬜ To do |
| 6 | Frontend `FoodCamera.tsx` + wire into Meal Logger | ⬜ To do |
| 7 | End-to-end test with real food photos, measure real latency | ⬜ To do |
| 8 | README update, final cleanup, merge to `main` | ⬜ To do |

---

## Remaining work (detail)

**Step 2 — Matcher. ✅ DONE.** Index grouped by base ingredient; ingredient name
fuzzy-matched with `rapidfuzz` against 130 names; rows in that group scored by
cooking method / oil / style (weights in YAML).
Confidence = ingredient match × Gemini's confidence × attribute match
(attribute share = `attribute_weight` 0.4). Below `min_confidence` (0.60) →
"possible match". Gram estimates clamped to 5–600 g. Tested incl. a real-dataset
check (roti → Wheat Atta, Griddled, No Added Fat).

**Step 3 — Alerts. ✅ DONE.** Meal totals (kcal, protein, fat, carbs, fibre,
sugar, sodium) scaled by grams. Alerts per child age group:
sugar > ⅓ of daily sugar limit, sodium > ⅓ of daily sodium limit (NASEM 2019:
1500 mg for 4–9 y, 1800 mg for 10–12 y), protein < half of the meal's protein
share, plus allergens from base ingredient **and** cooking fat (e.g. ghee → milk,
groundnut oil → peanuts). Unknown age → youngest group (most cautious).
Gentle wording, no blame.

**Step 4 — Gemini client.** REST call with `httpx`, JSON-schema response
(ingredient and method are restricted to our lists), retries with exponential
backoff + jitter, 30 s timeout, at most one call per 6 s. Key from
`GEMINI_API_KEY` only. Clear error if the key is missing or Gemini is down.

**Step 5 — Endpoint.** `POST /api/identify-food` with `image_base64`,
`mime_type`, optional `age_months`. Checks image type/size, never saves the image,
returns items + matches + nutrient totals + alerts + measured latency. Tests mock
Gemini.

**Step 6 — Frontend.** Camera/upload button, shrink photo to ~640 px before
upload, show each food with its matched dish, grams (editable), confidence badge
and alerts. "Add to meal log" sends them to the existing Meal Logger.

**Step 7 — Real test.** Run 10–20 real Indian food photos, note how many were
right, record real latency. These are the only numbers that should go on slides.

**Step 8 — Wrap up.** README section, update `FOOD_IDENTIFICATION_PLAN.md`
status, merge branch into `main` after review.

---

## Not in this 6–7 hour scope (keep on the roadmap slide)

- Fine-tuning YOLOv8 on Indian food images (needs a labelled dataset + GPU days)
- SAM outlines / estimating portion size from pixels or depth
- Barcode scanning of packaged food (Open Food Facts)
- Offline TFLite/ONNX model

## Notes for the slides (be honest)

- Slide 5 says Gemini 2.0 Flash — it is no longer available; we use **Gemini 2.5 Flash**.
- Slides 4, 5, 7, 9 (5,000 images, YOLOv8, SAM, F1 88.4%, 1.15 s, 14.2%) are **not
  built or measured** yet. Mark them as "planned/target" or replace with Step 7 results.
- Portion size = Gemini's gram estimate, which the parent can edit. Not SAM/depth.

## Known issues found along the way

- `pytest tests/` passes but never exits: the API tests open a SQLite connection
  that is never closed. Will be fixed in Step 5 with a test fixture.
- `src/llm/explainer.py` uses `claude-3-haiku-20240307`, which may be retired.
  If so, the app silently uses the built-in fallback message. Not part of this task.
