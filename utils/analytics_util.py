from datetime import datetime

def run_usage_analytics(db):
    """
    Collect key usage metrics for PittState-Connect.
    Extendable for department KPIs, engagement rates, AI usage, etc.
    """
    try:
        from models import User, Post, Department, Scholarship

        # Safely run lightweight counts
        total_users = db.session.query(User).count()
        total_posts = db.session.query(Post).count()
        total_departments = db.session.query(Department).count()
        total_scholarships = db.session.query(Scholarship).count()

        # Example extended metrics
        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "users": total_users,
            "posts": total_posts,
            "departments": total_departments,
            "scholarships": total_scholarships,
        }

        # Placeholder for external dashboard push (future-ready)
        # push_to_dashboard(data)

        return data

    except Exception as e:
        # No crash — returns partial results
        return {"timestamp": datetime.utcnow().isoformat(), "error": str(e)}
