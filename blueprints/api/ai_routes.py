from __future__ import annotations
import os, time, json, math, re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from flask import Blueprint, request, jsonify
from cachetools import TTLCache
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# OpenAI v2 client
try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # type: ignore

# Optional extras
try:
    import redis  # type: ignore
except Exception:
    redis = None  # type: ignore

try:
    import textstat  # type: ignore
except Exception:
    textstat = None  # type: ignore

try:
    import tiktoken  # type: ignore
except Exception:
    tiktoken = None  # type: ignore


ai_bp = Blueprint("ai_bp", __name__, url_prefix="/api/ai")

# ---------------------- Config ----------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_TOKENS_OUT = int(os.getenv("AI_MAX_TOKENS_OUT", "256"))
TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.3"))

TTL_SUMMARY = int(os.getenv("AI_TTL_SUMMARY", "600"))
TTL_TOPICS  = int(os.getenv("AI_TTL_TOPICS", "900"))
TTL_MATCH   = int(os.getenv("AI_TTL_MATCH", "1800"))
TTL_REWRITE = int(os.getenv("AI_TTL_REWRITE", "900"))

# New TTLs
TTL_INSIGHT = int(os.getenv("AI_TTL_INSIGHT", "600"))
TTL_LEARN   = int(os.getenv("AI_TTL_LEARN", "1800"))
TTL_THREAD  = int(os.getenv("AI_TTL_THREAD", "600"))
TTL_RESUME  = int(os.getenv("AI_TTL_RESUME", "1200"))
TTL_ESSAY   = int(os.getenv("AI_TTL_ESSAY", "1200"))
TTL_DONOR   = int(os.getenv("AI_TTL_DONOR", "3600"))
TTL_TREND   = int(os.getenv("AI_TTL_TREND", "900"))

RATE_LIMIT_TPM = int(os.getenv("AI_RATE_TPM", "30"))
RATE_WINDOW    = 60

REDIS_URL = os.getenv("REDIS_URL")

memo_summary = TTLCache(maxsize=1024, ttl=TTL_SUMMARY)
memo_topics  = TTLCache(maxsize=512, ttl=TTL_TOPICS)
memo_match   = TTLCache(maxsize=512, ttl=TTL_MATCH)
memo_rewrite = TTLCache(maxsize=512, ttl=TTL_REWRITE)
memo_insight = TTLCache(maxsize=256, ttl=TTL_INSIGHT)
memo_learn   = TTLCache(maxsize=256, ttl=TTL_LEARN)
memo_thread  = TTLCache(maxsize=512, ttl=TTL_THREAD)
memo_resume  = TTLCache(maxsize=256, ttl=TTL_RESUME)
memo_essay   = TTLCache(maxsize=256, ttl=TTL_ESSAY)
memo_donor   = TTLCache(maxsize=128, ttl=TTL_DONOR)
memo_trend   = TTLCache(maxsize=256, ttl=TTL_TREND)

_rate_bucket: Dict[str, List[float]] = {}

def has_openai() -> bool:
    return bool(OPENAI_API_KEY) and OpenAI is not None

def get_client():
    if not has_openai(): return None
    return OpenAI(api_key=OPENAI_API_KEY)

def use_redis() -> Optional[Any]:
    if not REDIS_URL or not redis: return None
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True); r.ping(); return r
    except Exception: return None

R = use_redis()

def identity_from_request() -> str:
    try:
        from flask_login import current_user  # type: ignore
        if getattr(current_user, "is_authenticated", False):
            uid = getattr(current_user, "id", None) or getattr(current_user, "username", None)
            if uid: return f"user:{uid}"
    except Exception: pass
    return f"ip:{request.headers.get('X-Forwarded-For', request.remote_addr)}"

def sanitize_text(s: str) -> str:
    s = re.sub(r"[\x00-\x1f\x7f]", " ", s); s = re.sub(r"\s+", " ", s).strip(); return s

