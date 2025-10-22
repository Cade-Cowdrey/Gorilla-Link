"""
Safe placeholder AI layer.
Later: wire to your own key-layer or OpenAI SDK.
All functions return deterministic mock data for demos.
"""
import os
from typing import List, Dict

USE_AI = os.environ.get("ENABLE_AI", "0") == "1"

def ai_scholarship_smart_match(profile: Dict, scholarships: List[Dict]) -> List[Dict]:
    if not USE_AI:
        # Simple deterministic scoring by tag overlap for demo
        tags = set([t.lower() for t in profile.get("tags", [])])
        scored = []
        for s in scholarships:
            stags = set([t.lower() for t in s.get("tags", [])])
            score = len(tags & stags)
            scored.append({**s, "match_score": score})
        return sorted(scored, key=lambda x: x["match_score"], reverse=True)[:10]
    # When ENABLE_AI=1 later, call your key-layer here.
    return []

def ai_essay_suggestions(prompt: str) -> str:
    if not USE_AI:
        return (
            "Suggestion 1: Start with a vivid personal anecdote.\n"
            "Suggestion 2: Tie your achievements to PSU values.\n"
            "Suggestion 3: End with future impact and gratitude."
        )
    return "AI suggestions would appear here."

def ai_resume_feedback(resume_text: str) -> Dict:
    if not USE_AI:
        return {
            "summary": "Clear structure. Add quant metrics and leadership verbs.",
            "ats_score": 78,
            "tips": ["Add 2 quantifiable bullets", "Mirror keywords from job post", "Reorder for relevance"]
        }
    return {"summary": "AI feedback placeholder", "ats_score": 0, "tips": []}
