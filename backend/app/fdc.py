# backend/app/fdc.py  # (rename from idc.py or update your import in main.py)
import os
from typing import Dict, Any, Optional, Tuple
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- Config ---
FDC_BASE = os.getenv("FDC_BASE", "https://api.nal.usda.gov/fdc")
FDC_TIMEOUT = float(os.getenv("FDC_TIMEOUT_S", "20"))
FDC_RETRIES = int(os.getenv("FDC_RETRIES", "3"))

def _make_session() -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=FDC_RETRIES,
        backoff_factor=0.3,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
        raise_on_status=False,
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://", HTTPAdapter(max_retries=retry))
    return s

class FDCClient:
    """Thin wrapper around USDA FDC Search + Details endpoints."""
    def __init__(self, api_key: Optional[str] = None, session: Optional[requests.Session] = None):
        self.api_key = api_key or os.getenv("USDA_FDC_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("Missing USDA_FDC_API_KEY")
        self.s = session or _make_session()

    def search(self, query: str, page_size: int = 10) -> Dict[str, Any]:
        params = {"api_key": self.api_key}
        payload = {"query": query, "pageSize": page_size}
        r = self.s.post(f"{FDC_BASE}/v1/foods/search", params=params, json=payload, timeout=FDC_TIMEOUT)
        r.raise_for_status()
        return r.json()


    def details(self, fdc_id: int) -> Dict[str, Any]:
        params = {"api_key": self.api_key}
        r = self.s.get(f"{FDC_BASE}/v1/food/{fdc_id}", params=params, timeout=FDC_TIMEOUT)
        r.raise_for_status()
        return r.json()

# Common nutrient IDs
ENERGY_NUTR_IDS = {1008, 2047}   # kcal, Energy (Atwater general)
PROTEIN_ID = 1003
FAT_ID = 1004
CARB_ID = 1005
FIBER_ID = 1079
SODIUM_ID = 1093
SUGAR_ID = 2000

def pick_best_food(search_json: Dict[str, Any]):
    """Prefer SR/Survey, then Branded, then everything else. Tie-break on FDC's score."""
    items = search_json.get("foods") or []
    if not items:
        return None
    items_sorted = sorted(
        items,
        key=lambda x: (
            0 if (x.get("dataType", "") or "").lower() in {"survey (fndds)", "sr legacy"} else
            1 if (x.get("dataType", "") or "").lower() == "branded" else 2,
            -float(x.get("score", 0.0)),
        ),
    )
    return items_sorted[0]

def extract_serving(food_json: Dict[str, Any]) -> Tuple[float, str]:
    """
    Return a (amount, unit) tuple. Prefer explicit servingSize/unit.
    Fallback to first gramWeight found. Default to (100, 'g').
    """
    serving_size = food_json.get("servingSize")
    serving_unit = food_json.get("servingSizeUnit")
    if serving_size and serving_unit:
        try:
            return float(serving_size), str(serving_unit)
        except Exception:
            pass

    # Branded & survey records often include gramWeight under portions/foodPortions
    for key in ("foodPortions", "portions"):
        portions = food_json.get(key) or []
        for p in portions:
            gram_weight = p.get("gramWeight")
            if gram_weight:
                try:
                    return float(gram_weight), "g"
                except Exception:
                    continue

    return 100.0, "g"

def _collect_food_nutrients(food_json: Dict[str, Any]) -> Dict[int, float]:
    """
    Build a map of nutrient_id -> amount from both 'foodNutrients' and
    (when present) 'labelNutrients' found in branded foods.
    Units:
      - calories/protein/fat/carb/fiber/sugars are typically grams (sodium is mg) in labelNutrients.
      - foodNutrients already report amounts with IDs consistent with our expectations.
    """
    out: Dict[int, float] = {}

    # 1) Standard foodNutrients list
    for n in food_json.get("foodNutrients", []) or []:
        nid = (n.get("nutrient") or {}).get("id") or n.get("nutrientId")
        amt = n.get("amount")
        if nid is None or amt is None:
            continue
        try:
            out[int(nid)] = float(amt)
        except Exception:
            pass

    # 2) Branded labelNutrients (per serving)
    # Map common label keys to FDC nutrient IDs
    ln = food_json.get("labelNutrients") or {}
    label_map = {
        "calories": 1008,
        "protein": PROTEIN_ID,
        "fat": FAT_ID,
        "carbohydrates": CARB_ID,
        "fiber": FIBER_ID,
        "sugars": SUGAR_ID,
        "sodium": SODIUM_ID,  # typically mg
    }
    for k, nid in label_map.items():
        node = ln.get(k)
        if not isinstance(node, dict):
            continue
        amt = node.get("value")
        if amt is None:
            continue
        try:
            # For sodium, label is usually mg already; others are grams/kcal as expected.
            out.setdefault(nid, float(amt))
        except Exception:
            pass

    return out

def nutrients_by_id(food_json: Dict[str, Any]) -> Dict[int, float]:
    """Public helper: nutrient_id -> amount."""
    return _collect_food_nutrients(food_json)

def summarize_macros(food_json: Dict[str, Any]) -> Dict[str, float]:
    """
    Return a compact macro dict expected by the UI/backend:
      - calories_kcal, protein_g, fat_g, carb_g, fiber_g, sodium_mg, sugars_g
    """
    ns = nutrients_by_id(food_json)

    def get_any(ids, default=None):
        for i in ids if isinstance(ids, (list, set, tuple)) else [ids]:
            if i in ns:
                return ns[i]
        return default

    return {
        "calories_kcal": get_any(ENERGY_NUTR_IDS, 0.0),
        "protein_g": get_any(PROTEIN_ID, 0.0),
        "fat_g": get_any(FAT_ID, 0.0),
        "carb_g": get_any(CARB_ID, 0.0),
        "fiber_g": get_any(FIBER_ID, 0.0),
        "sodium_mg": get_any(SODIUM_ID, 0.0),  # mg as expected by UI
        "sugars_g": get_any(SUGAR_ID, 0.0),
    }

def tips_from_profile(profile: Dict[str, float]):
    tips = []
    if profile.get("sodium_mg", 0) > 700:
        tips.append("High sodium: try low-sodium dressing or sauce.")
    if profile.get("fiber_g", 0) < 5:
        tips.append("Low fiber: add greens, beans, or whole grains.")
    if profile.get("protein_g", 0) < 15:
        tips.append("Boost protein with chicken, tofu, eggs, or legumes.")
    if profile.get("sugars_g", 0) > 20:
        tips.append("Sugary: keep dressing on the side or skip sweet drinks.")
    if not tips:
        tips.append("Nice balance! Pair with water and extra veggies if you like.")
    return tips[:3]

__all__ = [
    "FDCClient",
    "pick_best_food",
    "extract_serving",
    "nutrients_by_id",
    "summarize_macros",
    "tips_from_profile",
]