def token_truncate(text: str, model: str, max_tokens: int) -> str:
    if not tiktoken: return text[:12000]
    try:
        enc = tiktoken.encoding_for_model(model) if model else tiktoken.get_encoding("cl100k_base")
        toks = enc.encode(text)
        if len(toks) <= max_tokens: return text
        toks = toks[:max_tokens]; return enc.decode(toks)
    except Exception: return text[:12000]

def reading_time_seconds(text: str) -> int:
    words = max(1, len(text.split())); return math.ceil(words / 3.33)

def cache_get(cache_key: str, scope: str) -> Optional[Any]:
    try:
        if R:
            raw = R.get(f"ai:{scope}:{cache_key}"); return json.loads(raw) if raw else None
        memo_map = {
            "summary": memo_summary, "topics": memo_topics, "match": memo_match, "rewrite": memo_rewrite,
            "insight": memo_insight, "learn": memo_learn, "thread": memo_thread, "resume": memo_resume,
            "essay": memo_essay, "donor": memo_donor, "trend": memo_trend
        }
        return memo_map[scope].get(cache_key)
    except Exception: return None

def cache_set(cache_key: str, scope: str, value: Any):
    try:
        ttl_map = {
            "summary": TTL_SUMMARY, "topics": TTL_TOPICS, "match": TTL_MATCH, "rewrite": TTL_REWRITE,
            "insight": TTL_INSIGHT, "learn": TTL_LEARN, "thread": TTL_THREAD, "resume": TTL_RESUME,
            "essay": TTL_ESSAY, "donor": TTL_DONOR, "trend": TTL_TREND
        }
        if R:
            R.setex(f"ai:{scope}:{cache_key}", ttl_map[scope], json.dumps(value))
        else:
            memo_map = {
                "summary": memo_summary, "topics": memo_topics, "match": memo_match, "rewrite": memo_rewrite,
                "insight": memo_insight, "learn": memo_learn, "thread": memo_thread, "resume": memo_resume,
                "essay": memo_essay, "donor": memo_donor, "trend": memo_trend
            }
            memo_map[scope][cache_key] = value
    except Exception: pass

def rate_limited(identity: str) -> bool:
    now = time.time()
    if R:
        key = f"ai:rl:{identity}"
        with R.pipeline() as p:
            p.zremrangebyscore(key, 0, now - RATE_WINDOW)
            p.zadd(key, {str(now): now})
            p.zcard(key)
            p.expire(key, RATE_WINDOW)
            _, _, c, _ = p.execute()
        return int(c) > RATE_LIMIT_TPM
    bucket = _rate_bucket.setdefault(identity, [])
    while bucket and bucket[0] < now - RATE_WINDOW: bucket.pop(0)
    bucket.append(now)
    return len(bucket) > RATE_LIMIT_TPM

class AITransientError(Exception): ...
class AIPermanentError(Exception): ...

@retry(retry=retry_if_exception_type(AITransientError),
       stop=stop_after_attempt(3),
       wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
       reraise=True)
def call_openai(messages: List[Dict[str, str]], model: str, temperature: float, max_tokens: int) -> str:
    client = get_client()
    if not client: raise AIPermanentError("OpenAI not configured.")
    try:
        resp = client.chat.completions.create(model=model, messages=messages,
                                              temperature=temperature, max_tokens=max_tokens)
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        emsg = str(e).lower()
        if any(t in emsg for t in ["rate limit","timeout","temporarily","overloaded","unavailable","429","502","503","504"]):
            raise AITransientError(emsg)
        raise AIPermanentError(emsg)

def ok(data: Any, **meta): return (jsonify({"ok": True, "data": data, "meta": meta}), 200)
def fail(message: str, code: int = 400, **meta): return (jsonify({"ok": False, "error": {"message": message, "code": code}, "meta": meta}), code)

