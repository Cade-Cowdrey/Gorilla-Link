"""Seed PSU-branded demo messages for Gorilla-Link / PittState-Connect"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

# Revision identifiers
revision = "0006_seed_messages"
down_revision = "0005_seed_demo_posts"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    messages_table = sa.table(
        "messages",
        sa.column("sender_id", sa.Integer),
        sa.column("receiver_id", sa.Integer),
        sa.column("content", sa.String),
        sa.column("timestamp", sa.DateTime),
        sa.column("is_read", sa.Boolean),
    )

    # Prevent duplicates
    existing_msgs = [r[0] for r in session.execute(sa.text("SELECT content FROM messages")).all()]

    demo_messages = [
        {
            "sender_id": 1,
            "receiver_id": 2,
            "content": "Hey Dr. Davis, just wanted to say thanks for helping me prep for the Faculty Innovation Summit!",
            "timestamp": datetime.utcnow() - timedelta(hours=12),
            "is_read": True,
        },
        {
            "sender_id": 2,
            "receiver_id": 1,
            "content": "Anytime! Your presentation on digital engagement was excellent — Pitt State is lucky to have students like you.",
            "timestamp": datetime.utcnow() - timedelta(hours=11),
            "is_read": True,
        },
        {
            "sender_id": 3,
            "receiver_id": 4,
            "content": "Hi, I saw your alumni post about Koch Industries — would you be open to chatting about your career path?",
            "timestamp": datetime.utcnow() - timedelta(hours=10),
            "is_read": False,
        },
        {
            "sender_id": 4,
            "receiver_id": 3,
            "content": "Of course! I’d be happy to share insights. Let’s set up a quick Zoom later this week.",
            "timestamp": datetime.utcnow() - timedelta(hours=9),
            "is_read": False,
        },
        {
            "sender_id": 5,
            "receiver_id": 1,
            "content": "Hey! Can you review my STEM Symposium abstract before Friday?",
            "timestamp": datetime.utcnow() - timedelta(hours=8),
            "is_read": False,
        },
        {
            "sender_id": 1,
            "receiver_id": 5,
            "content": "Sure thing — send it over tonight and I’ll give feedback by tomorrow morning.",
            "timestamp": datetime.utcnow() - timedelta(hours=7),
            "is_read": False,
        },
        {
            "sender_id": 2,
            "receiver_id": 3,
            "content": "Reminder: Career & Internship Fair next week. Update your profile to stand out to employers!",
            "timestamp": datetime.utcnow() - timedelta(hours=6),
            "is_read": True,
        },
        {
            "sender_id": 3,
            "receiver_id": 2,
            "content": "Thanks! I’m polishing my resume and Handshake profile now.",
            "timestamp": datetime.utcnow() - timedelta(hours=5),
            "is_read": True,
        },
        {
            "sender_id": 4,
            "receiver_id": 5,
            "content": "Loved your presentation in the research symposium preview! Keep it up — your data visuals were excellent.",
            "timestamp": datetime.utcnow() - timedelta(hours=4),
            "is_read": False,
        },
        {
            "sender_id": 5,
            "receiver_id": 4,
            "content": "Thank you! Appreciate your feedback — hoping to publish the final version soon.",
            "timestamp": datetime.utcnow() - timedelta(hours=3),
            "is_read": False,
        },
    ]

    for m in demo_messages:
        if m["content"] not in existing_msgs:
            session.execute(messages_table.insert().values(**m))

    session.commit()
    print("✅ Seeded PSU-branded demo messages successfully.")


def downgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    session.execute(sa.text("""
        DELETE FROM messages WHERE content LIKE 'Hey Dr.%'
           OR content LIKE 'Anytime!%'
           OR content LIKE 'Hi, I saw your alumni%'
           OR content LIKE 'Of course!%'
           OR content LIKE 'Hey! Can you review%'
           OR content LIKE 'Sure thing%'
           OR content LIKE 'Reminder: Career%'
           OR content LIKE 'Thanks! I’m polishing%'
           OR content LIKE 'Loved your presentation%'
           OR content LIKE 'Thank you! Appreciate%';
    """))
    session.commit()
    print("🧹 Removed PSU-branded demo messages.")
