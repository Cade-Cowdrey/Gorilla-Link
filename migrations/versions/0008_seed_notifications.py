"""Seed demo notifications (likes, comments, connections)

Revision ID: 0008_seed_notifications
Revises: 0007_seed_events
Create Date: 2025-10-14
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime

revision = "0008_seed_notifications"
down_revision = "0007_seed_events"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    now = datetime.utcnow()

    user_map = {
        row["email"]: row["id"]
        for row in connection.execute(sa.text("SELECT id, email FROM users"))
    }

    post_map = {
        row["title"]: row["id"]
        for row in connection.execute(sa.text("SELECT id, title FROM posts"))
    }

    notifications = [
        # Likes
        {
            "user_email": "sarah.thompson@alumni.pittstate.edu",
            "message": "liked your post 'Looking for summer internship advice!'",
            "link": f"/posts/{post_map.get('Looking for summer internship advice!')}",
            "recipient_email": "cvandenberg@pittstate.edu",
        },
        {
            "user_email": "hdavis@alumni.pittstate.edu",
            "message": "liked your post 'Networking with healthcare alumni'",
            "link": f"/posts/{post_map.get('Networking with healthcare alumni')}",
            "recipient_email": "abrooks@pittstate.edu",
        },
        # Comments
        {
            "user_email": "mrodriguez@alumni.pittstate.edu",
            "message": "commented on your post 'Accounting internship openings?'",
            "link": f"/posts/{post_map.get('Accounting internship openings?')}",
            "recipient_email": "jcarter@pittstate.edu",
        },
        # Connections
        {
            "user_email": "sarah.thompson@alumni.pittstate.edu",
            "message": "accepted your connection request",
            "link": "/connections",
            "recipient_email": "cvandenberg@pittstate.edu",
        },
    ]

    for note in notifications:
        if user_map.get(note["user_email"]) and user_map.get(note["recipient_email"]):
            connection.execute(
                sa.text(
                    """
                    INSERT INTO notifications (sender_id, recipient_id, message, link, created_at, is_read)
                    VALUES (:sender_id, :recipient_id, :message, :link, :created_at, false);
                    """
                ),
                {
                    "sender_id": user_map[note["user_email"]],
                    "recipient_id": user_map[note["recipient_email"]],
                    "message": note["message"],
                    "link": note["link"],
                    "created_at": now,
                },
            )


def downgrade():
    connection = op.get_bind()
    connection.execute(sa.text("DELETE FROM notifications;"))