# ---------------------- Health ----------------------
@ai_bp.route("/health")
def health(): return ok({"openai": bool(has_openai()), "model": MODEL})

# ---------------------- Moderation (lightweight) ----------------------
@ai_bp.route("/moderate", methods=["POST"])
def moderate():
    # client sends { "text": "...", "threshold": 0.8 } where threshold ∈ [0,1]
    data = request.json or {}
    text = sanitize_text(data.get("text",""))
    thr  = float(data.get("threshold", 0.8))
    if not text: return fail("Missing text.", 422)
    # simple heuristic (expand with OpenAI moderation if key present)
    bad_words = ["hate","stupid","idiot","kill","dumb","trash","screw you"]
    score = min(1.0, sum(text.lower().count(w) for w in bad_words) * 0.25)
    flagged = score >= thr
    resp = {"flagged": flagged, "score": round(score, 2)}
    return ok(resp)

# ---------------------- Summary + Sentiment ----------------------
@ai_bp.route("/summary", methods=["POST","GET"])
def summary():
    ident = identity_from_request()
    if rate_limited(ident): return fail("Rate limit exceeded.", 429)
    text = sanitize_text((request.json or {}).get("text","")) if request.method=="POST" else sanitize_text(request.args.get("text",""))
    if not text: return fail("Missing 'text'.", 422)
    ck = f"v2:summary:{hash(text)}:{MODEL}:{MAX_TOKENS_OUT}"
    cached = cache_get(ck, "summary")
    if cached: return ok(cached, cached=True)

    rtime = reading_time_seconds(text)
    reading_level = textstat.text_standard(text, float_output=False) if textstat else None
    truncated = token_truncate(text, MODEL, 6000)

    if has_openai():
        sys = ("You are a concise university assistant. Return JSON with keys: "
               "bullets (max 6), sentiment (positive|neutral|negative), keywords (<=5 lower case), takeaway (1 sentence).")
        messages = [
            {"role":"system","content":sys},
            {"role":"user","content":f"Text:\n{truncated}\nRespond ONLY as minified JSON."}
        ]
        try:
            content = call_openai(messages, MODEL, 0.3, 300)
            # Try parse; if not JSON, fallback to raw
            try:
                data = json.loads(content)
            except Exception:
                data = {"bullets": content.splitlines()[:6], "sentiment":"neutral","keywords":[],"takeaway":""}
        except AIPermanentError as e: return fail(f"AI error: {e}", 500)
        except AITransientError as e:  return fail(f"AI temporarily unavailable: {e}", 503)
    else:
        sentences = re.split(r"(?<=[.!?])\s+", truncated)[:5]
        data = {"bullets": sentences, "sentiment":"neutral", "keywords": [], "takeaway": sentences[0] if sentences else ""}

    result = {"model": MODEL if has_openai() else "fallback",
              "summary": data, "reading_time_seconds": rtime, "reading_level": reading_level}
    cache_set(ck, "summary", result)
    return ok(result, cached=False)

# ---------------------- Topics ----------------------
@ai_bp.route("/topics", methods=["GET"])
def topics():
    ident = identity_from_request()
    if rate_limited(ident): return fail("Rate limit exceeded.", 429)
    seed = sanitize_text(request.args.get("seed","campus life, careers, scholarships"))
    ck = f"v1:topics:{seed}:{MODEL}"
    cached = cache_get(ck,"topics")
    if cached: return ok(cached, cached=True)

    if has_openai():
        sys = "Suggest trending discussion topics for a university platform. Output JSON: { topics: [..] }."
        msgs=[{"role":"system","content":sys},{"role":"user","content":f"Seeds: {seed}. Return 8-10 concise topics."}]
        try:
            content = call_openai(msgs, MODEL, 0.4, 220)
            try:
                payload = json.loads(content)
                topics_list = payload.get("topics") or []
            except Exception:
                topics_list = [t.strip("-• ").strip() for t in content.splitlines() if t.strip()]
        except Exception:
            topics_list = default_topics()
    else:
        topics_list = default_topics()

    result = {"topics": topics_list[:10]}
    cache_set(ck,"topics", result)
    return ok(result, cached=False)

