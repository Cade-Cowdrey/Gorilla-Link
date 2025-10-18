"""Seed demo private messages between users

Revision ID: 0006_seed_messages
Revises: 0005_seed_demo_posts
Create Date: 2025-10-14
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime

revision = "0006_seed_messages"
down_revision = "0005_seed_demo_posts"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()

    user_map = {
        row["email"]: row["id"]
        for row in connection.execute(sa.text("SELECT id, email FROM users"))
    }

    messages = [
        # Connor ↔ Sarah (student ↔ alumni)
        {
            "sender": "cvandenberg@pittstate.edu",
            "receiver": "sarah.thompson@alumni.pittstate.edu",
            "content": "Hi Sarah! Thanks for your advice on internships. Could we schedule a short Zoom chat?",
            "timestamp": datetime.utcnow(),
        },
        {
            "sender": "sarah.thompson@alumni.pittstate.edu",
            "receiver": "cvandenberg@pittstate.edu",
            "content": "Of course! I’ll email you some available times this week.",
            "timestamp": datetime.utcnow(),
        },

        # Alyssa ↔ Hannah
        {
            "sender": "abrooks@pittstate.edu",
            "receiver": "hdavis@alumni.pittstate.edu",
            "content": "Hi Hannah! I’d love to learn more about your teaching journey after PSU.",
            "timestamp": datetime.utcnow(),
        },
        {
            "sender": "hdavis@alumni.pittstate.edu",
            "receiver": "abrooks@pittstate.edu",
            "content": "Absolutely! I’ll share some resources I used during my student-teaching semesters.",
            "timestamp": datetime.utcnow(),
        },

        # James ↔ Michael
        {
            "sender": "jcarter@pittstate.edu",
            "receiver": "mrodriguez@alumni.pittstate.edu",
            "content": "Hey Michael, do you have any advice on getting internships in engineering or finance?",
            "timestamp": datetime.utcnow(),
        },
        {
            "sender": "mrodriguez@alumni.pittstate.edu",
            "receiver": "jcarter@pittstate.edu",
            "content": "Sure thing! Start with the Career Fair in February and follow up with alumni on LinkedIn.",
            "timestamp": datetime.utcnow(),
        },
    ]

    for msg in messages:
        if user_map.get(msg["sender"]) and user_map.get(msg["receiver"]):
            connection.execute(
                sa.text(
                    """
                    INSERT INTO messages (sender_id, receiver_id, content, created_at)
                    VALUES (:sender_id, :receiver_id, :content, :created_at);
                    """
                ),
                {
                    "sender_id": user_map[msg["sender"]],
                    "receiver_id": user_map[msg["receiver"]],
                    "content": msg["content"],
                    "created_at": msg["timestamp"],
                },
            )


def downgrade():
    connection = op.get_bind()
    connection.execute(sa.text("DELETE FROM messages;"))
