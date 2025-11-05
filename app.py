"""
Therapist Recommender FastAPI Host
----------------------------------

Overview
--------
This FastAPI service hosts the therapist recommendation system.
It wraps `therapists_recommender.recommend()` into API endpoints
so a website or frontend app can call it easily.

Endpoints
---------
- GET  /health       : Health check (JSON).
- POST /recommend    : Analyze user text via Gemini + match therapist DB.
- POST /build        : (Optional) Build databases for major cities via SerpAPI.

How to run
----------
1) Install dependencies:
   pip install fastapi "uvicorn[standard]" python-dotenv google-generativeai google-search-results

2) Set up your `.env` file in the same directory:
   GEMINI_API_KEY=your_gemini_key_here
   SERPAPI_API_KEY=your_serpapi_key_here
   GEMINI_MODEL=gemini-2.5-pro

3) Start the server:
   uvicorn app:app --reload --port 8000

4) Test endpoints:
   - http://localhost:8000/health
   - POST http://localhost:8000/recommend
"""

from __future__ import annotations
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# Local imports
from therapists_recommender import recommend
from database_fetcher import build_city, DEFAULT_CITIES

# --- FastAPI setup -----------------------------------------------------------
app = FastAPI(title="Therapist Recommender API", version="1.0.0")

# Enable CORS for your frontend (adjust origin in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # replace with your website domain later
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# --- Models -----------------------------------------------------------------
class RecommendRequest(BaseModel):
    text: str
    topk: int = 5

class RecommendResponse(BaseModel):
    needs: dict
    city: str
    results: list

class BuildRequest(BaseModel):
    cities: Optional[List[str]] = None

# --- Endpoints --------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/recommend", response_model=RecommendResponse)
def post_recommend(payload: RecommendRequest):
    """
    Analyze user text → parse needs (Gemini) → load/build DB → rank therapists.
    """
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text is required.")
    try:
        result = recommend(payload.text.strip(), top_k=payload.topk)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")

@app.post("/build")
def post_build(payload: BuildRequest):
    """
    Manually trigger database build for given cities (defaults to the 3 major ones).
    """
    cities = payload.cities or DEFAULT_CITIES
    built = []
    for c in cities:
        path = build_city(c)
        built.append(path)
    return {"built": built, "count": len(built)}

# --- Entry point ------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