def default_topics():
    return [
        "Best Study Spots Around Campus","Scholarship Application Tips That Work","Internship Interview Strategies",
        "Balancing Classes, Work, and Life","Affordable Housing Near PSU","Alumni AMA: First Year On The Job",
        "Clubs & Groups: Which One’s Right For You?","Research Opportunities This Semester",
        "Networking Events You Shouldn’t Miss","Mental Wellness Resources at PSU"
    ]

# ---------------------- Mentor Match (2.0) ----------------------
@dataclass
class Mentor:
    name: str; field: str; skills: List[str]; availability: int; persona: List[str]

MENTORS = [
    Mentor("Dr. Harrison Wells","Engineering",["cad","matlab","control systems","embedded"],2,["analytical","structured"]),
    Mentor("Rachel Kim","Business Analytics",["sql","python","tableau","forecasting"],3,["supportive","goal-oriented"]),
    Mentor("Jordan P.","Marketing",["copywriting","social","brand","seo"],0,["creative","outgoing"]),
    Mentor("Elena Garcia","Computer Science",["python","ml","java","systems"],1,["logical","curious"]),
    Mentor("Darnell Lee","Education",["curriculum","edtech","assessment"],2,["patient","encouraging"]),
]

@ai_bp.route("/match", methods=["POST","GET"])
def match():
    ident = identity_from_request()
    if rate_limited(ident): return fail("Rate limit exceeded.", 429)

    if request.method=="POST": profile = request.json or {}
    else: profile = {"interests": request.args.get("interests","python, internships, data").split(",")}
    interests = [sanitize_text(i).lower() for i in profile.get("interests",[]) if i]

    goals = [sanitize_text(g).lower() for g in profile.get("goals",[])]
    persona = [sanitize_text(p).lower() for p in profile.get("persona",[])]

    ck = f"v2:match:{','.join(sorted(interests))}:{','.join(sorted(goals))}:{','.join(sorted(persona))}"
    cached = cache_get(ck,"match")
    if cached: return ok(cached, cached=True)

    def score(m: Mentor) -> int:
        base = sum(1 for i in interests for s in m.skills if i.strip() in s)
        avail = 2 if m.availability>0 else 0
        field_bonus = 1 if any(i in m.field.lower() for i in interests) else 0
        persona_bonus = 1 if any(p in m.persona for p in persona) else 0
        return base*2 + field_bonus + avail + persona_bonus

    ranked = sorted(MENTORS, key=score, reverse=True)
    top = [m for m in ranked if m.availability>0][:3] or ranked[:1]

    explanation = None; compatibility = []
    if has_openai():
        try:
            comp = call_openai([
                {"role":"system","content":"Explain mentor matches briefly and positively; return JSON {explanation:'', scores:[number...] }."},
                {"role":"user","content":f"Interests:{interests}\nGoals:{goals}\nPersona:{persona}\nMentors:{[m.name for m in top]} / skills:{[m.skills for m in top]} / persona:{[m.persona for m in top]}"}
            ], MODEL, 0.4, 220)
            try:
                j = json.loads(comp); explanation=j.get("explanation"); compatibility=j.get("scores") or []
            except Exception:
                explanation = comp
        except Exception: explanation=None

    result = {
        "interests": interests, "goals": goals, "persona": persona,
        "matches": [{
            "name": m.name, "field": m.field, "skills": m.skills, "availability": m.availability,
            "persona": m.persona, "compatibility": (compatibility[idx] if idx<len(compatibility) else 75)
        } for idx,m in enumerate(top)],
        "explanation": explanation or "These mentors align with your skills/interests and have availability."
    }
    cache_set(ck,"match",result); return ok(result, cached=False)

