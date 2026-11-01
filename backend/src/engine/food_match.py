"""
Food Match Module.

Maps one food part described by the vision model (base ingredient, cooking method,
fat medium, grams) to the closest row of the Indian Dishes dataset.

Rows are blocked by base ingredient first (130 blocks of ~240 rows), so each lookup
fuzzy-matches against 130 ingredient names and then scores only one block —
never all 20,000 rows.
"""
from typing import Dict, List, Any, Optional, Tuple
import re

from rapidfuzz import fuzz, process, utils

_STYLE_PATTERN = re.compile(r"\[(.*?)\]")


def build_dish_index(dishes: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group dish rows by base ingredient (the blocking key)."""
    index: Dict[str, List[Dict[str, Any]]] = {}
    for dish in dishes:
        index.setdefault(dish["base_ingredient"], []).append(dish)
    return index


def resolve_base_ingredient(
    name: Optional[str],
    base_names: List[str],
    min_score: float
) -> Optional[Tuple[str, float]]:
    """Return (dataset ingredient name, score 0-100) for a model-supplied name, or None."""
    if not name:
        return None
    if name in base_names:
        return name, 100.0

    result = process.extractOne(
        name,
        base_names,
        scorer=fuzz.WRatio,
        processor=utils.default_process,
        score_cutoff=min_score,
    )
    if result is None:
        return None
    return result[0], float(result[1])


def dish_style(dish_name: str) -> Optional[str]:
    """Extract the style tag, e.g. 'Home-Style' from '... [Home-Style]'."""
    found = _STYLE_PATTERN.search(dish_name or "")
    return found.group(1) if found else None


def clamp_grams(grams: Optional[float], config: Dict[str, Any]) -> float:
    """Keep the model's portion estimate inside sane bounds from config."""
    matching = config["matching"]
    if grams is None or grams <= 0:
        return float(matching["default_grams"])
    return float(min(max(grams, matching["min_grams"]), matching["max_grams"]))


def _attribute_points(dish: Dict[str, Any], part: Dict[str, Any], config: Dict[str, Any]) -> float:
    weights = config["matching"]["weights"]
    points = 0.0

    if part.get("cooking_method") and dish.get("cooking_method") == part["cooking_method"]:
        points += weights["cooking_method"]
    if part.get("fat_medium") and dish.get("fat_medium") == part["fat_medium"]:
        points += weights["fat_medium"]

    # Rows without a style tag (e.g. plain boiled) count as the default style
    style = dish_style(dish.get("dish_name", ""))
    if style is None or style == config["matching"]["default_style"]:
        points += weights["style"]

    return points


def match_food_part(
    part: Dict[str, Any],
    index: Dict[str, List[Dict[str, Any]]],
    config: Dict[str, Any],
    base_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Find the best dataset row for one food part.

    Args:
        part: Dict with 'base_ingredient', optional 'cooking_method', 'fat_medium',
              'grams' and 'model_confidence' (0-1, from the vision model).
        index: Output of build_dish_index.
        config: Parsed food_scanner.yaml.
        base_names: Optional precomputed list(index.keys()) to avoid rebuilding per call.

    Returns:
        Dict with 'matched', 'dish', 'grams', 'confidence', 'possible_match'.
    """
    matching = config["matching"]
    names = base_names if base_names is not None else list(index.keys())
    grams = clamp_grams(part.get("grams"), config)

    resolved = resolve_base_ingredient(
        part.get("base_ingredient"), names, matching["base_ingredient_min_score"]
    )
    if resolved is None:
        return {
            "matched": False,
            "dish": None,
            "grams": grams,
            "confidence": 0.0,
            "possible_match": False,
        }

    base_name, base_score = resolved
    block = index[base_name]

    # First row wins ties, so results are stable between runs
    best_dish = block[0]
    best_points = -1.0
    for dish in block:
        points = _attribute_points(dish, part, config)
        if points > best_points:
            best_dish, best_points = dish, points

    weights = matching["weights"]
    max_points = weights["cooking_method"] + weights["fat_medium"] + weights["style"]
    attribute_fraction = best_points / max_points if max_points else 1.0

    attribute_weight = matching["attribute_weight"]
    model_confidence = float(part.get("model_confidence", 1.0))
    confidence = (
        (base_score / 100.0)
        * model_confidence
        * ((1.0 - attribute_weight) + attribute_weight * attribute_fraction)
    )
    confidence = round(min(max(confidence, 0.0), 1.0), 3)

    return {
        "matched": True,
        "dish": best_dish,
        "grams": grams,
        "confidence": confidence,
        "possible_match": confidence < matching["min_confidence"],
    }
