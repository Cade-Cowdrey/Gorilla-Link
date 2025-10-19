"""Seed PSU-branded analytics and performance stats for Gorilla-Link / PittState-Connect"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from datetime import datetime

# Revision identifiers
revision = "0010_seed_stats"
down_revision = "0009_seed_jobs_internships"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    stats_table = sa.table(
        "stats",
        sa.column("category", sa.String),
        sa.column("label", sa.String),
        sa.column("value", sa.Float),
        sa.column("last_updated", sa.DateTime),
        sa.column("description", sa.Text),
    )

    # Collect existing labels to avoid duplicates
    existing_labels = [r[0] for r in session.execute(sa.text("SELECT label FROM stats")).all()]

    now = datetime.utcnow()

    demo_stats = [
        # 🎓 Student & Alumni Success
        {
            "category": "student_outcomes",
            "label": "Graduation Rate",
            "value": 72.4,
            "last_updated": now,
            "description": "Percentage of PSU students who complete their degrees within 6 years.",
        },
        {
            "category": "student_outcomes",
            "label": "Job Placement Rate",
            "value": 94.1,
            "last_updated": now,
            "description": "Percent of Pitt State graduates employed or continuing education within 6 months of graduation.",
        },
        {
            "category": "student_outcomes",
            "label": "Average Starting Salary",
            "value": 58800,
            "last_updated": now,
            "description": "Average starting salary for PSU graduates across all majors.",
        },

        # 🧑‍💼 Alumni & Mentorship Engagement
        {
            "category": "alumni_engagement",
            "label": "Active Alumni Mentors",
            "value": 312,
            "last_updated": now,
            "description": "Number of verified alumni currently mentoring students via PittState-Connect.",
        },
        {
            "category": "alumni_engagement",
            "label": "Monthly Alumni Logins",
            "value": 1278,
            "last_updated": now,
            "description": "Unique alumni logins on the platform over the past 30 days.",
        },
        {
            "category": "alumni_engagement",
            "label": "Mentorship Matches",
            "value": 215,
            "last_updated": now,
            "description": "Total student-alumni mentorship matches facilitated through Gorilla-Link.",
        },

        # 💼 Career Services Performance
        {
            "category": "career_services",
            "label": "Active Job Listings",
            "value": 128,
            "last_updated": now,
            "description": "Number of currently active job and internship postings in the PSU career board.",
        },
        {
            "category": "career_services",
            "label": "Career Fair Employers",
            "value": 92,
            "last_updated": now,
            "description": "Employers registered for the latest PSU Career & Internship Fair.",
        },
        {
            "category": "career_services",
            "label": "Career Appointments This Month",
            "value": 143,
            "last_updated": now,
            "description": "Individual career advising sessions conducted this month via the platform.",
        },

        # 📈 Engagement Metrics
        {
            "category": "platform_engagement",
            "label": "Posts Created",
            "value": 524,
            "last_updated": now,
            "description": "Number of new posts and discussions made across all feed channels.",
        },
        {
            "category": "platform_engagement",
            "label": "Messages Sent",
            "value": 1087,
            "last_updated": now,
            "description": "Private messages exchanged between users across mentorship and networking threads.",
        },
        {
            "category": "platform_engagement",
            "label": "Events RSVPs",
            "value": 384,
            "last_updated": now,
            "description": "Total RSVPs for recent Pitt State events hosted through the Connect platform.",
        },

        # 🦍 Institutional Growth
        {
            "category": "institutional",
            "label": "Active Students",
            "value": 6550,
            "last_updated": now,
            "description": "Current active PSU students across all colleges.",
        },
        {
            "category": "institutional",
            "label": "Total Alumni Network",
            "value": 64000,
            "last_updated": now,
            "description": "Number of Pitt State alumni worldwide connected to the Gorilla Network.",
        },
        {
            "category": "institutional",
            "label": "Funding Growth (5-Year)",
            "value": 23.8,
            "last_updated": now,
            "description": "Percentage growth in university funding over the last five years driven by alumni engagement and visibility.",
        },
    ]

    for stat in demo_stats:
        if stat["label"] not in existing_labels:
            session.execute(stats_table.insert().values(**stat))

    session.commit()
    print("✅ Seeded PSU-branded analytics & stats successfully.")


def downgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    session.execute(sa.text("""
        DELETE FROM stats WHERE
            label IN (
                'Graduation Rate',
                'Job Placement Rate',
                'Average Starting Salary',
                'Active Alumni Mentors',
                'Monthly Alumni Logins',
                'Mentorship Matches',
                'Active Job Listings',
                'Career Fair Employers',
                'Career Appointments This Month',
                'Posts Created',
                'Messages Sent',
                'Events RSVPs',
                'Active Students',
                'Total Alumni Network',
                'Funding Growth (5-Year)'
            );
    """))
    session.commit()
    print("🧹 Removed PSU analytics & stats.")
