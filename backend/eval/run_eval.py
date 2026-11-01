"""
Food scanner benchmark: dish recognition and latency on a fixed, labelled photo set.

Photos are Wikimedia Commons files listed in eval/photos.csv (downloaded on first run
into eval/photos/, not committed — see each file's Commons page for its licence).
Each photo is shrunk to 640 px JPEG like the browser does, sent to a RUNNING backend,
and counted correct if any expected name appears in the names Gemini returned.

Usage (backend running on :8000):
    cd backend
    uv pip install -e ".[dev,eval]"
    python eval/run_eval.py                # all photos
    python eval/run_eval.py --limit 3      # first 3 (each photo uses 1 Gemini request)

Writes eval/results/<timestamp>.json and .md. Free tier is ~20 requests/day/model.
"""
import argparse
import base64
import csv
import io
import json
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from PIL import Image
from rapidfuzz import fuzz, utils

EVAL_DIR = Path(__file__).parent
PHOTO_DIR = EVAL_DIR / "photos"
RESULT_DIR = EVAL_DIR / "results"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "NutritionRiskSystem-eval/0.1 (+https://github.com/parthpalse/researchwork)"
MAX_SIDE = 640
JPEG_QUALITY = 80
NAME_MATCH_SCORE = 90  # rapidfuzz partial_ratio needed to count a name as matching


def download_photo(client: httpx.Client, commons_file: str, dest: Path) -> None:
    """Resolve a Commons file title to a 960 px thumbnail URL and save it."""
    params = {"action": "query", "titles": f"File:{commons_file}", "prop": "imageinfo",
              "iiprop": "url", "iiurlwidth": 960, "format": "json"}
    pages = client.get(COMMONS_API, params=params).json()["query"]["pages"]
    page = next(iter(pages.values()))
    if "imageinfo" not in page:
        raise RuntimeError(f"Commons file not found: {commons_file}")
    url = page["imageinfo"][0].get("thumburl") or page["imageinfo"][0]["url"]
    response = client.get(url)
    response.raise_for_status()
    dest.write_bytes(response.content)
    time.sleep(1.0)  # be polite to Wikimedia


def to_jpeg_base64(path: Path) -> str:
    img = Image.open(path).convert("RGB")
    img.thumbnail((MAX_SIDE, MAX_SIDE))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=JPEG_QUALITY)
    return base64.b64encode(buf.getvalue()).decode()


def is_correct(expected: list, names: list) -> bool:
    return any(
        fuzz.partial_ratio(e, n, processor=utils.default_process) >= NAME_MATCH_SCORE
        for e in expected for n in names
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default="http://127.0.0.1:8000")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--age-months", type=int, default=72)
    args = parser.parse_args()

    with open(EVAL_DIR / "photos.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))[: args.limit]

    PHOTO_DIR.mkdir(exist_ok=True)
    RESULT_DIR.mkdir(exist_ok=True)
    results = []

    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=60, follow_redirects=True) as web:
        for row in rows:
            photo = PHOTO_DIR / f"{row['id']}.jpg"
            if not photo.exists():
                download_photo(web, row["commons_file"], photo)

            expected = row["expected"].split("|")
            started = time.perf_counter()
            r = httpx.post(f"{args.server}/api/identify-food", timeout=120, json={
                "image_base64": to_jpeg_base64(photo), "mime_type": "image/jpeg",
                "age_months": args.age_months})
            wall_ms = round((time.perf_counter() - started) * 1000)

            if r.status_code != 200:
                print(f"{row['id']:15} ERROR HTTP {r.status_code}: {r.text[:120]}")
                results.append({"id": row["id"], "status": r.status_code, "error": r.text[:300]})
                if r.status_code == 429:
                    print("Free Gemini quota used up — stopping. Re-run later.")
                    break
                continue

            data = r.json()
            names = [item["name"] for item in data["items"]]
            correct = is_correct(expected, names)
            print(f"{row['id']:15} {'OK ' if correct else 'MISS'} {data['latency_ms']:>6} ms  "
                  f"{data['model']:22} {', '.join(names)}")
            results.append({
                "id": row["id"], "status": 200, "expected": expected, "identified": names,
                "correct": correct, "model": data["model"], "server_ms": data["latency_ms"],
                "wall_ms": wall_ms, "unmatched": data["unmatched"],
                "energy_kcal": data["totals"]["energy_kcal"],
                "alerts": [a["type"] for a in data["alerts"]],
            })

    scored = [r for r in results if r["status"] == 200]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (RESULT_DIR / f"{stamp}.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    lines = [f"# Food scanner benchmark — {stamp}", "",
             f"Photos attempted: {len(results)} · scored: {len(scored)} · server: {args.server}", ""]
    if scored:
        lat = [r["server_ms"] for r in scored]
        correct = sum(r["correct"] for r in scored)
        models = sorted({r["model"] for r in scored})
        lines += [
            "| Measure | Result |", "|---|---|",
            f"| Main dish named correctly | {correct} / {len(scored)} ({100 * correct / len(scored):.0f} %) |",
            f"| Server latency (ms) | min {min(lat)} · median {statistics.median(lat):.0f} · max {max(lat)} |",
            f"| Model(s) that answered | {', '.join(models)} |", "",
            "| Photo | Expected | Identified | OK | ms |", "|---|---|---|---|---|",
        ]
        lines += [f"| {r['id']} | {' / '.join(r['expected'])} | {', '.join(r['identified'])} | "
                  f"{'✅' if r['correct'] else '❌'} | {r['server_ms']} |" for r in scored]
    (RESULT_DIR / f"{stamp}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nReport: {RESULT_DIR / (stamp + '.md')}")


if __name__ == "__main__":
    main()
