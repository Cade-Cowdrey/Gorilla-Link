from __future__ import annotations
import os, time, json, math, re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from flask import Blueprint, request, jsonify
from cachetools import TTLCache
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# OpenAI v2 client (package name `openai`, import style below)
try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # type: ignore

# Optional Redis cache (if REDIS_URL is set)
try:
    import redis  # type: ignore
except Exception:
    redis = None  # type: ignore

# Optional text stats for reading time and grade level (already in requirements)
try:
    import textstat  # type: ignore
except Exception:
    textstat = None  # type: ignore

# Optional tokenization
try:
    import tiktoken  # type: ignore
except Exception:
    tiktoken = None  # type: ignore


ai_bp = Blueprint("ai_bp", __name__, url_prefix="/api/ai")

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # fast+cheap by default
MAX_TOKENS_OUT = int(os.getenv("AI_MAX_TOKENS_OUT", "256"))
TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.3"))

# Cache TTLs (seconds)
TTL_SUMMARY = int(os.getenv("AI_TTL_SUMMARY", "600"))      # 10 min
TTL_TOPICS  = int(os.getenv("AI_TTL_TOPICS", "900"))       # 15 min
TTL_MATCH   = int(os.getenv("AI_TTL_MATCH", "1800"))       # 30 min
TTL_REWRITE = int(os.getenv("AI_TTL_REWRITE", "900"))      # 15 min

# Rate-limiting (tokens per minute per identity)
RATE_LIMIT_TPM = int(os.getenv("AI_RATE_TPM", "30"))
RATE_WINDOW    = 60

# Redis (optional)
REDIS_URL = os.getenv("REDIS_URL")

# In-memory caches (used if Redis not configured)
memo_summary = TTLCache(maxsize=1024, ttl=TTL_SUMMARY)
memo_topics  = TTLCache(maxsize=512, ttl=TTL_TOPICS)
memo_match   = TTLCache(maxsize=512, ttl=TTL_MATCH)
memo_rewrite = TTLCache(maxsize=512, ttl=TTL_REWRITE)

# Simple in-memory rate limiter (fallback)
_rate_bucket: Dict[str, List[float]] = {}  # identity -> timestamps list


# ------------------------------------------------------------
# Utilities
# ------------------------------------------------------------
def has_openai() -> bool:
    return bool(OPENAI_API_KEY) and OpenAI is not None

def get_client():
    if not has_openai():
        return None
    return OpenAI(api_key=OPENAI_API_KEY)

def identity_from_request() -> str:
    # Prefer authenticated user id if available (Flask-Login current_user)
    try:
        from flask_login import current_user  # type: ignore
        if getattr(current_user, "is_authenticated", False):
            uid = getattr(current_user, "id", None) or getattr(current_user, "username", None)
            if uid:
                return f"user:{uid}"
    except Exception:
        pass
    # fallback to IP
    return f"ip:{request.headers.get('X-Forwarded-For', request.remote_addr)}"

