#!/usr/bin/env python3
"""
JSON-Only Database Builder for Mental-Health Providers (via SerpAPI Google Maps)

Features
--------
- Collect providers for given cities & search terms using SerpAPI (engine=google_maps)
- Robust fetching with basic retry & error detection
- Normalize common fields to a clean JSON schema
- Dedupe across multiple terms per city
- Atomic write to avoid broken JSON files
- Simple CLI + friendly console logs

Quick Start
-----------
1) Install deps:
   pip install serpapi python-dotenv

2) Put your SerpAPI key in a .env file next to this script:
   SERPAPI_API_KEY=your_api_key_here

3) Run with defaults (Hanoi, Ho Chi Minh City, Da Nang):
   python database_fetcher.py

4) Custom:
   python database_fetcher.py --cities "Hanoi" "Ho Chi Minh City" --terms "psychologist" "mental health clinic" --pages 2 --hl vi

Output
------
- Creates/updates JSON files under ./database/<City>_therapists.json
"""

from __future__ import annotations
import os
import json
import time
import argparse
import tempfile
from typing import List, Dict, Any

# Optional .env loader (won't crash if missing)
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    def load_dotenv() -> None:
        return

# SerpAPI client (if missing, give a clear message)
try:
    from serpapi import GoogleSearch  # type: ignore
except ImportError as e:
    raise SystemExit("Missing dependency 'serpapi'. Install it with: pip install serpapi") from e


# ---------------------------
# Utilities
# ---------------------------

def safe_name(s: str) -> str:
    """Make a filesystem-safe name: replace spaces and remove risky chars."""
    keep = []
    for ch in s:
        if ch.isalnum() or ch in ("_", "-"):
            keep.append(ch)
        elif ch.isspace():
            keep.append("_")
        else:
            # skip other punctuation
            continue
    return "".join(keep) or "output"


def write_json_atomic(data: Any, out_path: str) -> None:
    """
    Write JSON atomically: write to temp file then replace.
    Guarantees either old file or new valid JSON—never a half-written file.
    """
    dir_name = os.path.dirname(out_path) or "."
    os.makedirs(dir_name, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".tmp_", dir=dir_name, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp_path, out_path)
    except Exception:
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        raise


