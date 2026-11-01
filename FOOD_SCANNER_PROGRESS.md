# Food Scanner — Progress & Remaining Work

Branch: `feature/food-scanner` · Built: 2026-11-02 · Status: **feature complete, awaiting review/merge**

This file was updated after every step. It says what is done, what is left,
and what is honest to claim on the slides.

---

## What we built

Take or upload a food photo → Gemini (free tier) describes each food in terms of
our dataset (base ingredient + cooking method + oil + grams) → we find the
closest row in the 20,000-dish database → show calories/macros and
child-specific alerts (added sugar, sodium, low protein, allergens) → parent
checks/edits → dishes go into the Meal Logger.

### Why Gemini picks from our ingredient list
The 20k dataset is not named like "Idli" or "Roti". Every row is
**base ingredient × cooking method × oil × style**, built from only 130 base
ingredients (e.g. `Poha (Flattened Rice) (Boiled)`). So Gemini must break each food
into those parts (Roti → Wheat Atta, Griddled; Idli → Rice + Urad Dal, Fermented).
We give Gemini the exact list of 130 ingredients, 9 cooking methods and 7 fats as
a JSON schema, then search only that ingredient's ~240 rows (no all-vs-all matching).

---

## Steps

| # | Step | Status |
|---|------|--------|
| 1 | Branch, config (`config/food_scanner.yaml`), sodium limits, `rapidfuzz`, `.env.example` | ✅ Done |
| 2 | `src/engine/food_match.py` — match Gemini's description to a dish row + tests | ✅ Done |
| 3 | `src/engine/food_alerts.py` — added sugar / sodium / low-protein / allergen alerts + tests | ✅ Done |
| 4 | `src/llm/food_vision.py` — Gemini call (retry, backoff, timeout, rate limit, model fallback) + tests | ✅ Done |
| 5 | `src/api/identify.py` — `POST /api/identify-food` + `POST /api/scan-summary` + tests | ✅ Done |
| 6 | Frontend `FoodCamera.tsx` + wire into Meal Logger | ✅ Done |
| 7 | End-to-end test with 15 real food photos, measure latency, fix what it found | ✅ Done |
| 8 | README section, plan status, this file | ✅ Done |
| — | **You:** click through the UI in a browser, then approve merge into `main` | ⏳ Waiting |

Tests: **54 backend tests pass** (`pytest tests/` in ~3 s). Frontend `npm run build` passes.

---

## Step details

**Step 1 — Setup.** `config/food_scanner.yaml` holds every model setting,
limit and weight (nothing hardcoded). Sodium daily upper limits added to
`rda_children.yaml` (NASEM 2019: 1500 mg for 4–9 y, 1800 mg for 10–12 y).
`rapidfuzz` added; `GEMINI_API_KEY` in `.env.example`.

**Step 2 — Matcher.** Index grouped by base ingredient; ingredient name
fuzzy-matched with `rapidfuzz` against 130 names; rows in that group scored by
cooking method / oil / style. If an ingredient has no row for the requested
method (e.g. rice has no "Gravy-Stewed"), the closest method from
`similar_methods` in YAML gets partial credit — never a fattier one by accident.
Confidence = ingredient match × Gemini's confidence × attribute match. Below 0.60
→ "please check" tag. Gram estimates clamped to 5–600 g.

**Step 3 — Alerts.** Meal totals scaled by grams. Per child age group:
- added sugar > ⅓ of the day's limit — counts only sugar/jaggery, because the
  25–38 g limit is a WHO *free sugar* limit (natural sugar in milk/veg excluded)
- sodium > ⅓ of the day's limit
- protein < half of the meal's protein share
- allergens from ingredient **and** cooking fat (ghee → milk, groundnut oil → peanuts)

Unknown age → youngest group (most cautious). Gentle wording, no blame.

**Step 4 — Gemini client.** REST via `httpx` (no extra SDK). JSON-schema
response restricts values to our lists (`"Other"` → reported as unmatched).
Retries network errors and 5xx with exponential backoff + jitter; other 4xx not
retried. **HTTP 429 → switch to the next model in `fallback_models`** (free quotas
are per model and daily, so retrying the same model is pointless). 30 s timeout,
≤1 call per 6 s per model. Key only from `GEMINI_API_KEY`, sent in a header,
never in URL/logs. Response says which model answered.

**Step 5 — Endpoints.**
- `POST /api/identify-food` — `image_base64` (plain or `data:` URL), `mime_type`,
  optional `age_months`. Rejects wrong type (415), bad base64 (422), >4 MB (413)
  *before* calling Gemini. Image is never saved. Returns items → components,
  unmatched foods, totals, alerts, model, `latency_ms`.