def sanitize_text(s: str) -> str:
    # basic guard: strip control chars, collapse whitespace
    s = re.sub(r"[\x00-\x1f\x7f]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def reading_time_seconds(text: str) -> int:
    # 200 wpm baseline (~3.33 wps)
    words = max(1, len(text.split()))
    return math.ceil(words / 3.33)

def token_truncate(text: str, model: str, max_tokens: int) -> str:
    if not tiktoken:
        return text[:min(len(text), 8000)]  # crude safety
    try:
        enc = tiktoken.encoding_for_model(model) if model else tiktoken.get_encoding("cl100k_base")
        tokens = enc.encode(text)
        if len(tokens) <= max_tokens:
            return text
        tokens = tokens[:max_tokens]
        return enc.decode(tokens)
    except Exception:
        return text[:16000]

def use_redis() -> Optional[Any]:
    if not REDIS_URL or not redis:
        return None
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        r.ping()
        return r
    except Exception:
        return None

R = use_redis()

def cache_get(cache_key: str, scope: str) -> Optional[Any]:
    try:
        if R:
            val = R.get(f"ai:{scope}:{cache_key}")
            return json.loads(val) if val else None
        else:
            memo = {
                "summary": memo_summary,
                "topics": memo_topics,
                "match": memo_match,
                "rewrite": memo_rewrite
            }.get(scope)
            if memo is not None:
                return memo.get(cache_key)
    except Exception:
        return None
    return None

def cache_set(cache_key: str, scope: str, value: Any):
    try:
        if R:
            ttl = {
                "summary": TTL_SUMMARY,
                "topics": TTL_TOPICS,
                "match": TTL_MATCH,
                "rewrite": TTL_REWRITE
            }[scope]
            R.setex(f"ai:{scope}:{cache_key}", ttl, json.dumps(value))
        else:
            memo = {
                "summary": memo_summary,
                "topics": memo_topics,
                "match": memo_match,
                "rewrite": memo_rewrite
            }[scope]
            memo[cache_key] = value
    except Exception:
        pass

def rate_limited(identity: str) -> bool:
    now = time.time()
    if R:
        # Redis: simple leaky bucket
        key = f"ai:rl:{identity}"
        with R.pipeline() as p:
            p.zremrangebyscore(key, 0, now - RATE_WINDOW)
            p.zadd(key, {str(now): now})
            p.zcard(key)
            p.expire(key, RATE_WINDOW)
            _, _, count, _ = p.execute()
        return int(count) > RATE_LIMIT_TPM
    # in-memory fallback
    bucket = _rate_bucket.setdefault(identity, [])
    # drop old
    while bucket and bucket[0] < now - RATE_WINDOW:
        bucket.pop(0)
    bucket.append(now)
    return len(bucket) > RATE_LIMIT_TPM

class AITransientError(Exception): ...
class AIPermanentError(Exception): ...

@retry(
    retry=retry_if_exception_type(AITransientError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    reraise=True
)
def call_openai(messages: List[Dict[str, str]], model: str, temperature: float, max_tokens: int) -> str:
    client = get_client()
    if not client:
        raise AIPermanentError("OpenAI not configured.")
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        # Heuristic: retry on 429/5xx-ish messages
        emsg = str(e).lower()
        if any(tok in emsg for tok in ["rate limit", "timeout", "temporarily", "overloaded", "unavailable", "429", "502", "503", "504"]):
            raise AITransientError(emsg)
        raise AIPermanentError(emsg)

def ok(data: Any, **meta):
    payload = {"ok": True, "data": data, "meta": meta}
    return jsonify(payload), 200

def fail(message: str, code: int = 400, **meta):
    payload = {"ok": False, "error": {"message": message, "code": code}, "meta": meta}
    return jsonify(payload), code


# ------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------
@ai_bp.route("/health")
def health():
    return ok({"openai": bool(has_openai()), "model": MODEL})

@ai_bp.route("/summary", methods=["POST", "GET"])
def summary():
    ident = identity_from_request()
    if rate_limited(ident):
        return fail("Rate limit exceeded. Try again shortly.", 429)

    # Accept both GET (demo) and POST (real)
    if request.method == "POST":
        text = sanitize_text(request.json.get("text", ""))
    else:
        text = sanitize_text(request.args.get("text", ""))

    if not text:
        return fail("Missing 'text' to summarize.", 422)

    # Cache key
    ck = f"v1:{hash(text)}:{MODEL}:{MAX_TOKENS_OUT}"
    cached = cache_get(ck, "summary")
    if cached:
        return ok(cached, cached=True)

    # Compute stats
    rtime = reading_time_seconds(text)
    reading_level = (textstat.text_standard(text, float_output=False) if textstat else None)

    # Token-safe truncation
    truncated = token_truncate(text, MODEL, 6000)

    # System prompt (guardrail)
    sys_prompt = (
        "You are a concise, neutral summarizer for a university platform. "
        "Return: 1) bullet summary (max 6 bullets), 2) sentiment (pos/neg/neutral), "
        "3) top 5 keywords (lowercase), 4) 1-sentence takeaway."
    )

    if has_openai():
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": f"Text:\n{truncated}"}
        ]
        try:
            content = call_openai(messages, MODEL, TEMPERATURE, MAX_TOKENS_OUT)
        except AIPermanentError as e:
            return fail(f"AI error: {e}", 500)
        except AITransientError as e:
            return fail(f"AI temporarily unavailable: {e}", 503)

        result = {
            "model": MODEL,
            "summary": content,
            "reading_time_seconds": rtime,
            "reading_level": reading_level
        }
    else:
        # Safe fallback: naive summary
        sentences = re.split(r"(?<=[.!?])\s+", truncated)[:5]
        result = {
            "model": "fallback",
            "summary": " • " + "\n • ".join(sentences) if sentences else truncated[:280],
            "reading_time_seconds": rtime,
            "reading_level": reading_level
        }

    cache_set(ck, "summary", result)
    return ok(result, cached=False)


@ai_bp.route("/topics", methods=["GET"])
def topics():
    ident = identity_from_request()
    if rate_limited(ident):
        return fail("Rate limit exceeded. Try again shortly.", 429)

    seed = sanitize_text(request.args.get("seed", "campus life, careers, scholarships"))
    ck = f"v1:{seed}:{MODEL}:{MAX_TOKENS_OUT}"
    cached = cache_get(ck, "topics")
    if cached:
        return ok(cached, cached=True)

    sys_prompt = (
        "You suggest trending discussion topics for a university platform. "
        "Output 6-10 concise topic titles only, no numbering, one per line."
    )

    if has_openai():
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": f"Seed areas: {seed}"}
        ]
        try:
            content = call_openai(messages, MODEL, 0.4, 200)
            topics_list = [t.strip("-• ").strip() for t in content.splitlines() if t.strip()]
        except AIPermanentError as e:
            return fail(f"AI error: {e}", 500)
        except AITransientError as e:
            return fail(f"AI temporarily unavailable: {e}", 503)
    else:
        topics_list = [
            "Best Study Spots Around Campus",
            "Scholarship Application Tips That Work",
            "Internship Interview Strategies",
            "Balancing Classes, Work, and Life",
            "Affordable Housing Near PSU",
            "Alumni AMA: First Year On The Job",
            "Clubs & Groups: Which One’s Right For You?",
            "Research & Lab Opportunities This Semester",
            "Networking Events You Shouldn’t Miss",
            "Mental Wellness Resources at PSU"
        ]

    result = {"topics": topics_list[:10]}
    cache_set(ck, "topics", result)
    return ok(result, cached=False)


