def summarize_metrics(metrics: dict) -> dict:
    return {
        "users": metrics.get("users", 0),
        "alumni": metrics.get("alumni", 0),
        "jobs": metrics.get("jobs", 0),
        "scholarships": metrics.get("scholarships", 0),
        "engagement_rate": metrics.get("engagement_rate", 0.0),
    }