# ---------------------- Rewrite ----------------------
@ai_bp.route("/rewrite", methods=["POST"])
def rewrite():
    ident = identity_from_request()
    if rate_limited(ident): return fail("Rate limit exceeded.", 429)
    data = request.json or {}; text = sanitize_text(data.get("text","")); tone = sanitize_text(data.get("tone","friendly and professional"))
    if not text: return fail("Missing 'text'.", 422)
    ck = f"v1:rewrite:{hash(text)}:{tone}"; cached = cache_get(ck,"rewrite")
    if cached: return ok(cached, cached=True)

    truncated = token_truncate(text, MODEL, 6000)
    if has_openai():
        try:
            out = call_openai([
                {"role":"system","content":"Rewrite for clarity, brevity, correctness; preserve meaning."},
                {"role":"user","content":f"Tone: {tone}\nText:\n{truncated}"}
            ], MODEL, 0.2, MAX_TOKENS_OUT)
            result = {"original": text, "rewritten": out, "tone": tone}
        except AIPermanentError as e: return fail(f"AI error: {e}", 500)
        except AITransientError as e:  return fail(f"AI temporarily unavailable: {e}", 503)
    else:
        result = {"original": text, "rewritten": re.sub(r'\s+',' ', text).strip(), "tone": tone, "model":"fallback"}

    cache_set(ck,"rewrite",result); return ok(result, cached=False)

# ---------------------- Insight Bar ----------------------
@ai_bp.route("/insight", methods=["POST"])
def insight():
    """
    Accepts { feed: "...", discussions: "...", jobs: "..."} strings.
    Returns: { sentiment: 'positive|neutral|negative', moodScore: 0-100, topTopics:[], activeUsers:int }
    """
    ident = identity_from_request()
    if rate_limited(ident): return fail("Rate limit exceeded.", 429)
    data = request.json or {}
    feed = sanitize_text(data.get("feed","")); discussions=sanitize_text(data.get("discussions","")); jobs=sanitize_text(data.get("jobs",""))
    ck = f"v1:insight:{hash(feed+discussions+jobs)}"; cached = cache_get(ck,"insight")
    if cached: return ok(cached, cached=True)

    text = f"FEED:\n{feed}\n\nDISCUSSIONS:\n{discussions}\n\nJOBS:\n{jobs}"
    truncated = token_truncate(text, MODEL, 6000)

    if has_openai():
        sys=("Return JSON { sentiment, moodScore (0-100), topTopics:[..], takeaway } for campus status. "
             "Sentiment ∈ {positive, neutral, negative}.")
        try:
            out = call_openai([{"role":"system","content":sys},{"role":"user","content":truncated+" Respond only JSON."}],
                              MODEL, 0.3, 220)
            try: payload = json.loads(out)
            except Exception:
                payload = {"sentiment":"neutral","moodScore":65,"topTopics":[],"takeaway":"Steady week at PSU."}
        except Exception:
            payload = {"sentiment":"neutral","moodScore":65,"topTopics":[],"takeaway":"Steady week at PSU."}
    else:
        payload = {"sentiment":"neutral","moodScore":65,"topTopics":["internships","housing","events"],"takeaway":"Campus activity is moderate."}

    payload["activeUsers"] = int(os.getenv("FAKE_ACTIVE_USERS","3240"))
    cache_set(ck,"insight",payload); return ok(payload, cached=False)

