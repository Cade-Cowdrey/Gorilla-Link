# utils/report_pdf.py
from datetime import datetime
from flask import render_template, current_app
from weasyprint import HTML, CSS
from io import BytesIO
from utils.analytics_util import run_usage_analytics
from openai import OpenAI
import os

def _ai_monthly_highlights(metrics):
    """
    Optional enhancement: one-paragraph AI narrative tailored to PSU KPIs.
    Falls back gracefully if OpenAI isn't configured.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return ("AI highlights unavailable (no API key configured). "
                "Tip: set OPENAI_API_KEY to enable narrative summaries.")
    try:
        client = OpenAI(api_key=api_key)
        prompt = (
            "You are a data analyst for Pittsburg State University. "
            "Write a crisp, optimistic paragraph (max 80 words) highlighting "
            "the most relevant trends in these monthly platform metrics. "
            "Be specific but non-technical.\n\n"
            f"Metrics JSON: {metrics}"
        )
        result = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content":"Produce a short, executive-ready summary."},
                {"role":"user","content":prompt}
            ],
            max_tokens=140,
            temperature=0.5,
        )
        return (result.choices[0].message.content or "").strip()
    except Exception as e:
        current_app.logger.warning(f"[AI] monthly highlights failed: {e}")
        return "AI highlights were unavailable this month."

def build_monthly_report_pdf(db, month:int, year:int, department_id:int|None=None):
    """
    Returns (filename:str, pdf_bytes:bytes, meta:dict)
    - db: SQLAlchemy db session/handle
    - month/year: target period
    - department_id: optional filter (None for campus-wide)
    """
    # 1) Collect live analytics from your centralized util (already context-safe).
    base_metrics = run_usage_analytics(db, month=month, year=year, department_id=department_id)

    # Shape a stable payload for rendering/AI
    metrics = {
        "users": base_metrics.get("users", 0),
        "new_users": base_metrics.get("new_users", 0),
        "active_users": base_metrics.get("active_users", 0),
        "posts": base_metrics.get("posts", 0),
        "applications": base_metrics.get("applications", 0),
        "scholarships": base_metrics.get("scholarships", 0),
        "departments": base_metrics.get("departments", 0),
        "placements": base_metrics.get("placements", 0),
        "engagement_rate": base_metrics.get("engagement_rate", 0.0),
        "top_departments": base_metrics.get("top_departments", []),  # e.g. [{name, users, posts}, ...]
        "trending_topics": base_metrics.get("trending_topics", []),  # e.g. list[str]
        "time_series": base_metrics.get("time_series", []),          # e.g. [{date, users, posts}, ...]
    }

    # 2) AI narrative
    ai_summary = _ai_monthly_highlights(metrics)

    # 3) Render HTML (responsive + print-friendly)
    period_label = datetime(year, month, 1).strftime("%B %Y")
    html_str = render_template(
        "reports/monthly_report.html",
        period_label=period_label,
        generated_at=datetime.utcnow().strftime("%B %d, %Y %H:%M UTC"),
        department_id=department_id,
        metrics=metrics,
        ai_summary=ai_summary
    )

    # 4) Inline / attach PSU print CSS
    css = CSS(filename=current_app.static_folder + "/css/report-print.css")

    # 5) Generate PDF bytes
    pdf_io = BytesIO()
    HTML(string=html_str, base_url=current_app.root_path).write_pdf(
        pdf_io, stylesheets=[css]
    )
    pdf_io.seek(0)

    # 6) Return
    filename = f"PSU_Monthly_Analytics_{period_label.replace(' ','_')}"
    if department_id:
        filename += f"_Dept{department_id}"
    filename += ".pdf"

    meta = {"period_label": period_label, "department_id": department_id}
    return filename, pdf_io.read(), meta