@dataclass
class Mentor:
    name: str
    field: str
    skills: List[str]
    availability: int  # slots open

MENTORS = [
    Mentor("Dr. Harrison Wells", "Engineering", ["cad", "matlab", "control systems", "embedded"], 2),
    Mentor("Rachel Kim", "Business Analytics", ["sql", "python", "tableau", "forecasting"], 3),
    Mentor("Jordan P.", "Marketing", ["copywriting", "social", "brand", "seo"], 0),
    Mentor("Elena Garcia", "Computer Science", ["python", "ml", "java", "systems"], 1),
    Mentor("Darnell Lee", "Education", ["curriculum", "edtech", "assessment"], 2),
]

@ai_bp.route("/match", methods=["POST", "GET"])
def match():
    ident = identity_from_request()
    if rate_limited(ident):
        return fail("Rate limit exceeded. Try again shortly.", 429)

    # Accept profile via POST JSON or GET query
    if request.method == "POST":
        profile = request.json or {}
    else:
        profile = {"interests": request.args.get("interests", "python, internships, data").split(",")}

    # Normalize interests
    interests = [sanitize_text(i).lower() for i in profile.get("interests", []) if i]

    ck = f"v1:{','.join(sorted(interests))}"
    cached = cache_get(ck, "match")
    if cached:
        return ok(cached, cached=True)

    # Simple scoring + AI explanation (optional)
    def score(m: Mentor) -> int:
        base = sum(1 for i in interests for s in m.skills if i.strip() in s)
        avail = 1 if m.availability > 0 else 0
        field_bonus = 1 if any(i in m.field.lower() for i in interests) else 0
        return base * 2 + field_bonus + avail

    ranked = sorted(MENTORS, key=score, reverse=True)
    top = [m for m in ranked if m.availability > 0][:3] or ranked[:1]

    explanation = None
    if has_openai():
        try:
            expl = call_openai([
                {"role": "system", "content": "Explain mentor matches briefly and positively in 2-3 sentences."},
                {"role": "user", "content": f"Interests: {interests}\nMentors: {[m.name for m in top]} with skills {[m.skills for m in top]}."}
            ], MODEL, 0.4, 160)
            explanation = expl
        except Exception:
            explanation = None

    result = {
        "interests": interests,
        "matches": [{"name": m.name, "field": m.field, "skills": m.skills, "availability": m.availability} for m in top],
        "explanation": explanation or "These mentors align closely with your skills and interests while having current availability."
    }
    cache_set(ck, "match", result)
    return ok(result, cached=False)


@ai_bp.route("/rewrite", methods=["POST"])
def rewrite():
    """Optional enhancement: rewrite text for clarity & tone (“polish my post”)."""
    ident = identity_from_request()
    if rate_limited(ident):
        return fail("Rate limit exceeded. Try again shortly.", 429)

    data = request.json or {}
    text = sanitize_text(data.get("text", ""))
    tone = sanitize_text(data.get("tone", "friendly and professional"))
    if not text:
        return fail("Missing 'text' to rewrite.", 422)

    ck = f"v1:rewrite:{hash(text)}:{tone}"
    cached = cache_get(ck, "rewrite")
    if cached:
        return ok(cached, cached=True)

    # Token-safe truncate
    truncated = token_truncate(text, MODEL, 6000)

    if has_openai():
        try:
            out = call_openai([
                {"role": "system", "content": "Rewrite the user's text for clarity, brevity, and correctness, preserving intent and meaning."},
                {"role": "user", "content": f"Desired tone: {tone}\nText:\n{truncated}"}
            ], MODEL, 0.2, MAX_TOKENS_OUT)
            result = {"original": text, "rewritten": out, "tone": tone}
        except AIPermanentError as e:
            return fail(f"AI error: {e}", 500)
        except AITransientError as e:
            return fail(f"AI temporarily unavailable: {e}", 503)
    else:
        # Fallback: light-touch cleanup
        cleaned = re.sub(r"\s+", " ", text).strip()
        result = {"original": text, "rewritten": cleaned, "tone": tone, "model": "fallback"}

    cache_set(ck, "rewrite", result)
    return ok(result, cached=False)
