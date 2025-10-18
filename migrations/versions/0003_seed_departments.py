"""Seed Pitt State academic departments

Revision ID: 0003_seed_departments
Revises: 0002_seed_admin
Create Date: 2025-10-14
"""

from alembic import op
import sqlalchemy as sa

# Revision identifiers, used by Alembic.
revision = "0003_seed_departments"
down_revision = "0002_seed_admin"
branch_labels = None
depends_on = None


def upgrade():
    departments = [
        # ───────── College of Arts & Sciences ─────────
        {"name": "Biology", "college": "College of Arts & Sciences"},
        {"name": "Communication", "college": "College of Arts & Sciences"},
        {"name": "English & Modern Languages", "college": "College of Arts & Sciences"},
        {"name": "History, Philosophy, and Social Sciences", "college": "College of Arts & Sciences"},
        {"name": "Mathematics", "college": "College of Arts & Sciences"},
        {"name": "Physics", "college": "College of Arts & Sciences"},
        {"name": "Psychology & Counseling", "college": "College of Arts & Sciences"},
        {"name": "Chemistry", "college": "College of Arts & Sciences"},
        {"name": "Music", "college": "College of Arts & Sciences"},
        {"name": "Art", "college": "College of Arts & Sciences"},
        {"name": "Military Science (ROTC)", "college": "College of Arts & Sciences"},

        # ───────── Kelce College of Business ─────────
        {"name": "Accounting", "college": "Kelce College of Business"},
        {"name": "Economics, Finance, and Banking", "college": "Kelce College of Business"},
        {"name": "Management and Marketing", "college": "Kelce College of Business"},
        {"name": "MBA Program", "college": "Kelce College of Business"},

        # ───────── College of Education ─────────
        {"name": "Teaching and Leadership", "college": "College of Education"},
        {"name": "Health, Human Performance, and Recreation", "college": "College of Education"},
        {"name": "Educational Leadership and Research", "college": "College of Education"},
        {"name": "Psychology and Counseling", "college": "College of Education"},

        # ───────── College of Technology ─────────
        {"name": "Engineering Technology", "college": "College of Technology"},
        {"name": "Technology and Workforce Learning", "college": "College of Technology"},
        {"name": "School of Construction", "college": "College of Technology"},
        {"name": "Graphics and Imaging Technologies", "college": "College of Technology"},
        {"name": "Automotive Technology", "college": "College of Technology"},
        {"name": "School of Aviation", "college": "College of Technology"},
    ]

    connection = op.get_bind()
    for dept in departments:
        connection.execute(
            sa.text(
                """
                INSERT INTO departments (name, college)
                VALUES (:name, :college)
                ON CONFLICT (name) DO NOTHING;
                """
            ),
            **dept
        )


def downgrade():
    connection = op.get_bind()
    connection.execute(sa.text("DELETE FROM departments;"))