- `POST /api/scan-summary` — `[{dish_id, grams}]` → fresh totals/alerts after edits.
- Also fixed: `main.py` never loaded `backend/.env`; pytest hung after finishing.

**Step 6 — Frontend.** "Scan a Meal Photo" card at the top of the Meal Logger
tab: Take Photo (rear camera on phones) / Upload Photo; photo shrunk to 640 px in
the browser; per-component rows with tick box, editable grams, kcal, "please
check" tag; totals; amber (nutrient) / blue (allergen) alerts; edits re-fetch
alerts; "Add N items to Child's Meal Log".

**Step 7 — Real test (15 Wikimedia Commons photos, 640 px, child age 6 y).**

| Measure | Result |
|---|---|
| Main dish named correctly | **15 / 15** (biryani, roti, chole bhature, dal-rice, idli-sambar, jalebi, dalia khichdi, masala dosa, palak paneer, poha, rajma chawal, samosa, upma, poori-aloo, boiled egg) |
| Latency, `gemini-2.5-flash` (first run, 15 photos) | min 3.4 s · **median 5.3 s** · max 17.4 s |
| Latency, `gemini-2.5-flash-lite` fallback (9 photos) | min 4.4 s · **median 5.1 s** · max 5.8 s |
| Calorie / portion accuracy | **Not measured** — needs weighed reference meals |

What the test found and what was fixed:
1. Rice/semolina with an unavailable method matched **deep-fried** rows
   (biryani 1261 kcal) → closest-method fallback (now 678 kcal).
2. Sugar alert fired on idli-sambar/chole from natural tomato/onion sugar →
   alert now counts added sugar only.
3. **Free tier `gemini-2.5-flash` = only 20 requests/day** (quota resets at
   midnight Pacific ≈ 1:30 PM IST) → automatic fallback to `gemini-2.5-flash-lite`.
4. Flash-lite is a little less precise (read chole as black chana, bhature as
   wheat atta instead of maida). The parent review step exists for this.

Observations (not bugs): portions are estimated as they appear, so adult plates
give adult portions; Indian cooked dishes in the dataset carry a lot of sodium, so
the sodium alert fires on many full meals.

---

## Remaining work

**Must do (you):**
1. Open the app and scan 2–3 photos to check the UI looks right (I could only
   test the API and build, not click through the page).
2. Approve merging `feature/food-scanner` into `main`.
3. **Delete the Gemini key** that was pasted into chat (AI Studio → Delete key)
   and put a new one in `backend/.env` after the demo.

**Should do before presenting:**
4. Update slides — see "Notes for the slides" below.
5. On demo day, don't waste quota: ~20 scans/day on flash + a separate quota on
   flash-lite. Test before 1:30 PM IST or after the reset.

**Could do next (roadmap):**
- Fine-tune YOLOv8 on Indian food images (dataset + labelling + GPU days)
- SAM outlines / portion size from pixels or a reference object
- Barcode scanning of packaged food (Open Food Facts)
- Measure calorie error against weighed meals
- Add common dishes missing from the dataset (papad, pickle, chutney)
- ~~`src/llm/explainer.py` uses retired `claude-3-haiku-20240307`~~ — **fixed**:
  now the official `anthropic` SDK with `claude-haiku-5-5`, JSON-schema output,
  SDK retries/backoff, 30 s timeout, refusal → fallback template (4 tests).
  Still needs a `CLAUDE_API_KEY` in `backend/.env` to use Claude; without one the
  template message is used, as before.

---

## Notes for the slides (be honest)

- Slide 5: Gemini 2.0 Flash is no longer available → **Gemini 2.5 Flash, with
  2.5 Flash-Lite fallback**.
- Slides 4, 5 (5,000 images, YOLOv8, SAM) — **not built**. Move to roadmap.
- Slides 7, 9 (F1 88.4 %, 1.15 s, 14.2 %, generic-API comparison) — **not
  measured**. Replace with the Step 7 table: 15/15 dishes named, ~5 s median.
- Slide 6 "built" items are now true for: scanner UI, image upload API,
  calorie estimation (from dataset × estimated grams), dietary alerts.
- Portion size = Gemini's gram estimate, editable by the parent. Not SAM/depth.

## How to run

```bash
# backend (needs GEMINI_API_KEY in backend/.env)
cd backend
uv pip install -e ".[dev]"
python -m uvicorn src.main:app --port 8000

# frontend (second terminal)
cd frontend
npm install
npm run dev        # open http://localhost:5173 → Meal Logger tab → Scan a Meal Photo
```
