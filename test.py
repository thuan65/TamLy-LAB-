"""
Simple runner for manual testing (great inside PyCharm).

— MODULE OVERVIEW —
Iterates over sample inputs, calls recommend(), and prints JSON results.
If the necessary city JSON databases do not exist yet, they will be built
on demand by therapists_recommender via database_fetcher.

— QUICK START —
1) Ensure you've installed dependencies and created .env.
2) Run:   python test.py
3) Inspect the printed JSON (needs + top matches) for each sample input.

Tip: Replace/extend 'samples' to test more user scenarios.
"""
from __future__ import annotations
from therapists_recommender import recommend
import json

if __name__ == "__main__":
    samples = [
         "Tôi ở Thanh Hóa, bị trầm cảm",
        #gọi ít thôi không nó bug :))) tràn api gemini á
    ]
    for s in samples:
        print("\n=== INPUT ===\n", s)
        out = recommend(s, top_k=5)
        print("\n=== OUTPUT ===\n", json.dumps(out, ensure_ascii=False, indent=2))
