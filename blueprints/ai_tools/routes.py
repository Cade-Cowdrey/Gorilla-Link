# blueprints/ai_tools/routes.py
from __future__ import annotations
from flask import Blueprint, request, jsonify

ai_tools_bp = Blueprint("ai_tools_bp", __name__, url_prefix="/ai/tools")

def _score_readability(text: str) -> dict:
    words = len(text.split())
    sentences = max(1, text.count(".") + text.count("!") + text.count("?"))
    avg_len = sum(len(w) for w in text.split())/max(1, words)
    return {"words": words, "sentences": sentences, "avg_word_len": round(avg_len,2)}

@ai_tools_bp.route("/analyze_essay", methods=["POST"])
def analyze_essay():
    payload = request.get_json(silent=True) or {}
    essay = payload.get("text","").strip()
    if not essay:
        return jsonify(ok=False, error={"message":"Missing 'text'"}), 422
    read = _score_readability(essay)
    feedback = [
        "Use active voice and PSU-aligned tone (confident, community-focused).",
        "Lead with impact: scholarship relevance, measurable outcomes.",
        "Tighten sentences; aim for 14–20 words avg.",
    ]
    return jsonify(ok=True, data={"readability": read, "feedback": feedback})

@ai_tools_bp.route("/optimize_resume", methods=["POST"])
def optimize_resume():
    data = request.get_json(silent=True) or {}
    bullets = data.get("bullets", [])
    optimized = []
    for b in bullets[:20]:
        ob = b.strip()
        if ob and not ob.lower().startswith(("led","spearheaded","increased","reduced","built")):
            ob = "Spearheaded " + ob[0].lower() + ob[1:]
        optimized.append(ob)
    return jsonify(ok=True, data={"optimized": optimized})
