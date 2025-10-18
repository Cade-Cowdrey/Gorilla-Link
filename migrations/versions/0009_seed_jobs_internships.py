"""Seed demo job and internship postings

Revision ID: 0009_seed_jobs_internships
Revises: 0008_seed_notifications
Create Date: 2025-10-14
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime, timedelta

revision = "0009_seed_jobs_internships"
down_revision = "0008_seed_notifications"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    now = datetime.utcnow()

    department_map = {
        row["name"]: row["id"]
        for row in connection.execute(sa.text("SELECT id, name FROM departments"))
    }

    jobs = [
        {
            "title": "Marketing Internship – Summer 2025",
            "company": "Cerner Corporation",
            "location": "Kansas City, MO",
            "description": "Assist in digital marketing campaigns, content strategy, and brand analytics. Great for Communication and Marketing majors.",
            "department_id": department_map.get("Management and Marketing"),
            "posted_at": now - timedelta(days=2),
            "expires_at": now + timedelta(days=28),
            "type": "Internship",
        },
        {
            "title": "Mechanical Design Engineer Intern",
            "company": "John Deere",
            "location": "Waterloo, IA",
            "description": "Work with senior engineers to design and test mechanical systems. Ideal for Engineering Technology students.",
            "department_id": department_map.get("Engineering Technology"),
            "posted_at": now - timedelta(days=5),
            "expires_at": now + timedelta(days=25),
            "type": "Internship",
        },
        {
            "title": "Accounting Assistant – Part Time",
            "company": "Koch Industries",
            "location": "Wichita, KS",
            "description": "Assist finance team with reporting, auditing, and data entry. Flexible hours for current students.",
            "department_id": department_map.get("Accounting"),
            "posted_at": now - timedelta(days=1),
            "expires_at": now + timedelta(days=30),
            "type": "Job",
        },
        {
            "title": "Psychology Research Assistant",
            "company": "KU Medical Center",
            "location": "Kansas City, KS",
            "description": "Work with behavioral health research projects, data collection, and subject coordination.",
            "department_id": department_map.get("Psychology & Counseling"),
            "posted_at": now - timedelta(days=3),
            "expires_at": now + timedelta(days=20),
            "type": "Internship",
        },
        {
            "title": "Construction Project Coordinator",
            "company": "JE Dunn Construction",
            "location": "Kansas City, MO",
            "description": "Support large-scale commercial construction projects. Suitable for Construction Management majors.",
            "department_id": department_map.get("School of Construction"),
            "posted_at": now - timedelta(days=7),
            "expires_at": now + timedelta(days=21),
            "type": "Job",
        },
    ]

    for job in jobs:
        connection.execute(
            sa.text(
                """
                INSERT INTO jobs (title, company, location, description, department_id, posted_at, expires_at, type)
                VALUES (:title, :company, :location, :description, :department_id, :posted_at, :expires_at, :type)
                ON CONFLICT (title) DO NOTHING;
                """
            ),
            job,
        )


def downgrade():
    connection = op.get_bind()
    connection.execute(sa.text("DELETE FROM jobs;"))
