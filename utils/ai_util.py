# utils/ai_util.py
# ---------------------------------------------------------------------
# Production-ready AI utility for PittState-Connect
# - Provider-agnostic (OpenAI / Azure OpenAI via env vars)
# - Robust retries with exponential backoff
# - Circuit breaker to avoid cascading failures
# - Prompt templating + safety moderation
# - Strict timeouts and graceful fallbacks
# - Lightweight in-process cache (works alongside Redis)
# - Structured logging hooks for analytics
# ---------------------------------------------------------------------

from __future__ import annotations

import os
import time
import json
import logging
import hashlib
import re
from functools import lru_cache
from typing import Optional, Dict, Any, Tuple

# ---- Logging ----------------------------------------------------------
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | ai_util | %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# ---- Provider selection (env-configurable) ----------------------------
# Supported:
#   PROVIDER=openai            -> uses OpenAI API
#   PROVIDER=azure             -> uses Azure OpenAI (Responses API compatible)
PROVIDER = os.getenv("AI_PROVIDER", "openai").strip().lower()

# Model + parameters
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.3"))
AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "600"))

# OpenAI config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "").strip() or None  # optional custom base

# Azure OpenAI config
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", AI_MODEL)  # often the deployment name
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")  # current as of 2025

# Timeouts / retries / circuit breaker
REQUEST_TIMEOUT_SECS = int(os.getenv("AI_TIMEOUT_SECS", "30"))
RETRY_ATTEMPTS = int(os.getenv("AI_RETRY_ATTEMPTS", "3"))
RETRY_BASE_DELAY = float(os.getenv("AI_RETRY_BASE_DELAY", "0.6"))
CIRCUIT_FAIL_WINDOW_SECS = int(os.getenv("AI_CB_WINDOW_SECS", "120"))
CIRCUIT_FAIL_THRESHOLD = int(os.getenv("AI_CB_FAIL_THRESHOLD", "4"))
CIRCUIT_COOLDOWN_SECS = int(os.getenv("AI_CB_COOLDOWN_SECS", "45"))

# Moderation toggle (best-effort heuristic if API disabled)
ENABLE_BASIC_MODERATION = os.getenv("AI_ENABLE_BASIC_MODERATION", "true").lower() == "true"

# Lightweight in-process cache (separate from Redis)
ENABLE_LOCAL_CACHE = os.getenv("AI_ENABLE_LOCAL_CACHE", "true").lower() == "true"
LOCAL_CACHE_TTL_SECS = int(os.getenv("AI_LOCAL_CACHE_TTL_SECS", "900"))  # 15 minutes


# ----------------- Circuit Breaker (module-level state) ----------------
_CB_STATE = {
    "fails": 0,
    "first_fail_ts": 0.0,
    "open_until": 0.0,
}


def _cb_is_open() -> bool:
    now = time.time()
    return now < _CB_STATE.get("open_until", 0.0)


def _cb_record_success():
    _CB_STATE["fails"] = 0
    _CB_STATE["first_fail_ts"] = 0.0
    _CB_STATE["open_until"] = 0.0


def _cb_record_failure():
    now = time.time()
    if _CB_STATE["fails"] == 0:
        _CB_STATE["first_fail_ts"] = now
    _CB_STATE["fails"] += 1

    # reset the window if it has expired
    if now - _CB_STATE["first_fail_ts"] > CIRCUIT_FAIL_WINDOW_SECS:
        _CB_STATE["fails"] = 1
        _CB_STATE["first_fail_ts"] = now

    if _CB_STATE["fails"] >= CIRCUIT_FAIL_THRESHOLD:
        _CB_STATE["open_until"] = now + CIRCUIT_COOLDOWN_SECS
        logger.warning(
            f"⚠️ Circuit opened for {CIRCUIT_COOLDOWN_SECS}s due to repeated AI failures."
        )


