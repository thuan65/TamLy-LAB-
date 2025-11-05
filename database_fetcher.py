"""
Build city-scoped JSON databases of mental-health providers using SerpAPI's Google Maps engine.

— MODULE OVERVIEW —
This script queries Google Maps (via SerpAPI) for mental-health providers in
three Vietnamese hubs: Ho Chi Minh City, Hanoi, and Da Nang. Results are
normalized, deduplicated, and saved to JSON files inside the ./database folder.
No SQLite is used.

— QUICK START —
1) Install dependencies:
       pip install python-dotenv serpapi
2) Create a .env file next to this script with:
       SERPAPI_API_KEY=your_serpapi_key_here
3) Run directly (build default 3 cities):
       python database_fetcher.py
   Or specify custom list:
       python database_fetcher.py --cities "Hanoi,Ho Chi Minh City,Da Nang"

— INPUTS —
- Environment variable SERPAPI_API_KEY from .env
- City list (default 3 hubs) and built-in search terms

— OUTPUTS —
- JSON files written to ./database:
      database/ho_chi_minh_city_therapists.json
      database/hanoi_therapists.json
      database/da_nang_therapists.json
  Each file is a list of provider objects with fields: name, address, rating,
  reviews, phone, website, category, city, lat, lng, source.

— ERROR HANDLING —
- Missing dependencies raise a clear message with the pip command to install.
- Missing SERPAPI_API_KEY causes an immediate exit with instructions.

— TROUBLESHOOTING —
- If you see few results, try different SEARCH_TERMS, or add hl/gl country hints.
- Watch for SerpAPI rate limits; adjust pause_sec in build_city.
"""
from __future__ import annotations
import os, json, time, argparse, re
from typing import Dict, Any, List
from dataclasses import dataclass

try:
    from dotenv import load_dotenv  # Loads variables from .env into environment
except ImportError:
    raise SystemExit("Missing dependency 'python-dotenv'. Install it with: pip install python-dotenv")

try:
    from serpapi import GoogleSearch  # SerpAPI Python client
except ImportError:
    raise SystemExit("Missing dependency 'serpapi'. Install it with: pip install serpapi")

# Load .env file (expects SERPAPI_API_KEY)
load_dotenv()
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
if not SERPAPI_API_KEY:
    raise SystemExit("SERPAPI_API_KEY not found. Create a .env with SERPAPI_API_KEY=... next to this script.")

DATABASE_DIR = os.path.join(os.path.dirname(__file__), "database")

DEFAULT_CITIES = [
    "Ho Chi Minh City",
    "Hanoi",
    "Da Nang",
]

SEARCH_TERMS = [
    # Vietnamese
    "bác sĩ tâm thần", "tâm lý gia", "phòng khám tâm lý", "trị liệu tâm lý", "trị liệu CBT",
    # English
    "psychiatrist", "psychologist", "mental health clinic", "counseling center", "CBT therapy",
]


def safe_name(s: str) -> str:
    """Convert any string into a lowercase, underscore-separated safe filename."""
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return re.sub(r"_+", "_", s).strip("_")

@dataclass
class Provider:
    """Structured provider record after normalization."""
    name: str
    address: str | None
    rating: float | None
    reviews: int | None
    phone: str | None
    website: str | None
    category: str | None
    city: str
    lat: float | None
    lng: float | None
    source: str

    def key(self) -> str:
        """Unique key to deduplicate results using (name + address)."""
        return f"{(self.name or '').strip().lower()}||{(self.address or '').strip().lower()}"

    def as_dict(self) -> Dict[str, Any]:
        """Serialize to plain dict for JSON dumping."""
        return {
            "name": self.name,
            "address": self.address,
            "rating": self.rating,
            "reviews": self.reviews,
            "phone": self.phone,
            "website": self.website,
            "category": self.category,
            "city": self.city,
            "lat": self.lat,
            "lng": self.lng,
            "source": self.source,
        }

def serp_maps_search(city: str, query: str) -> List[Dict[str, Any]]:
    params = {
        "engine": "google_maps",
        "type": "search",
        "q": f"{query} in {city}, Vietnam",
        "location": f"{city}, Vietnam",
        "hl": "vi",               # vietnamese
        "gl": "vn",               # Vietnam
        "google_domain": "google.com.vn",
        "api_key": SERPAPI_API_KEY,
        "no_cache": True
    }
    search = GoogleSearch(params)
    result = search.get_dict()
    chunks = []
    for key in ("local_results", "place_results", "results"):
        if key in result and isinstance(result[key], list):
            chunks.extend(result[key])
    if not chunks and isinstance(result.get("place_results"), dict):
        chunks.append(result["place_results"])
    return chunks


def parse_provider(raw: Dict[str, Any], city: str, query: str) -> Provider | None:
    """Convert a raw SerpAPI record into our Provider structure."""
    name = raw.get("title") or raw.get("name")
    address = raw.get("address") or raw.get("formatted_address")
    rating = float(raw.get("rating")) if isinstance(raw.get("rating"), (int, float)) else None
    reviews = next((int(v) for k, v in raw.items() if k in ("reviews", "user_ratings_total", "reviews_count") and isinstance(v, (int, float))), None)
    phone = raw.get("phone") or raw.get("phone_number")
    website = raw.get("website") or raw.get("link") or raw.get("google_maps_url")
    category = raw.get("type") or raw.get("category") or (raw.get("types")[0] if isinstance(raw.get("types"), list) else None)
    gps = raw.get("gps_coordinates") or raw.get("latlng")
    lat, lng = (gps.get("latitude"), gps.get("longitude")) if isinstance(gps, dict) else (None, None)
    if not name: return None
    return Provider(name, address, rating, reviews, phone, website, category, city, lat, lng, f"serpapi:{query}")

def build_city(city: str, out_dir: str = DATABASE_DIR, pause_sec: float = 0.8) -> str:
    """Fetch, normalize, deduplicate, and write JSON for a single city."""
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{safe_name(city)}_therapists.json")
    seen, all_items = {}, []
    for term in SEARCH_TERMS:
        raw_list = serp_maps_search(city, term)
        for raw in raw_list:
            p = parse_provider(raw, city, term)
            if not p: continue
            k = p.key()
            if k not in seen:
                seen[k] = p
                all_items.append(p)
        time.sleep(pause_sec)
    all_items.sort(key=lambda x: (-(x.rating or 0.0), -(x.reviews or 0), x.name.lower()))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump([p.as_dict() for p in all_items], f, ensure_ascii=False, indent=2)
    return out_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build therapists JSON databases via SerpAPI")
    parser.add_argument("--cities", type=str, default=",".join(DEFAULT_CITIES), help="Comma-separated city list. Default: the 3 major cities (HCMC, Hanoi, Da Nang)")
    args = parser.parse_args()
    cities = [c.strip() for c in args.cities.split(",") if c.strip()]
    print(f"Building databases for: {cities}")
    for c in cities:
        path = build_city(c)
        print(f"✔ Wrote: {path}")
