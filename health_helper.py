"""

Overview
--------
This FastAPI service exposes two endpoints that return plain text (Markdown-friendly)
so a frontend can display the answer directly without parsing JSON or saving files.

Endpoints
---------
- GET  /health        : Quick health check.
- GET  /              : Minimal landing page (links to /docs).
- POST /stress_text   : Generate stress-reduction advice as plain text.
- POST /plan_text     : Generate a wellbeing plan as plain text.

How to run (development)
------------------------
1) Install dependencies:
   pip install fastapi "uvicorn[standard]" python-dotenv google-generativeai

2) Set environment variables in a .env file in the same directory:
   GEMINI_API_KEY=your_key_here
   GEMINI_MODEL=gemini-2.5-pro

3) Start the server:
   uvicorn health_helper:app --reload --port 8000

4) Open in browser:
   - http://localhost:8000/           (landing page)
   - http://localhost:8000/docs       (Swagger UI)

Frontend usage (example)
------------------------
fetch("http://localhost:8000/stress_text", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    text: "I feel nervous before presentations",
    context: {
      location: "Ho Chi Minh City",
      preferences: ["prefers_online"],
      constraints: ["limited_time"]
    }
  })
}).then(res => res.text()).then(console.log);
"""

from dataclasses import dataclass
from typing import List, Optional

import os
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────
# Load .env variables (GEMINI_API_KEY, GEMINI_MODEL)
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAOCJATPmILXcQj5RmOSnfks0zetQFFOwI")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")

if not API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY in environment or .env file.")

# Configure Gemini client
genai.configure(api_key=API_KEY)

# Generation config for plain text (no JSON)
GEN_CONFIG_TEXT = {
    "temperature": 0.4,        # Lower for stability and fewer mid-sentence cutoffs
    "top_p": 0.9,
    "max_output_tokens": 3072  # Increase room to reduce truncation
}

def _model():
    """Create a GenerativeModel instance for each request."""
    return genai.GenerativeModel(model_name=MODEL_NAME, generation_config=GEN_CONFIG_TEXT)

# ─────────────────────────────────────────────────────────────────────────────
# Data models
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class UserContext:
    """Lightweight context to personalize prompts."""
    age: Optional[int] = None
    location: Optional[str] = None
    preferences: Optional[List[str]] = None
    constraints: Optional[List[str]] = None

class ContextIn(BaseModel):
    """Input schema for optional context included with the request."""
    age: Optional[int] = None
    location: Optional[str] = "Viet Nam"
    preferences: Optional[List[str]] = ["prefers_online"]
    constraints: Optional[List[str]] = ["low_budget", "limited_time"]

class AskIn(BaseModel):
    """Input schema for user text + optional context."""
    text: str
    context: Optional[ContextIn] = None

# ─────────────────────────────────────────────────────────────────────────────
# Prompt builders (text mode)
# ─────────────────────────────────────────────────────────────────────────────
def _stress_prompt_text(user_text: str, ctx: Optional[UserContext]) -> str:
    """Build a concise, Markdown-friendly prompt for stress advice."""
    prefs = ", ".join(ctx.preferences) if (ctx and ctx.preferences) else "none"
    cons  = ", ".join(ctx.constraints) if (ctx and ctx.constraints) else "none"
    age = str(ctx.age) if (ctx and ctx.age is not None) else "unspecified"
    loc = ctx.location if (ctx and ctx.location) else "unspecified"
    return f"""
You are a careful, evidence-aligned mental health assistant (non-clinical).
Write a clear, concise Markdown answer with headings and bullet points.
Do not use code fences or backticks. Return plain text/Markdown only.

User:
- Age: {age}
- Location: {loc}
- Preferences: {prefs}
- Constraints: {cons}

Stress description:
\"\"\"{user_text}\"\"\"

Sections to include:
# Summary (non-diagnostic)
# Quick Wins (3–5 bullets; breathing/grounding/PMR; tiny habits)
# Cognitive/Behavioral (CBT-style reframing; worry scheduling)
# Lifestyle Levers (sleep hygiene; caffeine timing; physical activity)
# When to Escalate (red flags; caution)
"""

