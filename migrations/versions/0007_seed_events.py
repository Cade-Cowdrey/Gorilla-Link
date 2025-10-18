"""Seed demo networking and career events

Revision ID: 0007_seed_events
Revises: 0006_seed_messages
Create Date: 2025-10-14
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime, timedelta

revision = "0007_seed_events"
down_revision = "0006_seed_messages"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    now = datetime.utcnow()

    events = [
        {
            "title": "Spring 2025 Career Fair",
            "description": "Meet employers, alumni, and recruiters at the annual PittState Career Fair in the Overman Student Center.",
            "location": "Overman Student Center Ballroom",
            "start_time": now + timedelta(days=30),
            "end_time": now + timedelta(days=30, hours=4),
        },
        {
            "title": "Communication Department Networking Night",
            "description": "An evening for Communication majors to connect with alumni in marketing, journalism, and PR fields.",
            "location": "Grubbs Hall, Room 109",
            "start_time": now + timedelta(days=45, hours=17),
            "end_time": now + timedelta(days=45, hours=20),
        },
        {
            "title": "Technology & Engineering Alumni Mixer",
            "description": "Kelce Tech alumni return to campus for mentorship sessions and project showcases.",
            "location": "Kansas Technology Center Atrium",
            "start_time": now + timedelta(days=60, hours=18),
            "end_time": now + timedelta(days=60, hours=21),
        },
        {
            "title": "Resume & Interview Workshop",
            "description": "Career Services hosts this session for juniors and seniors to sharpen professional communication skills.",
            "location": "Career Services Office",
            "start_time": now + timedelta(days=10, hours=15),
            "end_time": now + timedelta(days=10, hours=17),
        },
    ]

    for e in events:
        connection.execute(
            sa.text(
                """
                INSERT INTO events (title, description, location, start_time, end_time)
                VALUES (:title, :description, :location, :start_time, :end_time)
                ON CONFLICT (title) DO NOTHING;
                """
            ),
            e,
        )


def downgrade():
    connection = op.get_bind()
    connection.execute(sa.text("DELETE FROM events;"))
