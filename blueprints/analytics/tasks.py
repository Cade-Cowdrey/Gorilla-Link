"""
PittState-Connect | Nightly Analytics Tasks
---------------------------------------------------
Handles periodic system analytics refreshes:
 - Updates cached KPI summaries
 - Refreshes donor & funding dashboards
 - Rebuilds AI-powered summaries
 - Regenerates Gorilla Scholars leaderboard
 - Logs metrics snapshots to Redis and DB
"""

import os
import json
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy import text
from extensions import db, cache, redis_client
from utils.mail_util import send_system_email

# Optional: AI-powered summaries
try:
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY")
except Exception:
    openai = None


# --------------------------------------------------
# 🔁 Helper: Safe cache set
# --------------------------------------------------
def safe_cache_set(key: str, value, ttl: int = 86400):
    """Writes to both Redis (if available) and Flask-Cache."""
    try:
        cache.set(key, value, timeout=ttl)
        if redis_client:
            redis_client.set(key, json.dumps(value), ex=ttl)
        logger.info(f"🧠 Cached key={key} (TTL={ttl}s)")
    except Exception as e:
        logger.warning(f"⚠️ Failed to cache key={key}: {e}")


# --------------------------------------------------
# 🧮 1. Core Metrics Aggregation
# --------------------------------------------------
def aggregate_core_metrics():
    """Aggregate overall system metrics from DB."""
    logger.info("📊 Aggregating core PSU metrics...")
    metrics = {}
    try:
        metrics["total_users"] = db.session.execute(text("SELECT COUNT(*) FROM user")).scalar()
        metrics["active_users"] = db.session.execute(text("SELECT COUNT(*) FROM user WHERE last_login > NOW() - INTERVAL '30 days'")).scalar()
        metrics["total_scholarships"] = db.session.execute(text("SELECT COUNT(*) FROM scholarship")).scalar()
        metrics["open_jobs"] = db.session.execute(text("SELECT COUNT(*) FROM job WHERE status='open'")).scalar()
        metrics["departments"] = db.session.execute(text("SELECT COUNT(*) FROM department")).scalar()
        metrics["avg_funding_amount"] = db.session.execute(text("SELECT AVG(amount) FROM scholarship")).scalar() or 0
        metrics["timestamp"] = datetime.utcnow().isoformat()
        safe_cache_set("analytics:core_summary", metrics)
        logger.success("✅ Core analytics metrics cached successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to aggregate core metrics: {e}")
    return metrics


# --------------------------------------------------
# 💰 2. Donor & Funding Insights
# --------------------------------------------------
def aggregate_donor_impact():
    """Calculate donor impact and funding progress."""
    logger.info("💰 Aggregating donor impact metrics...")
    data = {}
    try:
        data["active_donors"] = db.session.execute(text("SELECT COUNT(*) FROM donor WHERE active=true")).scalar()
        data["total_donations"] = db.session.execute(text("SELECT COALESCE(SUM(amount),0) FROM donation")).scalar()
        data["avg_donation"] = db.session.execute(text("SELECT COALESCE(AVG(amount),0) FROM donation")).scalar()
        data["last_updated"] = datetime.utcnow().isoformat()
        safe_cache_set("analytics:donor_summary", data)
        logger.success("✅ Donor and funding impact cached successfully.")
    except Exception as e:
        logger.error(f"❌ Donor analytics aggregation failed: {e}")
    return data


# --------------------------------------------------
# 🧑‍🎓 3. Gorilla Scholars Leaderboard
# --------------------------------------------------
def refresh_leaderboard():
    """Refresh cached leaderboard of top PSU scholars."""
    logger.info("🏆 Refreshing Gorilla Scholars leaderboard...")
    try:
        query = text("""
            SELECT u.id, u.first_name, u.last_name, COUNT(a.id) AS applications, SUM(s.amount) AS total_awarded
            FROM user u
            JOIN scholarship_application a ON a.user_id = u.id
            JOIN scholarship s ON a.scholarship_id = s.id
            WHERE a.status = 'awarded'
            GROUP BY u.id
            ORDER BY total_awarded DESC
            LIMIT 20
        """)
        leaderboard = [dict(row._mapping) for row in db.session.execute(query)]
        safe_cache_set("analytics:leaderboard", leaderboard)
        logger.success("✅ Gorilla Scholars leaderboard updated.")
        return leaderboard
    except Exception as e:
        logger.error(f"❌ Failed to refresh leaderboard: {e}")
        return []


# --------------------------------------------------
# 🧠 4. AI Summary Generator
# --------------------------------------------------
def generate_ai_summary(core_metrics, donor_data, leaderboard):
    """Generate human-readable summary using OpenAI."""
    if not openai:
        logger.warning("⚠️ Skipping AI summary (OpenAI unavailable)")
        return None

    try:
        content = f"""
        PittState-Connect Nightly Summary — {datetime.utcnow().strftime('%Y-%m-%d')}
        Total Users: {core_metrics.get('total_users')}
        Active Users: {core_metrics.get('active_users')}
        Scholarships Available: {core_metrics.get('total_scholarships')}
        Donors Active: {donor_data.get('active_donors')}
        Total Donations: ${donor_data.get('total_donations'):,.2f}
        Top Scholar: {leaderboard[0]['first_name']} {leaderboard[0]['last_name']} (${leaderboard[0]['total_awarded']:,.0f})
        """
        resp = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a PSU data analyst summarizing campus funding and engagement."},
                {"role": "user", "content": content}
            ],
            max_tokens=200,
        )
        summary = resp.choices[0].message.content.strip()
        safe_cache_set("analytics:ai_summary", summary)
        logger.success("🧠 AI summary generated successfully.")
        return summary
    except Exception as e:
        logger.error(f"❌ AI summary generation failed: {e}")
        return None


# --------------------------------------------------
# 🕐 5. Main Entry: Nightly Job
# --------------------------------------------------
def refresh_insight_cache():
    """
    Main nightly scheduled job.
    Aggregates metrics, refreshes caches, and sends summary email.
    """
    logger.info("🌙 Starting nightly analytics refresh...")
    try:
        core = aggregate_core_metrics()
        donor = aggregate_donor_impact()
        leaders = refresh_leaderboard()
        summary = generate_ai_summary(core, donor, leaders)
        safe_cache_set("analytics:last_run", datetime.utcnow().isoformat())
        logger.success("✅ Nightly analytics refresh completed successfully.")
        try:
            send_system_email(
                subject="PittState-Connect | Nightly Analytics Report",
                recipients=[os.getenv("ADMIN_EMAIL", "admin@pittstate.edu")],
                html_body=f"""
                <h2>PittState-Connect Analytics Summary</h2>
                <p><strong>Users:</strong> {core.get('total_users')}</p>
                <p><strong>Scholarships:</strong> {core.get('total_scholarships')}</p>
                <p><strong>Active Donors:</strong> {donor.get('active_donors')}</p>
                <p><strong>Top Scholar:</strong> {leaders[0]['first_name']} {leaders[0]['last_name']}</p>
                <p><strong>Generated:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                <hr>
                <p>{summary or 'AI summary unavailable.'}</p>
                """,
            )
            logger.info("📧 Admin summary email sent successfully.")
        except Exception as mail_error:
            logger.warning(f"⚠️ Could not send analytics email: {mail_error}")
    except Exception as e:
        logger.error(f"❌ Nightly analytics refresh failed: {e}")
