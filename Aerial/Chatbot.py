
#!/usr/bin/env python3
"""
GUI.py — Flask API + Web UI wrapper for your existing modules
=============================================================

- Converts the FastAPI endpoints in health_helper.py to Flask-style endpoints
- Exposes unified routes under /api/*
- Serves your GUI.html as the homepage

How to run
----------
1) Install deps (in your venv):
   pip install flask flask-cors python-dotenv google-generativeai serpapi

2) Create a .env next to this file with (at least):
   GEMINI_API_KEY=your_gemini_key
   GEMINI_MODEL=gemini-2.5-pro
   SERPAPI_API_KEY=your_serpapi_key

3) Start:
   python GUI.py   (or)   python -m flask --app GUI.py run --host 0.0.0.0 --port 8000

4) Open: http://localhost:8000

Endpoints
---------
GET  /api/health
POST /api/stress_text    { "text": "...", "context": {...} }  -> text/plain (Markdown)
POST /api/plan_text      { "text": "...", "context": {...} }  -> text/plain (Markdown)
POST /api/recommend      { "text": "...", "top_k": 5 }        -> application/json
"""

from __future__ import annotations
import os, json, re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from flask import Flask, request, jsonify, send_from_directory, Response, render_template
from flask_cors import CORS
from dotenv import load_dotenv

# ─────────────────────────────────────────────────────────────────────────────
# Load env & configure APIs
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
SERPAPI_API_KEY= os.getenv("SERPAPI_API_KEY")

# Gemini client (lazy import to keep startup fast)
import google.generativeai as genai
if not GEMINI_API_KEY:
    raise SystemExit("Missing GEMINI_API_KEY. Put it in .env next to GUI.py")
genai.configure(api_key=GEMINI_API_KEY)

# Generation config similar to health_helper.py
FALLBACK_MODELS = [
    os.getenv('GEMINI_MODEL', 'gemini-2.5-pro'),
    'gemini-2.5-flash',
    'gemini-1.5-flash',
    'gemini-1.5-flash-8b'
]

GEN_CONFIG_TEXT = {
    "temperature": 0.4,
    "top_p": 0.9,
    "max_output_tokens": 3072
}
def _model(name:str):
    return genai.GenerativeModel(model_name=name, generation_config=GEN_CONFIG_TEXT)

# ─────────────────────────────────────────────────────────────────────────────
# Import your recommender and database modules; patch compatibility if needed
# ─────────────────────────────────────────────────────────────────────────────
# Ensure therapists_recommender can auto-build a city DB using database_fetcher
try:
    import database_fetcher as dbf
except Exception as e:
    raise SystemExit(f"Could not import database_fetcher.py: {e}")

# Provide a compatibility shim for therapists_recommender.ensure_city_database()
# which calls `from database_fetcher import build_city`.
if not hasattr(dbf, "build_city"):
    def build_city(city: str,
                   terms: Optional[List[str]] = None,
                   outdir: str = None,
                   hl: str = "vi",
                   pages: int = 2,
                   sleep_s: float = 1.2):
        """
        Compatibility wrapper to build a single city's JSON using database_fetcher.build_city_database
        """
        if SERPAPI_API_KEY is None:
            raise SystemExit("Missing SERPAPI_API_KEY. Put it in .env for database building.")
        if terms is None:
            terms = ["psychologist", "psychiatrist", "mental health clinic"]
        if outdir is None:
            # Align with therapists_recommender.DB_DIR (./database next to scripts)
            outdir = os.path.join(os.path.dirname(__file__), "database")
        os.makedirs(outdir, exist_ok=True)
        out_path = os.path.join(outdir, f"{safe_name(city)}_therapists.json")
        dbf.build_city_database(
            city=city,
            terms=terms,
            out_path=out_path,
            api_key=SERPAPI_API_KEY,
            hl=hl,
            pages=pages,
            sleep_s=sleep_s,
        )
        return out_path

    # Utility for safe file naming (mirrors logic in database_fetcher)
    def safe_name(s: str) -> str:
        keep = []
        for ch in s:
            if ch.isalnum() or ch in ("_", "-"):
                keep.append(ch)
            elif ch.isspace():
                keep.append("_")
            else:
                continue
        return "".join(keep) or "output"

    dbf.build_city = build_city  # monkey-patch

