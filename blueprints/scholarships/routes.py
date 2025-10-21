from flask import Blueprint, render_template, request
bp = Blueprint("scholarships_bp", __name__, url_prefix="/scholarships")

@bp.get("/hub")
def hub():
    return render_template("scholarships/hub.html")

@bp.get("/recommender")
def recommender():
    # Placeholder Smart Match view
    q = request.args.get("q", "")
    return render_template("scholarships/recommender.html", query=q)

@bp.get("/deadlines")
def deadlines():
    return render_template("scholarships/deadlines.html")

@bp.get("/progress")
def progress():
    return render_template("scholarships/progress.html")

@bp.get("/essay-library")
def essay_library():
    return render_template("scholarships/essay_library.html")

@bp.get("/financial-literacy")
def financial_literacy():
    return render_template("scholarships/financial_literacy.html")

@bp.get("/cost-to-completion")
def cost_to_completion():
    return render_template("scholarships/cost_to_completion.html")

@bp.get("/funding-journey")
def funding_journey():
    return render_template("scholarships/funding_journey.html")

@bp.get("/faculty-recommendations")
def faculty_recommendations():
    return render_template("scholarships/faculty_recommendations.html")

@bp.get("/leaderboard")
def leaderboard():
    return render_template("scholarships/leaderboard.html")

@bp.get("/peer-mentors")
def peer_mentors():
    return render_template("scholarships/peer_mentors.html")

@bp.get("/impact-stories")
def impact_stories():
    return render_template("scholarships/impact_stories.html")