# ------------------------- Provider Clients ----------------------------
@lru_cache(maxsize=1)
def _openai_client():
    """
    Lazily constructs a provider client.
    Supports:
      - OpenAI (python SDK)
      - Azure OpenAI (python SDK)
    """
    try:
        if PROVIDER == "azure":
            # Azure OpenAI via OpenAI SDK “client” with api_key/base_url
            # Requires: openai>=1.0.0
            from openai import OpenAI
            base_url = f"{AZURE_OPENAI_ENDPOINT}/openai"
            client = OpenAI(
                api_key=AZURE_OPENAI_API_KEY,
                base_url=base_url,
                default_headers={"api-key": AZURE_OPENAI_API_KEY},
            )
            logger.info("✅ Initialized Azure OpenAI client.")
            return client

        # Default: OpenAI
        from openai import OpenAI
        kwargs = {}
        if OPENAI_BASE_URL:
            kwargs["base_url"] = OPENAI_BASE_URL
        client = OpenAI(api_key=OPENAI_API_KEY, **kwargs)
        logger.info("✅ Initialized OpenAI client.")
        return client
    except Exception as e:
        logger.exception(f"❌ Failed to initialize AI client: {e}")
        raise


# --------------------------- Prompt Tools ------------------------------
SYSTEM_PROMPT = """You are the PittState-Connect Career Copilot.
Your job: analyze a student's search intent and return crisp, helpful job-market insights for Pittsburg State University students.
Be concise, actionable, and optimistic. Include:
- Skills & keywords to use in applications
- Entry-level role titles that match
- 2–3 industry trends or resources students should read
- ONE short, PSU-tailored next step
Never fabricate facts. If unclear, note assumptions briefly.
Return plain text; avoid markdown tables.
"""

def _build_user_prompt(query: str) -> str:
    query = query.strip()
    return (
        f"Student query: {query}\n"
        "Context: Early-career student at Pittsburg State University seeking guidance.\n"
        "Deliver: 120-220 words, skimmable bullets where it helps, no fluff."
    )


# --------------------------- Moderation --------------------------------
# Basic regex-based guardrails (complementary to upstream moderation)
_BLOCK_PATTERNS = [
    r"\b(?:credit card|ssn|social security number)\b",
    r"\b(?:sell|buy)\s+(?:weapons|drugs)\b",
]

def _basic_moderation(text: str) -> Tuple[bool, Optional[str]]:
    t = text.lower()
    for pat in _BLOCK_PATTERNS:
        if re.search(pat, t):
            return False, "The request appears to contain prohibited or sensitive content."
    # overly-long queries are often accidental pastes
    if len(text) > 4000:
        return False, "Your request is too long. Try a shorter search phrase."
    return True, None


# --------------------------- Local Cache --------------------------------
class _LocalCache:
    def __init__(self, ttl: int):
        self.ttl = ttl
        self.store: Dict[str, Tuple[float, str]] = {}

    def make_key(self, prompt: str, model: str) -> str:
        raw = json.dumps({"p": prompt, "m": model}, sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[str]:
        if not ENABLE_LOCAL_CACHE:
            return None
        hit = self.store.get(key)
        if not hit:
            return None
        ts, val = hit
        if (time.time() - ts) > self.ttl:
            self.store.pop(key, None)
            return None
        return val

    def set(self, key: str, value: str):
        if not ENABLE_LOCAL_CACHE:
            return
        self.store[key] = (time.time(), value)


_local_cache = _LocalCache(ttl=LOCAL_CACHE_TTL_SECS)


# --------------------------- Core Call ----------------------------------
def _call_model(messages: list[Dict[str, str]], *, model: str) -> str:
    """
    Raw model call with retries, timeout, and circuit breaker.
    Returns text string (may be empty if provider returns none).
    """
    if _cb_is_open():
        raise RuntimeError("AI circuit breaker is open; skipping upstream call.")

    last_err: Optional[Exception] = None
    client = _openai_client()

    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            start = time.time()

            if PROVIDER == "azure":
                # Azure OpenAI using Responses/Chat Completions compatible API
                # Prefer Responses API if available; fall back to Chat Completions.
                # Here we use chat.completions for broad compatibility.
                resp = client.chat.completions.create(
                    model=AZURE_OPENAI_DEPLOYMENT,
                    messages=messages,
                    temperature=AI_TEMPERATURE,
                    max_tokens=AI_MAX_TOKENS,
                    timeout=REQUEST_TIMEOUT_SECS,  # supported by SDK's httpx client
                )
                text = (resp.choices[0].message.content or "").strip()
            else:
                # OpenAI Responses/Chat Completions (use chat for broad SDK support)
                resp = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=AI_TEMPERATURE,
                    max_tokens=AI_MAX_TOKENS,
                    timeout=REQUEST_TIMEOUT_SECS,
                )
                text = (resp.choices[0].message.content or "").strip()

            elapsed = (time.time() - start) * 1000
            logger.info(f"🤖 AI call ok (attempt {attempt}) in {elapsed:.0f}ms")
            _cb_record_success()
            return text

        except Exception as e:
            last_err = e
            _cb_record_failure()
            if attempt >= RETRY_ATTEMPTS:
                break
            sleep_for = RETRY_BASE_DELAY * (2 ** (attempt - 1))
            jitter = min(0.25, sleep_for * 0.2)
            time.sleep(sleep_for + jitter)
            logger.warning(f"Retrying AI call (attempt {attempt+1}/{RETRY_ATTEMPTS}) after error: {e}")

    # all retries failed
    raise RuntimeError(f"AI upstream failed after {RETRY_ATTEMPTS} attempts: {last_err}")


