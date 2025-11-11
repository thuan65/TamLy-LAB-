#!/usr/bin/env python3
"""
Therapist Recommender (EN + VI Robust)
======================================

Purpose
-------
Provides a bilingual therapist recommendation engine that:
- Parses free-text user input (Vietnamese or English)
- Infers therapy needs, city, modality, budget, etc.
- Loads or auto-builds a therapist database (via SerpAPI)
- Scores and returns the best-matching clinics/providers

Main Features
-------------
- Dual-language support (English/Vietnamese)
- Automatic database creation for major cities (HCMC, Hanoi, Da Nang)
- Smart text normalization and accent-insensitive city routing
- Integration-ready for FastAPI backend or CLI execution

How to Use
----------
1. Install dependencies:
   pip install python-dotenv google-generativeai google-search-results

2. Set environment variables in `.env`:
   GEMINI_API_KEY=your_api_key_here
   GEMINI_MODEL=gemini-2.5-pro

3. Run from CLI:
   python therapists_recommender.py --text "I'm in Da Nang. Need CBT for anxiety." --topk 5

4. Or import and call:
   from therapists_recommender import recommend
   result = recommend("I’m in Hanoi, need online therapy for depression.")
"""

from __future__ import annotations
import os, json, re, unicodedata
from typing import Dict, Any, List
from functools import lru_cache
from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# Utility: Accent removal (for Vietnamese text normalization)
# -----------------------------------------------------------------------------
def _deaccent(s: str) -> str:
    if not isinstance(s, str):
        return ""
    nfkd = unicodedata.normalize("NFD", s)
    return "".join(ch for ch in nfkd if unicodedata.category(ch) != "Mn")

load_dotenv()

# -----------------------------------------------------------------------------
# Gemini Initialization
# -----------------------------------------------------------------------------
def _init_gemini():
    """Initialize and return a Gemini model instance."""
    try:
        import google.generativeai as genai
    except ImportError:
        raise SystemExit("Missing dependency 'google-generativeai'. Install it with: pip install google-generativeai")

    api_key = os.getenv("GEMINI_API_KEY", "AIzaSyAOCJATPmILXcQj5RmOSnfks0zetQFFOwI")
    if not api_key:
        raise SystemExit("Missing API key. Add GEMINI_API_KEY to your .env file.")

    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
    return genai.GenerativeModel(model_name)

# -----------------------------------------------------------------------------
# Language Detection
# -----------------------------------------------------------------------------
_EN_WORDS = {"the","and","for","need","english","therapy","online","cbt","anxiety","clinic"}
_VI_HINTS = {"tôi","mình","ở","bác sĩ","tâm lý","tâm thần","trực tiếp","trực tuyến"}

def detect_language(text: str) -> str:
    """Detects whether the text is likely English or Vietnamese."""
    t = text.lower()
    en_hits = sum(1 for w in _EN_WORDS if w in t)
    vi_hits = sum(1 for w in _VI_HINTS if w in t)
    if en_hits > vi_hits:
        return "en"
    if vi_hits > en_hits:
        return "vi"
    return "en" if re.fullmatch(r"[\x00-\x7F\s\W]+", text) else "vi"

# -----------------------------------------------------------------------------
# Text Utilities
# -----------------------------------------------------------------------------
def _as_lower_text(v) -> str:
    """Return a lowercased string representation for text/list/None."""
    if v is None:
        return ""
    if isinstance(v, list):
        return " ".join(str(x) for x in v if x is not None).lower()
    return str(v).lower()

def _coerce_str(v) -> str | None:
    """Convert a list or value to a string."""
    if v is None:
        return None
    if isinstance(v, list):
        return " ".join(str(x) for x in v if x)
    return str(v)

# -----------------------------------------------------------------------------
# City Resolution (Accent-insensitive, full Vietnam coverage)
# -----------------------------------------------------------------------------
HUB_HCMC  = "Ho Chi Minh City"
HUB_HANOI = "Hanoi"
HUB_DN    = "Da Nang"

# ===== Region sets (full) =====
NORTH_PROVINCES = [
    "Hà Nội","Hải Phòng","Quảng Ninh","Bắc Ninh","Bắc Giang","Lạng Sơn","Cao Bằng","Hà Giang",
    "Tuyên Quang","Thái Nguyên","Phú Thọ","Vĩnh Phúc","Hòa Bình","Sơn La","Điện Biên","Lai Châu",
    "Lào Cai","Yên Bái","Thái Bình","Hải Dương","Hưng Yên","Hà Nam","Nam Định","Ninh Bình"
]

