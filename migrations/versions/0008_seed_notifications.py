"""Seed PSU notifications"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from datetime import datetime

# Revision identifiers, used by Alembic.
revision = "0008_seed_notifications"
down_revision = "0007_seed_events"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    notifications_table = sa.table(
        "notifications",
        sa.column("user_id", sa.Integer),
        sa.column("message", sa.String),
        sa.column("link", sa.String),
        sa.column("timestamp", sa.DateTime),
        sa.column("is_read", sa.Boolean),
    )

    existing_msgs = [r[0] for r in session.execute(sa.text("SELECT message FROM notifications")).all()]
    new_notifications = [
        {
            "user_id": 1,
            "message": "🎉 Welcome to PittState-Connect! Start exploring your new dashboard.",
            "link": "/feed",
            "timestamp": datetime.utcnow(),
            "is_read": False,
        },
        {
            "user_id": 2,
            "message": "🏫 The Faculty Innovation Summit is next week — RSVP now!",
            "link": "/events",
            "timestamp": datetime.utcnow(),
            "is_read": False,
        },
        {
            "user_id": 3,
            "message": "💼 Career & Internship Fair opens soon! Update your profile for recruiters.",
            "link": "/careers",
            "timestamp": datetime.utcnow(),
            "is_read": False,
        },
        {
            "user_id": 4,
            "message": "🏅 You earned the ‘Gorilla Pride’ badge for campus involvement!",
            "link": "/badges/dashboard",
            "timestamp": datetime.utcnow(),
            "is_read": False,
        },
        {
            "user_id": 5,
            "message": "🦍 Your weekly digest is ready. Stay connected with PSU updates!",
            "link": "/notifications",
            "timestamp": datetime.utcnow(),
            "is_read": False,
        },
    ]

    for n in new_notifications:
        if n["message"] not in existing_msgs:
            session.execute(notifications_table.insert().values(**n))

    session.commit()
    print("✅ Seeded PSU demo notifications successfully.")


def downgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    session.execute(sa.text("DELETE FROM notifications WHERE message LIKE '🎉 Welcome to PittState%' OR message LIKE '🏫 The Faculty%' OR message LIKE '💼 Career%' OR message LIKE '🏅 You earned%' OR message LIKE '🦍 Your weekly digest%';"))
    session.commit()
    print("🧹 Removed PSU demo notifications.")
