"""Seed demo analytics statistics for PittState Connect dashboard

Revision ID: 0010_seed_stats
Revises: 0009_seed_jobs_internships
Create Date: 2025-10-14
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime

revision = "0010_seed_stats"
down_revision = "0009_seed_jobs_internships"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    now = datetime.utcnow()

    # Count totals from live data
    totals = {
        "users": connection.execute(sa.text("SELECT COUNT(*) FROM users")).scalar(),
        "departments": connection.execute(sa.text("SELECT COUNT(*) FROM departments")).scalar(),
        "posts": connection.execute(sa.text("SELECT COUNT(*) FROM posts")).scalar(),
        "replies": connection.execute(sa.text("SELECT COUNT(*) FROM replies")).scalar(),
        "connections": connection.execute(sa.text("SELECT COUNT(*) FROM connections")).scalar(),
        "events": connection.execute(sa.text("SELECT COUNT(*) FROM events")).scalar(),
        "jobs": connection.execute(sa.text("SELECT COUNT(*) FROM jobs")).scalar(),
    }

    # Demo trend data for charts (fake but realistic)
    growth_data = [
        {"month": "May 2025", "new_users": 12, "connections_made": 8},
        {"month": "June 2025", "new_users": 18, "connections_made": 12},
        {"month": "July 2025", "new_users": 25, "connections_made": 19},
        {"month": "August 2025", "new_users": 40, "connections_made": 32},
        {"month": "September 2025", "new_users": 58, "connections_made": 50},
        {"month": "October 2025", "new_users": 72, "connections_made": 61},
    ]

    # Insert summary stats for dashboard cards
    connection.execute(
        sa.text(
            """
            INSERT INTO stats (metric, value, updated_at)
            VALUES
                ('Total Users', :users, :now),
                ('Departments', :departments, :now),
                ('Posts', :posts, :now),
                ('Replies', :replies, :now),
                ('Connections', :connections, :now),
                ('Events', :events, :now),
                ('Open Jobs', :jobs, :now)
            ON CONFLICT (metric) DO UPDATE SET value = EXCLUDED.value, updated_at = EXCLUDED.updated_at;
            """
        ),
        {**totals, "now": now},
    )

    # Insert sample growth metrics for line/bar charts
    for g in growth_data:
        connection.execute(
            sa.text(
                """
                INSERT INTO analytics (month, new_users, connections_made)
                VALUES (:month, :new_users, :connections_made)
                ON CONFLICT (month) DO NOTHING;
                """
            ),
            g,
        )


def downgrade():
    connection = op.get_bind()
    connection.execute(sa.text("DELETE FROM stats;"))
    connection.execute(sa.text("DELETE FROM analytics;"))
