"""Seed PSU-branded job and internship listings for Gorilla-Link / PittState-Connect"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

# Revision identifiers
revision = "0009_seed_jobs_internships"
down_revision = "0008_seed_notifications"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    jobs_table = sa.table(
        "jobs",
        sa.column("title", sa.String),
        sa.column("company", sa.String),
        sa.column("department_id", sa.Integer),
        sa.column("location", sa.String),
        sa.column("job_type", sa.String),
        sa.column("posted_at", sa.DateTime),
        sa.column("deadline", sa.DateTime),
        sa.column("description", sa.Text),
        sa.column("is_active", sa.Boolean),
    )

    existing_jobs = [r[0] for r in session.execute(sa.text("SELECT title FROM jobs")).all()]

    now = datetime.utcnow()

    demo_jobs = [
        {
            "title": "Software Engineering Intern (Summer 2025)",
            "company": "Garmin International",
            "department_id": 3,  # Computer Science
            "location": "Olathe, KS",
            "job_type": "Internship",
            "posted_at": now - timedelta(days=4),
            "deadline": now + timedelta(days=30),
            "description": (
                "Join Garmin’s Engineering Internship Program and work with embedded systems, "
                "C/C++ development, and product innovation alongside Pitt State alumni mentors."
            ),
            "is_active": True,
        },
        {
            "title": "Business Analyst Intern",
            "company": "Koch Industries",
            "department_id": 2,  # Business Administration
            "location": "Wichita, KS",
            "job_type": "Internship",
            "posted_at": now - timedelta(days=5),
            "deadline": now + timedelta(days=25),
            "description": (
                "Assist in analyzing operational data, creating dashboards, and supporting decision-making "
                "processes at Koch Industries. Ideal for Kelce College of Business students."
            ),
            "is_active": True,
        },
        {
            "title": "Healthcare Data Analyst",
            "company": "Cerner Corporation (Oracle Health)",
            "department_id": 6,  # Health Informatics / Nursing
            "location": "Kansas City, MO",
            "job_type": "Full-Time",
            "posted_at": now - timedelta(days=8),
            "deadline": now + timedelta(days=20),
            "description": (
                "Work with large healthcare datasets to improve patient outcomes using analytics "
                "and visualization tools. Pitt State alumni currently leading this team!"
            ),
            "is_active": True,
        },
        {
            "title": "Marketing Coordinator",
            "company": "Pittsburg State University Marketing Dept.",
            "department_id": 5,  # Communications
            "location": "Pittsburg, KS",
            "job_type": "Full-Time",
            "posted_at": now - timedelta(days=3),
            "deadline": now + timedelta(days=15),
            "description": (
                "Coordinate on-campus campaigns, student engagement initiatives, and digital content "
                "for PSU social media. Great for students passionate about community impact."
            ),
            "is_active": True,
        },
        {
            "title": "Mechanical Design Engineer",
            "company": "John Deere",
            "department_id": 4,  # Engineering Technology
            "location": "Waterloo, IA",
            "job_type": "Full-Time",
            "posted_at": now - timedelta(days=6),
            "deadline": now + timedelta(days=40),
            "description": (
                "Collaborate with senior engineers to design and test mechanical components. "
                "Preferred candidates: PSU Mechanical Engineering Technology graduates."
            ),
            "is_active": True,
        },
        {
            "title": "Research Assistant – STEM Grant Program",
            "company": "Pittsburg State University Research Office",
            "department_id": 7,  # Science / STEM
            "location": "Pittsburg, KS",
            "job_type": "Part-Time",
            "posted_at": now - timedelta(days=1),
            "deadline": now + timedelta(days=10),
            "description": (
                "Assist faculty in laboratory research, data entry, and grant reporting "
                "for ongoing STEM education projects."
            ),
            "is_active": True,
        },
    ]

    for job in demo_jobs:
        if job["title"] not in existing_jobs:
            session.execute(jobs_table.insert().values(**job))

    session.commit()
    print("✅ Seeded PSU-branded job and internship listings successfully.")


def downgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    session.execute(sa.text("""
        DELETE FROM jobs WHERE
            title LIKE 'Software Engineering Intern%'
            OR title LIKE 'Business Analyst Intern%'
            OR title LIKE 'Healthcare Data Analyst%'
            OR title LIKE 'Marketing Coordinator%'
            OR title LIKE 'Mechanical Design Engineer%'
            OR title LIKE 'Research Assistant%';
    """))
    session.commit()
    print("🧹 Removed PSU-branded job and internship listings.")