# ---------------------- Learning Path Generator ----------------------
@ai_bp.route("/learning-path", methods=["POST"])
def learning_path():
    ident=identity_from_request()
    if rate_limited(ident): return fail("Rate limit exceeded.", 429)
    data=request.json or {}
    goal=sanitize_text(data.get("goal","data analyst"))
    ck=f"v1:learn:{goal}:{MODEL}"
    cached=cache_get(ck,"learn")
    if cached: return ok(cached, cached=True)

    sys=("Create a PSU-aligned learning path. JSON: { roadmap:[ {title, why, resources:[...] } ], estMonths:int }")
    if has_openai():
        try:
            out = call_openai([{"role":"system","content":sys},{"role":"user","content":f"Goal: {goal}. Return JSON."}],
                              MODEL, 0.4, 380)
            try: payload=json.loads(out)
            except Exception:
                payload={"roadmap":[{"title":"Intro courses","why":"Foundations","resources":["PSU course catalog"]}], "estMonths":6}
        except Exception:
            payload={"roadmap":[{"title":"Intro courses","why":"Foundations","resources":["PSU course catalog"]}], "estMonths":6}
    else:
        payload={"roadmap":[
            {"title":"STAT 101 & CS 101","why":"Math & coding base","resources":["Khan Academy","PSU Catalog"]},
            {"title":"SQL & Tableau","why":"Analytics tools","resources":["W3Schools SQL","Tableau Free"]},
            {"title":"Internship","why":"Real-world exp","resources":["Career Services"]},
        ], "estMonths":8}

    cache_set(ck,"learn",payload); return ok(payload, cached=False)

# ---------------------- Thread Summary ----------------------
@ai_bp.route("/thread/summary", methods=["POST"])
def thread_summary():
    ident=identity_from_request()
    if rate_limited(ident): return fail("Rate limit exceeded.", 429)
    data=request.json or {}; text=sanitize_text(data.get("text",""))
    if not text: return fail("Missing text.",422)
    ck=f"v1:thread:{hash(text)}"; cached=cache_get(ck,"thread")
    if cached: return ok(cached, cached=True)

    truncated=token_truncate(text, MODEL, 6000)
    if has_openai():
        sys=("Summarize a forum thread. JSON { bullets:[..], pro:[..], con:[..], sentiment, suggestions:[..] }")
        try:
            out=call_openai([{"role":"system","content":sys},{"role":"user","content":truncated+" Respond JSON only."}], MODEL,0.3,320)
            try: payload=json.loads(out)
            except Exception:
                payload={"bullets":[],"pro":[],"con":[],"sentiment":"neutral","suggestions":[]}
        except Exception:
            payload={"bullets":[],"pro":[],"con":[],"sentiment":"neutral","suggestions":[]}
    else:
        payload={"bullets": text.split(".")[:5], "pro":[],"con":[],"sentiment":"neutral","suggestions":[]}

    cache_set(ck,"thread",payload); return ok(payload, cached=False)

# ---------------------- Resume Optimizer ----------------------
@ai_bp.route("/resume/optimize", methods=["POST"])
def resume_optimize():
    ident=identity_from_request()
    if rate_limited(ident): return fail("Rate limit exceeded.", 429)
    data=request.json or {}
    resume = sanitize_text(data.get("resume",""))
    job    = sanitize_text(data.get("job_description",""))
    if not resume or not job: return fail("Provide 'resume' and 'job_description'.",422)

    ck=f"v1:resume:{hash(resume+job)}"
    cached=cache_get(ck,"resume")
    if cached: return ok(cached, cached=True)

    if has_openai():
        sys=("Act as a resume optimizer. Return JSON { missingKeywords:[..], improvedSummary:'', bulletSuggestions:[..], score:0-100 }")
        msgs=[{"role":"system","content":sys},
              {"role":"user","content":f"RESUME:\n{resume}\n\nJOB DESCRIPTION:\n{job}\nRespond JSON only."}]
        try:
            out=call_openai(msgs, MODEL, 0.2, 360)
            try: payload=json.loads(out)
            except Exception: payload={"missingKeywords":[],"improvedSummary":"","bulletSuggestions":[],"score":72}
        except Exception: payload={"missingKeywords":[],"improvedSummary":"","bulletSuggestions":[],"score":72}
    else:
        # naive keyword diff
        job_kw=set([w.lower() for w in re.findall(r"[A-Za-z]{3,}", job)])
        res_kw=set([w.lower() for w in re.findall(r"[A-Za-z]{3,}", resume)])
        missing=[k for k in job_kw - res_kw if len(k)>3][:15]
        payload={"missingKeywords":missing,"improvedSummary":"", "bulletSuggestions":[],"score":70}

    cache_set(ck,"resume",payload); return ok(payload, cached=False)

