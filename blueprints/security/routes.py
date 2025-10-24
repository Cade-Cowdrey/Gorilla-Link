# blueprints/security/routes.py
from __future__ import annotations
from flask import Blueprint, request, jsonify, render_template

security_bp = Blueprint("security_bp", __name__, url_prefix="/admin")

_flagged_store: list[dict] = []  # replace with DB

@security_bp.route("/audit")
def audit_page():
    return render_template("admin/audit.html", items=_flagged_store)

@security_bp.route("/moderate", methods=["POST"])
def moderate_text():
    data = request.get_json(silent=True) or {}
    text = data.get("text","")
    threshold = float(data.get("threshold", 0.8))
    bad_words = ["hate","stupid","idiot","kill","dumb","trash","screw you"]
    score = min(1.0, sum(text.lower().count(w) for w in bad_words) * 0.25)
    flagged = score >= threshold
    item = {"text": text, "score": round(score,2), "flagged": flagged}
    if flagged: _flagged_store.append(item)
    return jsonify(ok=True, data=item)
