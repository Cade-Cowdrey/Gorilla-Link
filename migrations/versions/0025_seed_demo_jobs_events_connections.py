"""Seed demo data for Jobs, Events, Connections, and Digests"""

from alembic import op
from sqlalchemy.sql import table, column
from sqlalchemy import String, Integer, Boolean, Text, DateTime
from datetime import datetime, timedelta


# Revision identifiers
revision = "0025_seed_demo_jobs_events_connections"
down_revision = "0024_add_missing_models_full"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # ==========================================================
    # 💼 SEED DEMO JOBS
    # ==========================================================
    jobs_table = table(
        "jobs",
        column("title", String),
        column("company", String),
        column("location", String),
        column("job_type", String),
        column("description", Text),
        column("posted_by", Integer),
        column("posted_at", DateTime),
        column("is_active", Boolean),
    )

    jobs_data = [
        {
            "title": "Marketing Intern",
            "company": "Pittsburg State University",
            "location": "Pittsburg, KS",
            "job_type": "Internship",
            "description": "Assist the University Marketing Department with social media content, analytics, and student outreach.",
            "posted_by": 1,
            "posted_at": datetime.utcnow(),
            "is_active": True,
        },
        {
            "title": "Software Engineer (Entry Level)",
            "company": "Gorilla Innovations LLC",
            "location": "Pittsburg, KS",
            "job_type": "Full-time",
            "description": "Develop backend APIs and student tools for PittState-Connect and other community SaaS projects.",
            "posted_by": 1,
            "posted_at": datetime.utcnow(),
            "is_active": True,
        },
        {
            "title": "Business Analyst",
            "company": "Freeman Health Systems",
            "location": "Joplin, MO",
            "job_type": "Full-time",
            "description": "Support data analysis and reporting on healthcare operations using dashboards and SQL queries.",
            "posted_by": 2,
            "posted_at": datetime.utcnow(),
            "is_active": True,
        },
    ]
    conn.execute(jobs_table.insert(), jobs_data)

    # ==========================================================
    # 🎟️ SEED DEMO EVENTS
    # ==========================================================
    events_table = table(
        "events",
        column("title", String),
        column("description", Text),
        column("location", String),
        column("event_date", DateTime),
        column("created_by", Integer),
        column("created_at", DateTime),
    )

    now = datetime.utcnow()
    events_data = [
        {
            "title": "Career & Internship Expo 2025",
            "description": "Meet top employers, network with alumni, and explore job and internship opportunities.",
            "location": "Overman Student Center Ballroom",
            "event_date": now + timedelta(days=30),
            "created_by": 1,
            "created_at": now,
        },
        {
            "title": "Gorilla Alumni Networking Night",
            "description": "Reconnect with fellow Gorillas for a night of stories, success, and student mentorship.",
            "location": "Kelce College of Business Atrium",
            "event_date": now + timedelta(days=60),
            "created_by": 1,
            "created_at": now,
        },
        {
            "title": "Innovation Showcase",
            "description": "Student teams present startup ideas and research projects to local business leaders and investors.",
            "location": "Bicknell Family Center for the Arts",
            "event_date": now + timedelta(days=90),
            "created_by": 2,
            "created_at": now,
        },
    ]
    conn.execute(events_table.insert(), events_data)

    # ==========================================================
    # 🧩 SEED DEMO CONNECTIONS
    # ==========================================================
    connections_table = table(
        "connections",
        column("user_id", Integer),
        column("connected_user_id", Integer),
        column("status", String),
        column("created_at", DateTime),
    )

    connections_data = [
        {"user_id": 1, "connected_user_id": 2, "status": "accepted", "created_at": now},
        {"user_id": 1, "connected_user_id": 3, "status": "accepted", "created_at": now},
        {"user_id": 2, "connected_user_id": 4, "status": "pending", "created_at": now},
    ]
    conn.execute(connections_table.insert(), connections_data)

    # ==========================================================
    # 🗞️ SEED DEMO DIGEST ARCHIVES
    # ==========================================================
    digests_table = table(
        "digest_archives",
        column("title", String),
        column("summary", Text),
        column("pdf_url", String),
        column("created_at", DateTime),
    )

    digests_data = [
        {
            "title": "Jungle Report — Spring 2025",
            "summary": "Celebrating innovation, alumni achievements, and student success across Pitt State.",
            "pdf_url": "/static/pdfs/jungle_report_spring2025.pdf",
            "created_at": now,
        },
        {
            "title": "Jungle Report — Summer 2025",
            "summary": "Highlights from the summer semester, internship stories, and new partnerships with employers.",
            "pdf_url": "/static/pdfs/jungle_report_summer2025.pdf",
            "created_at": now,
        },
    ]
    conn.execute(digests_table.insert(), digests_data)

    # ==========================================================
    # ✉️ SEED DEMO EMAIL DIGEST LOGS
    # ==========================================================
    logs_table = table(
        "email_digest_logs",
        column("recipient_email", String),
        column("subject", String),
        column("sent_at", DateTime),
        column("status", String),
    )

    logs_data = [
        {
            "recipient_email": "student1@pittstate.edu",
            "subject": "Welcome to PittState-Connect — Your Weekly Jungle Report",
            "sent_at": now,
            "status": "sent",
        },
        {
            "recipient_email": "alumni@pittstate.edu",
            "subject": "Reconnect & Mentor Students — PittState-Connect Digest",
            "sent_at": now,
            "status": "sent",
        },
    ]
    conn.execute(logs_table.insert(), logs_data)


def downgrade():
    conn = op.get_bind()
    conn.execute("DELETE FROM email_digest_logs")
    conn.execute("DELETE FROM digest_archives")
    conn.execute("DELETE FROM connections")
    conn.execute("DELETE FROM events")
    conn.execute("DELETE FROM jobs")