def normalize_local_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a Google Maps local result item to a compact schema.
    Fields may be missing; keep None where unknown.
    """
    gps = item.get("gps_coordinates") or {}
    return {
        "name": item.get("title") or item.get("name"),
        "address": item.get("address"),
        "rating": item.get("rating"),
        "reviews": item.get("reviews") or item.get("reviews_count"),
        "phone": item.get("phone"),
        "website": item.get("website"),
        "category": item.get("type") or item.get("category"),
        "google_maps_url": gps.get("link") or item.get("link"),
        "latitude": gps.get("latitude"),
        "longitude": gps.get("longitude"),
    }


def is_serpapi_error(resp: Any) -> str | None:
    """Return error message if response indicates SerpAPI error; else None."""
    if not isinstance(resp, dict):
        return "Non-dict response from SerpAPI"
    err = resp.get("error")
    if err:
        return str(err)
    # Sometimes error-like info hides elsewhere; extend if needed.
    return None


def serpapi_maps_search(
    query: str,
    api_key: str,
    hl: str = "vi",
    max_pages: int = 2,
    per_page_pause_s: float = 1.2,
    retries: int = 2,
    backoff_s: float = 1.5,
) -> List[Dict[str, Any]]:
    """
    Fetch multiple pages of Google Maps results from SerpAPI.
    - Uses 'local_results' list if present.
    - Basic retry on transient exceptions.
    - Stops if no pagination token found.
    """
    collected: List[Dict[str, Any]] = []
    next_page_param: Any = None

    for page_idx in range(max_pages):
        params: Dict[str, Any] = {
            "engine": "google_maps",
            "q": query,
            "hl": hl,
            "api_key": api_key,
            # "type": "search",  # Uncomment if needed
        }
        if next_page_param is not None:
            params["start"] = next_page_param  # SerpAPI sometimes uses 'start' for pagination

        attempt = 0
        while True:
            attempt += 1
            try:
                resp = GoogleSearch(params).get_dict()
            except Exception as e:
                if attempt <= retries:
                    print(f"[WARN] SerpAPI exception (attempt {attempt}/{retries}) page {page_idx+1}: {e}")
                    time.sleep(backoff_s * attempt)
                    continue
                print(f"[ERROR] SerpAPI exception: {e}")
                return collected

            err_msg = is_serpapi_error(resp)
            if err_msg:
                print(f"[ERROR] SerpAPI returned error: {err_msg}")
                return collected

            local_results = resp.get("local_results") or []
            if not isinstance(local_results, list):
                local_results = []

            for raw in local_results:
                collected.append(normalize_local_item(raw))

            # Try to detect pagination
            pag = resp.get("serpapi_pagination") or {}
            next_page_param = None
            if isinstance(pag, dict):
                # Some schemas expose next page token differently (adjust if needed)
                next_page_param = pag.get("next_page_token") or pag.get("next")

            break  # break retry loop, page fetched OK

        if not next_page_param:
            # No more pages
            break

        time.sleep(per_page_pause_s)

    return collected


def dedupe_providers(providers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Dedupe by (lower(name), lower(address))."""
    seen: set[tuple[Any, Any]] = set()
    unique: List[Dict[str, Any]] = []
    for p in providers:
        key = (
            (p.get("name") or "").strip().lower(),
            (p.get("address") or "").strip().lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(p)
    return unique


def verify_json(path: str) -> None:
    """Open the file and json.load to ensure validity; raises on error."""
    with open(path, "r", encoding="utf-8") as f:
        json.load(f)


# ---------------------------
# Core workflow
# ---------------------------

def build_city_database(
    city: str,
    terms: List[str],
    out_path: str,
    api_key: str,
    hl: str = "vi",
    pages: int = 2,
    sleep_s: float = 1.2,
) -> None:
    """
    Build one city JSON by merging & deduping results from multiple terms.
    Writes atomically and verifies JSON integrity.
    """
    print(f"\n=== Building database for: {city} ===")
    all_items: List[Dict[str, Any]] = []

    for term in terms:
        query = f"{term} in {city}"
        print(f"[Fetch] {query}")
        batch = serpapi_maps_search(
            query=query,
            api_key=api_key,
            hl=hl,
            max_pages=pages,
            per_page_pause_s=sleep_s,
        )
        print(f"[Fetch] -> {len(batch)} items")
        all_items.extend(batch)

    deduped = dedupe_providers(all_items)
    print(f"[Dedupe] -> {len(deduped)} unique providers")

    write_json_atomic(deduped, out_path)
    verify_json(out_path)
    print(f"[OK] JSON valid → {out_path}")


# ---------------------------
# CLI
# ---------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build JSON databases of mental-health providers via SerpAPI (Google Maps)."
    )
    parser.add_argument(
        "--cities",
        nargs="+",
        default=["Hanoi", "Ho Chi Minh City", "Da Nang"],
        help="City names (default: Hanoi, Ho Chi Minh City, Da Nang)",
    )
    parser.add_argument(
        "--terms",
        nargs="+",
        default=["psychologist", "psychiatrist", "mental health clinic"],
        help="Search terms per city.",
    )
    parser.add_argument(
        "--outdir",
        default="database",
        help="Output folder (default: database)",
    )
    parser.add_argument(
        "--hl",
        default="vi",
        help="Interface language for Google (hl) e.g., vi or en (default: vi)",
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=2,
        help="Max pages per query (default: 2)",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=1.2,
        help="Pause seconds between pages (default: 1.2)",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()  # Load SERPAPI_API_KEY if .env exists
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        raise SystemExit("Missing SERPAPI_API_KEY (set in environment or .env)")

    args = parse_args()
    outdir = args.outdir
    os.makedirs(outdir, exist_ok=True)

    for city in args.cities:
        file_name = f"{safe_name(city)}_therapists.json"
        out_path = os.path.join(outdir, file_name)
        try:
            build_city_database(
                city=city,
                terms=args.terms,
                out_path=out_path,
                api_key=api_key,
                hl=args.hl,
                pages=args.pages,
                sleep_s=args.sleep,
            )
        except Exception as e:
            # Keep going with other cities, but print error clearly
            print(f"[ERROR] Failed for city '{city}': {e}")

    print("\nAll done.")


if __name__ == "__main__":
    main()
