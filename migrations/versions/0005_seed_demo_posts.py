"""Seed demo posts"""
from datetime import datetime, timedelta
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from models import User, Post

# revision identifiers
revision = '0005_seed_demo_posts'
down_revision = '0004_seed_demo_users'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    users = session.query(User).all()
    demo_posts = []

    sample_texts = [
        "Excited to share that I got an internship with Cerner!",
        "Just finished a major project on AI-powered tutoring systems.",
        "PSU networking event was amazing this week!",
        "Graduated with honors — so proud to be a Gorilla!",
        "Research paper on sustainable business models now published!",
    ]

    for i, user in enumerate(users):
        post = Post(
            author=user,
            content=sample_texts[i % len(sample_texts)],
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 14))
        )
        demo_posts.append(post)

    session.add_all(demo_posts)
    session.commit()
    print("✅ Seeded demo posts successfully.")


def downgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    session.query(Post).delete()
    session.commit()