def _plan_prompt_text(user_text: str, ctx: Optional[UserContext]) -> str:
    """Build a concise, Markdown-friendly prompt for a wellbeing plan."""
    prefs = ", ".join(ctx.preferences) if (ctx and ctx.preferences) else "none"
    cons  = ", ".join(ctx.constraints) if (ctx and ctx.constraints) else "none"
    age = str(ctx.age) if (ctx and ctx.age is not None) else "unspecified"
    loc = ctx.location if (ctx and ctx.location) else "unspecified"
    return f"""
You are a behavior-change coach (non-clinical).
Return a readable Markdown plan (no code fences, no JSON).

User:
- Age: {age}
- Location: {loc}
- Preferences: {prefs}
- Constraints: {cons}

Goal/context:
\"\"\"{user_text}\"\"\"

Include:
# Overview
# Pillars
- Sleep: Tier 1/2/3 with short steps
- Activity: Tier 1/2/3
- Cognition: Tier 1/2/3
- Social: Tier 1/2/3
- Lifestyle: Tier 1/2/3
# 4-Week Progression (Week 1–4)
# Tiny Rewards & Skip Rules
"""

# ─────────────────────────────────────────────────────────────────────────────
# Text generation helper
# ─────────────────────────────────────────────────────────────────────────────
def _extract_text_from_response(resp) -> str:
    """Robustly extract text from a Gemini Response object."""
    try:
        if hasattr(resp, "text") and resp.text:
            return resp.text
    except Exception:
        pass

    candidates = getattr(resp, "candidates", []) or []
    for cand in candidates:
        content = getattr(cand, "content", None)
        if not content:
            continue
        parts = getattr(content, "parts", []) or []
        texts = []
        for p in parts:
            txt = getattr(p, "text", None) or (p.get("text") if isinstance(p, dict) else None)
            if txt:
                texts.append(txt)
        if texts:
            return "\n".join(texts)

    return ""

def _gen_text(prompt: str) -> str:
    """
    Generate plain text from Gemini.
    - Returns a human-readable fallback if the model returns an empty output.
    - Avoids JSON parsing entirely to keep things simple for a chat frontend.
    """
    try:
        r = _model().generate_content(prompt)
    except Exception as e:
        return f"Generation error: {e}"

    text = _extract_text_from_response(r).strip()
    if not text:
        # Provide a deterministic fallback message to avoid silent failures.
        fr = None
        try:
            fr = getattr(r.candidates[0], "finish_reason", None)
        except Exception:
            pass
        return "Sorry, I could not generate a response right now." + (f" (finish_reason={fr})" if fr is not None else "")
    return text

# ─────────────────────────────────────────────────────────────────────────────
# FastAPI app and routes
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(title="Health Helper (Gemini, text-only)")

# Enable permissive CORS for development; restrict in production if needed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
def home():
    """Minimal landing page with links to Swagger docs and example endpoints."""
    return HTMLResponse(
        """
        <h2>Health Helper</h2>
        <p>Use <a href="/docs">/docs</a> for Swagger UI.</p>
        <ul>
          <li>GET  <code>/health</code></li>
          <li>POST <code>/stress_text</code></li>
          <li>POST <code>/plan_text</code></li>
        </ul>
        """,
        status_code=200,
    )

@app.get("/health")
def health():
    """Lightweight health-check endpoint."""
    return {"status": "ok"}

@app.post("/stress_text")
def stress_text(payload: AskIn):
    """
    Generate stress-reduction advice as plain text.
    - Input: JSON { "text": string, "context"?: { age?, location?, preferences?, constraints? } }
    - Output: text/plain (Markdown-friendly)
    """
    ctx = None
    if payload.context:
        c = payload.context
        ctx = UserContext(age=c.age, location=c.location, preferences=c.preferences, constraints=c.constraints)
    prompt = _stress_prompt_text(payload.text, ctx)
    text = _gen_text(prompt)
    return Response(content=text, media_type="text/plain; charset=utf-8")

@app.post("/plan_text")
def plan_text(payload: AskIn):
    """
    Generate a wellbeing plan as plain text.
    - Input: JSON { "text": string, "context"?: { age?, location?, preferences?, constraints? } }
    - Output: text/plain (Markdown-friendly)
    """
    ctx = None
    if payload.context:
        c = payload.context
        ctx = UserContext(age=c.age, location=c.location, preferences=c.preferences, constraints=c.constraints)
    prompt = _plan_prompt_text(payload.text, ctx)
    text = _gen_text(prompt)
    return Response(content=text, media_type="text/plain; charset=utf-8")
