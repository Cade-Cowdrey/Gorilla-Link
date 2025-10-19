"""Seed PSU-branded demo posts for Gorilla-Link / PittState-Connect"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

# Revision identifiers
revision = "0005_seed_demo_posts"
down_revision = "0004_seed_demo_users"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    posts_table = sa.table(
        "posts",
        sa.column("user_id", sa.Integer),
        sa.column("content", sa.String),
        sa.column("created_at", sa.DateTime),
        sa.column("likes_count", sa.Integer),
        sa.column("comments_count", sa.Integer),
        sa.column("visibility", sa.String),
    )

    # Collect existing post contents to prevent duplication
    existing = [r[0] for r in session.execute(sa.text("SELECT content FROM posts")).all()]

    demo_posts = [
        {
            "user_id": 1,
            "content": "🦍 Excited to announce that PittState-Connect has officially launched! Connecting students, alumni, and faculty across Gorilla Nation.",
            "created_at": datetime.utcnow() - timedelta(days=1),
            "likes_count": 42,
            "comments_count": 7,
            "visibility": "public",
        },
        {
            "user_id": 2,
            "content": "💼 Honored to represent the Kelce College of Business at this year's Faculty Innovation Summit — amazing energy and collaboration!",
            "created_at": datetime.utcnow() - timedelta(days=2),
            "likes_count": 27,
            "comments_count": 3,
            "visibility": "public",
        },
        {
            "user_id": 3,
            "content": "📅 Don’t forget to attend the upcoming Career & Internship Fair next week! Top employers will be at the Weede building — bring your resumes!",
            "created_at": datetime.utcnow() - timedelta(days=3),
            "likes_count": 34,
            "comments_count": 5,
            "visibility": "public",
        },
        {
            "user_id": 4,
            "content": "🏆 Alumni highlight: huge congratulations to our PSU graduates now leading projects at Garmin, Cerner, and Koch Industries. Keep shining Gorillas!",
            "created_at": datetime.utcnow() - timedelta(days=4),
            "likes_count": 18,
            "comments_count": 2,
            "visibility": "public",
        },
        {
            "user_id": 5,
            "content": "🔬 STEM Research Symposium submissions are open! Submit abstracts by Friday to be featured in this year’s Tyler Research Showcase.",
            "created_at": datetime.utcnow() - timedelta(days=5),
            "likes_count": 22,
            "comments_count": 1,
            "visibility": "public",
        },
        {
            "user_id": 1,
            "content": "🎓 Thanks to everyone who joined the Alumni Networking Night! Amazing turnout and energy — proud to be part of Gorilla Nation.",
            "created_at": datetime.utcnow() - timedelta(days=6),
            "likes_count": 31,
            "comments_count": 4,
            "visibility": "public",
        },
    ]

    for post in demo_posts:
        if post["content"] not in existing:
            session.execute(posts_table.insert().values(**post))

    session.commit()
    print("✅ Seeded PSU-branded demo posts successfully.")


def downgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    session.execute(sa.text("""
        DELETE FROM posts
        WHERE content LIKE '🦍 Excited to announce%'
           OR content LIKE '💼 Honored to represent%'
           OR content LIKE '📅 Don’t forget%'
           OR content LIKE '🏆 Alumni highlight%'
           OR content LIKE '🔬 STEM Research%'
           OR content LIKE '🎓 Thanks to everyone%';
    """))
    session.commit()
    print("🧹 Removed PSU-branded demo posts.")