# ----------------------- Public API Surface -----------------------------
def generate_ai_job_insight(query: str) -> str:
    """
    High-level function used by the API blueprint to produce a student-facing
    career insight. Includes:
      - Input normalization
      - Basic moderation gate
      - Prompt building
      - Local caching
      - Upstream model call with retries + circuit breaker
      - Post-processing and safe fallback
    Returns: plain text insight (<= ~220 words goal).
    """
    q = (query or "").strip()
    if not q:
        return "Please provide a short phrase like 'data analyst internships in Kansas City'."

    if ENABLE_BASIC_MODERATION:
        ok, reason = _basic_moderation(q)
        if not ok:
            return f"Sorry — I can’t help with that request. {reason}"

    system = {"role": "system", "content": SYSTEM_PROMPT}
    user = {"role": "user", "content": _build_user_prompt(q)}
    messages = [system, user]

    # local cache key is model + prompt; Redis layer happens in the API route
    cache_key = _local_cache.make_key(prompt=json.dumps(messages, sort_keys=True), model=AI_MODEL)
    cached = _local_cache.get(cache_key)
    if cached:
        logger.info("✅ Local AI cache hit.")
        return cached

    try:
        text = _call_model(messages, model=AI_MODEL)

        # Post-process: trim, remove extreme whitespace, guard empty
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        if not text:
            text = _fallback_response(q)

        # Clamp length softly (avoid walls of text)
        if len(text) > 1800:
            text = text[:1770].rsplit(" ", 1)[0] + "..."

        _local_cache.set(cache_key, text)
        return text

    except Exception as e:
        logger.exception(f"AI insight generation failed: {e}")
        return _fallback_response(q)


def _fallback_response(query: str) -> str:
    """
    Safe, deterministic fallback when AI is unavailable.
    """
    # derive a couple of safe keywords from the query
    words = re.findall(r"[a-zA-Z]{3,}", query.lower())[:6]
    kws = ", ".join(sorted(set(words))) or "entry-level, internship, junior"
    return (
        "Here’s a quick starting point while our AI is busy:\n"
        f"- Suggested keywords: {kws}\n"
        "- Role ideas: Analyst, Coordinator, Associate, Intern\n"
        "- Next step (PSU): Visit the Career Resource Center to refine your resume and search Handshake for 5 matching roles.\n"
        "Tip: Add 3 skills you’re actively building to your resume and tailor your summary to one target role."
    )


# ----------------------- (Optional) Test Hook ---------------------------
def _self_test() -> Dict[str, Any]:
    """
    Lightweight smoke test for health checks or admin dashboards.
    Does not call the upstream model.
    """
    return {
        "provider": PROVIDER,
        "model": AI_MODEL,
        "local_cache_enabled": ENABLE_LOCAL_CACHE,
        "moderation_enabled": ENABLE_BASIC_MODERATION,
        "circuit_open": _cb_is_open(),
        "cb_fails": _CB_STATE["fails"],
        "cb_open_until": _CB_STATE["open_until"],
    }


# ----------------------- Minimal Public Facade --------------------------
__all__ = [
    "generate_ai_job_insight",
    "_self_test",
]