# Now import the recommender
try:
    from therapists_recommender import recommend

    def _format_recommend_markdown(result: dict) -> str:
        """Render recommender JSON into friendly Vietnamese Markdown."""
        try:
            needs = result.get("needs") or {}
            providers = result.get("results") or result.get("providers") or []
            city = needs.get("nearest_major_city") or needs.get("city") or "khu vực của bạn"
        except Exception:
            needs, providers, city = {}, [], "khu vực của bạn"

        lines = []
        lines.append(f"**Gợi ý chuyên gia gần {city}:**")
        if not providers:
            lines.append(
            "\n_Chưa tìm được cơ sở phù hợp. Hãy thử mô tả rõ hơn về vấn đề, ngân sách, hình thức online/offline._"
            )
            return "\n".join(lines)

        for i, p in enumerate(providers[:10], start=1):
            name = p.get("name") or p.get("title") or "Cơ sở"
            rating = p.get("rating")
            addr = p.get("address") or p.get("formatted_address") or ""
            phone = p.get("phone") or p.get("international_phone_number") or ""
            website = p.get("website") or ""
            bits = [addr, phone, website]
            meta = " • ".join([b for b in bits if b])
            star = f" — ⭐ {rating}" if isinstance(rating, (int, float, str)) and str(rating).strip() else ""
            lines.append(f"- **{i}. {name}**{star}")
            if meta:
                lines.append(f"  {meta}")
        return "\n".join(lines)

