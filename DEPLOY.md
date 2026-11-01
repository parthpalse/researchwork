# Deploying NutriScan (free, ~10 minutes)

The whole app — API and website — runs as **one Docker service on Render's free plan**,
using `Dockerfile` and `render.yaml` in this repo. You get one public HTTPS link that
works on laptops and phones, and phones can install it like an app.

Tested locally on 2026-11-02: the image builds, starts in ~12 s, serves the app and
API on Render's `$PORT`, contains no `.env`, and scans a food photo via Gemini.

## 1. Before you start

- A **new Gemini API key** from https://aistudio.google.com/ → *Get API key*.
  (The old key was pasted in a chat — delete it there first.)
- Optional: a Claude API key, if you want AI-written parent messages
  (without it, the built-in template message is used).

## 2. Deploy on Render

1. Go to https://render.com and **sign up with your GitHub account** (`parthpalse`).
2. Dashboard → **New +** → **Blueprint**.
3. Connect / select the repository **`parthpalse/researchwork`**, branch **`main`**.
4. Render reads `render.yaml` and shows one service, **`nutriscan`** (Docker, Free,
   Singapore). It asks for the two secret values:
   - `GEMINI_API_KEY` → paste your new key
   - `CLAUDE_API_KEY` → paste a key, or leave empty
5. Click **Apply / Deploy**. The first build takes about 5–10 minutes.
6. When it says **Live**, open the link it shows, e.g.
   `https://nutriscan-xxxx.onrender.com`.
   Check `https://<your-link>/api/health` shows `{"status":"ok",...}`.

Keys live only in Render's dashboard (Environment tab) — never in the repo.
Every push to `main` redeploys automatically.

## 3. Install it on a phone

- **Android (Chrome):** open the link → menu ⋮ → **Install app** / **Add to Home screen**.
- **iPhone (Safari):** open the link → Share → **Add to Home Screen**.

It opens full screen with its own icon. The camera works for meal photos because the
link is HTTPS.

## Things to know about the free plan

| Behaviour | What it means for you |
|---|---|
| Sleeps after ~15 min without visitors | First open after a break takes ~30–60 s. **Open the link a minute before a demo.** |
| No permanent disk | Children, assessments and meal logs are **reset when the service restarts or redeploys**. The 20,000 dishes reload automatically. Fine for demos; for real users add a database (e.g. Supabase/Render Postgres) later. |
| Gemini free quota (~20 scans/day per model) | Shared by everyone using the link. Falls back to Flash-Lite automatically. |

## Run the same container on your laptop (optional)

Start Docker Desktop, then from the repo root:

```bash
docker build -t nutriscan .
docker run --rm -p 8000:8000 --env-file backend/.env nutriscan
# open http://localhost:8000
```

## Troubleshooting

- **Build fails on Render:** open the service → *Events* / *Logs*; the last red lines
  say why. Most often a typo in a key is not the cause (keys are only used at runtime).
- **Scanner says "not configured":** `GEMINI_API_KEY` is missing — add it in
  *Environment* and Render restarts the service.
- **Scanner says "limit is used up":** free Gemini quota reached; resets daily at
  ~1:30 PM IST.
