"""Seed PSU events"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

# Revision identifiers, used by Alembic.
revision = "0007_seed_events"
down_revision = "0006_seed_messages"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    events_table = sa.table(
        "events",
        sa.column("title", sa.String),
        sa.column("description", sa.String),
        sa.column("date", sa.DateTime),
        sa.column("location", sa.String),
        sa.column("department_id", sa.Integer),
    )

    existing = [r[0] for r in session.execute(sa.text("SELECT title FROM events")).all()]
    new_events = [
        {
            "title": "Alumni Networking Night",
            "description": "Reconnect with fellow Gorillas and expand your professional network.",
            "date": datetime.utcnow() + timedelta(days=7),
            "location": "Overman Student Center Ballroom",
            "department_id": 1,
        },
        {
            "title": "Career and Internship Fair",
            "description": "Meet top employers hiring Pitt State students and alumni.",
            "date": datetime.utcnow() + timedelta(days=14),
            "location": "Weede Physical Education Building",
            "department_id": 2,
        },
        {
            "title": "Faculty Innovation Summit",
            "description": "Collaborate on new teaching strategies and mentorship programs.",
            "date": datetime.utcnow() + timedelta(days=21),
            "location": "Kelce College of Business",
            "department_id": 3,
        },
        {
            "title": "Gorilla Pride Parade",
            "description": "Celebrate PSU spirit and community pride downtown!",
            "date": datetime.utcnow() + timedelta(days=28),
            "location": "Downtown Pittsburg, KS",
            "department_id": 4,
        },
        {
            "title": "STEM Research Symposium",
            "description": "Students present groundbreaking research across science and engineering.",
            "date": datetime.utcnow() + timedelta(days=35),
            "location": "Tyler Research Center",
            "department_id": 5,
        },
    ]

    for e in new_events:
        if e["title"] not in existing:
            session.execute(events_table.insert().values(**e))

    session.commit()
    print("✅ Seeded PSU demo events successfully.")


def downgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    session.execute(sa.text("DELETE FROM events WHERE title IN ('Alumni Networking Night','Career and Internship Fair','Faculty Innovation Summit','Gorilla Pride Parade','STEM Research Symposium');"))
    session.commit()
    print("🧹 Removed PSU demo events.")
