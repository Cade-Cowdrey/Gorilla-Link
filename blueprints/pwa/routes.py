from flask import Blueprint, render_template, jsonify

pwa_bp = Blueprint("pwa_bp", __name__, template_folder="../../templates/pwa")


# ------------------------------------------------------------
#  PWA ONBOARDING
# ------------------------------------------------------------
@pwa_bp.route("/install")
def onboarding():
    """PWA install / onboarding page."""
    features = [
        {"title": "Offline Ready", "desc": "Access saved content without internet."},
        {"title": "Push Notifications", "desc": "Get real-time scholarship and job alerts."},
        {"title": "One-Tap Launch", "desc": "Start instantly from your home screen."},
    ]
    return render_template("pwa/onboarding.html", features=features)


# ------------------------------------------------------------
#  PWA STATUS CHECK API
# ------------------------------------------------------------
@pwa_bp.route("/api/pwa-status")
def status():
    """Returns a small JSON to verify service-worker registration."""
    return jsonify({"pwa_active": True, "version": "1.0.0"})