CENTRAL_PROVINCES = [
    "Thanh Hóa","Nghệ An","Hà Tĩnh","Quảng Bình","Quảng Trị","Thừa Thiên Huế","Đà Nẵng",
    "Quảng Nam","Quảng Ngãi","Bình Định","Phú Yên","Khánh Hòa","Ninh Thuận","Bình Thuận",
    # Tây Nguyên
    "Kon Tum","Gia Lai","Đắk Lắk","Đắk Nông","Lâm Đồng"
]

SOUTH_PROVINCES = [
    "Hồ Chí Minh","Bà Rịa Vũng Tàu","Bình Dương","Bình Phước","Đồng Nai","Tây Ninh",
    "An Giang","Bạc Liêu","Bến Tre","Cà Mau","Cần Thơ","Đồng Tháp","Hậu Giang","Kiên Giang",
    "Long An","Sóc Trăng","Tiền Giang","Trà Vinh","Vĩnh Long"
]

PROVINCE_TO_HUB: dict[str, str] = {}

def _k(s: str) -> str:
    return _deaccent(s).lower().strip()

for name in SOUTH_PROVINCES:
    PROVINCE_TO_HUB[_k(name)] = HUB_HCMC
for name in CENTRAL_PROVINCES:
    PROVINCE_TO_HUB[_k(name)] = HUB_DN
for name in NORTH_PROVINCES:
    PROVINCE_TO_HUB[_k(name)] = HUB_HANOI

PROVINCE_TO_HUB.setdefault("tp ho chi minh", HUB_HCMC)
PROVINCE_TO_HUB.setdefault("tp hcm",        HUB_HCMC)
PROVINCE_TO_HUB.setdefault("sai gon",       HUB_HCMC)
PROVINCE_TO_HUB.setdefault("ha noi",        HUB_HANOI)
PROVINCE_TO_HUB.setdefault("hanoi",         HUB_HANOI)
PROVINCE_TO_HUB.setdefault("da nang",       HUB_DN)
PROVINCE_TO_HUB.setdefault("danang",        HUB_DN)

SUBREGION_ALIAS = {
    "thu duc": HUB_HCMC, "binh thanh": HUB_HCMC, "quan 1": HUB_HCMC,
    "ha dong": HUB_HANOI, "dong anh": HUB_HANOI,
    "hai chau": HUB_DN, "son tra": HUB_DN,
}

CITY_ALIASES = {
    "tp ho chi minh": HUB_HCMC, "tp. ho chi minh": HUB_HCMC,
    "ha noi": HUB_HANOI, "thanh pho ha noi": HUB_HANOI,
    "da nang": HUB_DN, "thanh pho da nang": HUB_DN,
}

def resolve_nearest_major_city(user_text: str) -> str:
    """Return the most likely major city hub (HCMC/Hanoi/Da Nang)."""
    raw = (user_text or "").lower()
    t = _deaccent(raw)

    for k, hub in CITY_ALIASES.items():
        if k in t: return hub
    for prov, hub in PROVINCE_TO_HUB.items():
        if prov in t: return hub
    for sub, hub in SUBREGION_ALIAS.items():
        if sub in t: return hub
    if "mien bac" in t: return HUB_HANOI
    if "mien trung" in t: return HUB_DN
    if "mien nam" in t: return HUB_HCMC
    return HUB_HCMC

# -----------------------------------------------------------------------------
# Gemini-based Needs Extraction
# -----------------------------------------------------------------------------
ANALYZE_SYS_PROMPT = (
    "You are a bilingual clinical triage assistant. Extract structured needs "
    "from Vietnamese or English input. Return strict JSON with these keys: "
    "city, nearest_major_city, condition, modality, budget_level, language, "
    "need_psychiatrist, specialties."
)

@lru_cache(maxsize=256)
def _cached_model():
    return _init_gemini()