except Exception as e:
    raise SystemExit(f"Could not import therapists_recommender.py: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# Minimal data classes to mirror health_helper inputs
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class UserContext:
    age: Optional[int] = None
    location: Optional[str] = None
    preferences: Optional[List[str]] = None
    constraints: Optional[List[str]] = None

# ─────────────────────────────────────────────────────────────────────────────
# Prompt builders (text-only Markdown, adapted from health_helper.py)
# ─────────────────────────────────────────────────────────────────────────────
def _stress_prompt_text(user_text: str, ctx: Optional[UserContext]) -> str:
    prefs = ", ".join(ctx.preferences) if (ctx and ctx.preferences) else "none"
    cons  = ", ".join(ctx.constraints) if (ctx and ctx.constraints) else "none"
    age = str(ctx.age) if (ctx and ctx.age is not None) else "unspecified"
    loc = ctx.location if (ctx and ctx.location) else "unspecified"
    return f"""
You are a careful, evidence-aligned mental health assistant (non-clinical).
Write a clear, concise Markdown answer with headings and bullet points. Always respond in Vietnamese (tiếng Việt chuẩn).
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
    prefs = ", ".join(ctx.preferences) if (ctx and ctx.preferences) else "none"
    cons  = ", ".join(ctx.constraints) if (ctx and ctx.constraints) else "none"
    age = str(ctx.age) if (ctx and ctx.age is not None) else "unspecified"
    loc = ctx.location if (ctx and ctx.location) else "unspecified"
    return f"""
You are a behavior-change coach (non-clinical).
Return a readable Markdown plan (no code fences, no JSON). Always respond in Vietnamese (tiếng Việt chuẩn).

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

def _extract_text_from_response(resp) -> str:
    """Gracefully extract text from a Gemini Response."""
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


def _parse_retry_after_seconds(err_msg: str) -> int:
    """Extract 'retry in Xs' or 'seconds: N' from error message."""
    if not err_msg:
        return 0
    import re
    m = re.search(r"retry in ([\d\.]+)s", err_msg, flags=re.I)
    if m:
        try:
            val = float(m.group(1)); 
            return int(max(1, round(val)))
        except Exception:
            pass
    m2 = re.search(r"seconds[:\s]+(\d+)", err_msg, flags=re.I)
    if m2:
        try:
            return int(m2.group(1))
        except Exception:
            pass
    return 0

def _gen_text(prompt: str) -> str:
    """Generate plain text via Gemini with retries/backoff and model fallback."""
    last_err = None
    import time
    for mname in FALLBACK_MODELS:
        for attempt in range(2):  # 2 attempts per model
            try:
                r = _model(mname).generate_content(prompt)
                text = _extract_text_from_response(r).strip()
                if text:
                    return text
                last_err = f"Empty response from model {mname}."
                break
            except Exception as e:
                msg = str(e)
                last_err = f"{type(e).__name__}: {msg} (model={mname}, attempt={attempt+1})"
                if "429" in msg or "quota" in msg.lower() or "rate" in msg.lower():
                    wait_s = _parse_retry_after_seconds(msg) or 6
                    time.sleep(min(wait_s, 12))
                    continue
                else:
                    break
        # try next model
    return "Xin lỗi, máy chủ đang bận. Vui lòng thử lại sau.\nChi tiết: " + (last_err or "unknown error")

# ─────────────────────────────────────────────────────────────────────────────
# Flask app
# ─────────────────────────────────────────────────────────────────────────────
app = Flask(__name__, template_folder='templates')
CORS(app)

# Optional tiny anti-burst throttle per IP
LAST_HIT = {}
THROTTLE_SECONDS = float(os.getenv('THROTTLE_SECONDS', '0.0'))

def _throttle():
    if THROTTLE_SECONDS <= 0:
        return
    try:
        import time
        addr = request.remote_addr or 'unknown'
        now = time.time()
        last = LAST_HIT.get(addr, 0)
        if now - last < THROTTLE_SECONDS:
            time.sleep(THROTTLE_SECONDS - (now - last))
        LAST_HIT[addr] = time.time()
    except Exception:
        pass

@app.route("/", methods=["GET"])
def index():
    return render_template("GUI_new.html")

# Health check
@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({"status": "ok"})

# Stress advice (text/markdown)
@app.route("/api/stress_text", methods=["POST"])
def api_stress_text():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    ctx_in = data.get("context") or {}
    ctx = UserContext(
        age=ctx_in.get("age"),
        location=ctx_in.get("location", "Viet Nam"),
        preferences=ctx_in.get("preferences") or ["prefers_online"],
        constraints=ctx_in.get("constraints") or ["low_budget","limited_time"],
    )
    prompt = _stress_prompt_text(text, ctx)
    out = _gen_text(prompt)
    return Response(out, mimetype="text/plain; charset=utf-8")

# Wellbeing plan (text/markdown)
@app.route("/api/plan_text", methods=["POST"])
def api_plan_text():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    ctx_in = data.get("context") or {}
    ctx = UserContext(
        age=ctx_in.get("age"),
        location=ctx_in.get("location", "Viet Nam"),
        preferences=ctx_in.get("preferences") or ["prefers_online"],
        constraints=ctx_in.get("constraints") or ["low_budget","limited_time"],
    )
    prompt = _plan_prompt_text(text, ctx)
    out = _gen_text(prompt)
    return Response(out, mimetype="text/plain; charset=utf-8")

# Recommender (JSON)

@app.route("/api/recommend_text", methods=["POST"])
def api_recommend_text():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    top_k = int(data.get("top_k") or 5)
    try:
        res = recommend(text, top_k=top_k)
        md = _format_recommend_markdown(res)
        return Response(md, mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"Lỗi: {e}", mimetype="text/plain; charset=utf-8", status=500)

@app.route("/api/recommend", methods=["POST"])
def api_recommend():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    top_k = int(data.get("top_k") or 5)
    try:
        out = recommend(text, top_k=top_k)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify(out)

# ─────────────────────────────────────────────────────────────────────────────
# Entrypoint
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=True)


# Modern UI route
@app.route("/new", methods=["GET"])
def new_ui():
    return render_template("GUI_new.html")