# ---------------------- Essay Analyzer ----------------------
@ai_bp.route("/essay/analyze", methods=["POST"])
def essay_analyze():
    ident=identity_from_request()
    if rate_limited(ident): return fail("Rate limit exceeded.", 429)
    data=request.json or {}
    essay=sanitize_text(data.get("essay","")); criteria=sanitize_text(data.get("criteria","impact, leadership, need"))
    if not essay: return fail("Missing 'essay'.",422)

    ck=f"v1:essay:{hash(essay+criteria)}"
    cached=cache_get(ck,"essay")
    if cached: return ok(cached, cached=True)

    readability = textstat.flesch_reading_ease(essay) if textstat else None
    grade = textstat.text_standard(essay, float_output=False) if textstat else None

    if has_openai():
        sys=("Analyze scholarship essay. Return JSON { strengths:[..], improvements:[..], keywordMatch:[..], confidence:0-100 }")
        msgs=[{"role":"system","content":sys},
              {"role":"user","content":f"ESSAY:\n{essay}\nCRITERIA:\n{criteria}\nRespond JSON only."}]
        try:
            out=call_openai(msgs, MODEL,0.3,360)
            try: payload=json.loads(out)
            except Exception: payload={"strengths":[],"improvements":[],"keywordMatch":[],"confidence":70}
        except Exception: payload={"strengths":[],"improvements":[],"keywordMatch":[],"confidence":70}
    else:
        payload={"strengths":[],"improvements":[],"keywordMatch":criteria.split(","),"confidence":68}

    payload.update({"readability": readability, "gradeLevel": grade})
    cache_set(ck,"essay",payload); return ok(payload, cached=False)

# ---------------------- Donor Story Generator ----------------------
@ai_bp.route("/donor/story", methods=["POST"])
def donor_story():
    ident=identity_from_request()
    if rate_limited(ident): return fail("Rate limit exceeded.", 429)
    data=request.json or {}
    stats=data.get("stats", {"studentsImpacted":12,"fund":"Crimson Legacy","highlight":"engineering internships"})
    ck=f"v1:donor:{hash(json.dumps(stats,sort_keys=True))}"
    cached=cache_get(ck,"donor")
    if cached: return ok(cached, cached=True)

    if has_openai():
        sys=("Write a 2-3 sentence donor impact story. JSON { title:'', body:'' }")
        try:
            out=call_openai([{"role":"system","content":sys},{"role":"user","content":json.dumps(stats)}], MODEL,0.5,180)
            try: payload=json.loads(out)
            except Exception: payload={"title":"Your Impact at PSU","body":"Because of your generosity, students achieved new milestones this term."}
        except Exception:
            payload={"title":"Your Impact at PSU","body":"Because of your generosity, students achieved new milestones this term."}
    else:
        payload={"title":"Your Impact at PSU","body":"Because of your generosity, 12 students completed internships this year."}

    cache_set(ck,"donor",payload); return ok(payload, cached=False)

# ---------------------- Sentiment Trend ----------------------
@ai_bp.route("/sentiment/trend", methods=["POST"])
def sentiment_trend():
    ident=identity_from_request()
    if rate_limited(ident): return fail("Rate limit exceeded.", 429)
    data=request.json or {}
    days=int(data.get("days",7))
    # Fake safe fallback trend (server can later compute from DB)
    trend=[{"day":i, "positive": max(0, 60+int(10*math.sin(i))), "neutral": 25, "negative": max(0,15-int(10*math.sin(i)))} for i in range(1,days+1)]
    return ok({"trend": trend})
