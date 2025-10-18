from flask import Blueprint, jsonify
api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/", methods=["GET"])
def index():
    return jsonify({"ok": True, "name": "PittState-Connect API", "version": 1})