def analyze_user_text(text: str) -> Dict[str, Any]:
    """Parse user input using Gemini + heuristic fallbacks."""
    lang = detect_language(text)
    user_tl = text.lower()
    model = _cached_model()

    user_msg = (
        f"{ANALYZE_SYS_PROMPT}\nUser language hint: {lang}.\nInput:\n{text.strip()}"
    )

    payload = None
    for _ in range(2):
        resp = model.generate_content(user_msg)
        raw = getattr(resp, "text", None)
        if raw:
            try:
                payload = json.loads(raw)
                break
            except Exception:
                pass

    if not payload or not isinstance(payload, dict):
        payload = {}

    out = {
        "city": _coerce_str(payload.get("city")),
        "nearest_major_city": payload.get("nearest_major_city") or resolve_nearest_major_city(text),
        "condition": (_coerce_str(payload.get("condition")) or "unspecified").lower(),
        "modality": "online" if "online" in user_tl else "in_person" if "trực tiếp" in user_tl else "either",
        "budget_level": "low" if "cheap" in user_tl or "rẻ" in user_tl else "unspecified",
        "language": payload.get("language") if isinstance(payload.get("language"), list) else [lang],
        "need_psychiatrist": bool(payload.get("need_psychiatrist")),
        "specialties": payload.get("specialties") if isinstance(payload.get("specialties"), list) else [],
    }

    return out

# -----------------------------------------------------------------------------
# Database Management (Auto-build + Load)
# -----------------------------------------------------------------------------
PROJECT_DIR = os.path.dirname(__file__)
DB_DIR = os.path.join(PROJECT_DIR, "database")

def _safe(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", s.lower())
    return s.strip("_")

def ensure_city_database(city: str) -> str:
    """Ensure a city-specific JSON database exists; build if missing."""
    path = os.path.join(DB_DIR, f"{_safe(city)}_therapists.json")
    if os.path.exists(path):
        return path
    from database_fetcher import build_city
    os.makedirs(DB_DIR, exist_ok=True)
    build_city(city)
    return path

def load_city(city: str) -> List[Dict[str, Any]]:
    """Load and normalize provider data from a JSON city database."""
    path = ensure_city_database(city)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    normed = []
    for p in data:
        q = dict(p)
        for k in ["category", "website", "address"]:
            if isinstance(q.get(k), list):
                q[k] = " ".join(str(x) for x in q[k] if x)
        normed.append(q)
    return normed

# -----------------------------------------------------------------------------
# Scoring Logic
# -----------------------------------------------------------------------------
def score_provider(p: Dict[str, Any], needs: Dict[str, Any]) -> float:
    """Compute a relevance score for a single provider."""
    score = 0.0

    if p.get("city") == needs.get("nearest_major_city"):
        score += 3.0

    cat = _as_lower_text(p.get("category"))
    if needs.get("need_psychiatrist") and "psychiat" in cat:
        score += 2.2
    if not needs.get("need_psychiatrist") and any(x in cat for x in ["psycholog", "counsel", "clinic"]):
        score += 1.6

    rating = float(p.get("rating") or 0)
    reviews = int(p.get("reviews") or 0)
    score += min(rating, 5.0) * 0.6
    score += min(reviews, 1500) * 0.002

    langs = set(needs.get("language", []))
    site_text = _as_lower_text(p.get("website")) + " " + _as_lower_text(p.get("name"))
    if "en" in langs and any(k in site_text for k in ["english", "/en"]):
        score += 0.6
    if "vi" in langs:
        score += 0.2

    return score

# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------
def recommend(text: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Main pipeline:
    1. Analyze user input via Gemini
    2. Resolve nearest major city
    3. Load corresponding provider database
    4. Rank and return top matches
    """
    needs = analyze_user_text(text)
    nearest = needs.get("nearest_major_city") or resolve_nearest_major_city(text)
    needs["nearest_major_city"] = nearest
    providers = load_city(nearest)

    scored = [(score_provider(p, needs), p) for p in providers]
    scored.sort(key=lambda x: x[0], reverse=True)

    return {
        "needs": needs,
        "city": nearest,
        "results": [p for _, p in scored[:top_k]]
    }

# -----------------------------------------------------------------------------
# Command-Line Interface
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Therapist recommender (EN+VI robust)")
    parser.add_argument("--text", type=str, required=True, help="Free-text user description (EN/VI)")
    parser.add_argument("--topk", type=int, default=5, help="Number of top results to show")
    args = parser.parse_args()

    out = recommend(args.text, top_k=args.topk)
    print(json.dumps(out, ensure_ascii=False, indent=2))
