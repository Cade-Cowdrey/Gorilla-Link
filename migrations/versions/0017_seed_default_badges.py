"""Seed default badges for CareerBadge

Revision ID: 0017_seed_default_badges
Revises: 0016_add_badge_models
Create Date: 2025-10-17
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic
revision = "0017_seed_default_badges"
down_revision = "0016_add_badge_models"
branch_labels = None
depends_on = None


def upgrade():
    # insert a few starter badges
    badges = [
        {
            "name": "Top Mentor",
            "slug": "top-mentor",
            "label": "Outstanding Mentor",
            "description": "Recognized for providing exceptional mentorship and career guidance.",
            "icon": "fa-solid fa-user-tie",
        },
        {
            "name": "Career Builder",
            "slug": "career-builder",
            "label": "Career Builder",
            "description": "Active participant in career events and job fairs.",
            "icon": "fa-solid fa-briefcase",
        },
        {
            "name": "Campus Leader",
            "slug": "campus-leader",
            "label": "Campus Leader",
            "description": "Recognized for leadership in campus organizations and outreach.",
            "icon": "fa-solid fa-graduation-cap",
        },
        {
            "name": "Alumni Connector",
            "slug": "alumni-connector",
            "label": "Alumni Connector",
            "description": "Bridging the gap between current students and alumni networks.",
            "icon": "fa-solid fa-link",
        },
    ]

    connection = op.get_bind()
    for badge in badges:
        connection.execute(
            sa.text(
                """
                INSERT INTO career_badges (name, slug, label, description, icon, active, created_at)
                VALUES (:name, :slug, :label, :description, :icon, :active, :created_at)
                ON CONFLICT(slug) DO NOTHING
                """
            ),
            {**badge, "active": True, "created_at": datetime.utcnow()},
        )


def downgrade():
    connection = op.get_bind()
    slugs = ["top-mentor", "career-builder", "campus-leader", "alumni-connector"]
    connection.execute(
        sa.text("DELETE FROM career_badges WHERE slug = ANY(:slugs)"),
        {"slugs": slugs},
    )
