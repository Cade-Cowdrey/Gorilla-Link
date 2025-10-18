"""Seed demo jobs and internships for departments"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timedelta

# Revision identifiers
revision = "0012_seed_jobs_internships_demo"
down_revision = "0011_add_connection_model"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    departments = conn.execute(sa.text("SELECT id, name FROM departments")).fetchall()
    now = datetime.utcnow()

    demo_jobs = [
        {
            "title": "Marketing Intern",
            "company": "Jake’s Fireworks",
            "location": "Pittsburg, KS",
            "description": "Assist in social media strategy, campaign reporting, and event marketing during summer fireworks season.",
            "department": "Marketing & Communications",
        },
        {
            "title": "Software Developer Intern",
            "company": "GorillaLink Technologies",
            "location": "Remote / Pittsburg, KS",
            "description": "Build new campus engagement and analytics features using Flask, React, and PostgreSQL.",
            "department": "Computer Information Systems",
        },
        {
            "title": "Supply Chain Analyst Intern",
            "company": "Joplin Logistics Group",
            "location": "Joplin, MO",
            "description": "Work with the logistics team to improve inventory tracking and optimize vendor workflows.",
            "department": "Supply Chain Management",
        },
        {
            "title": "Student Engagement Coordinator",
            "company": "Pitt State Student Life Office",
            "location": "Pittsburg, KS",
            "description": "Coordinate campus activities, mentorship programs, and Greek Life outreach for the semester.",
            "department": "Student Life & Leadership",
        },
        {
            "title": "Public Relations Intern",
            "company": "City of Pittsburg Communications Office",
            "location": "Pittsburg, KS",
            "description": "Assist with media releases, event planning, and digital communications for the local government.",
            "department": "Public Relations",
        },
    ]

    for job in demo_jobs:
        dept = next((d for d in departments if job["department"].lower() in d.name.lower()), None)
        dept_id = dept.id if dept else None
        conn.execute(
            sa.text("""
                INSERT INTO jobs_internships (title, company, location, description, department_id, posted_at, deadline)
                VALUES (:title, :company, :location, :description, :department_id, :posted_at, :deadline)
            """),
            {
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "description": job["description"],
                "department_id": dept_id,
                "posted_at": now,
                "deadline": now + timedelta(days=45),
            },
        )


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM jobs_internships WHERE company IN ('Jake’s Fireworks', 'GorillaLink Technologies', 'Joplin Logistics Group', 'Pitt State Student Life Office', 'City of Pittsburg Communications Office');"))
