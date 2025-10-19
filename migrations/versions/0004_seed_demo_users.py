"""Seed demo users for testing (students, faculty, alumni)."""

from alembic import op
import sqlalchemy as sa
from datetime import datetime
from werkzeug.security import generate_password_hash

revision = "0004_seed_demo_users"
down_revision = "0003_seed_departments"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()

    users = [
        ("Cade", "Cowdrey", "cade.cowdrey@pittstate.edu", "Student", "Department of Computer Science"),
        ("Emily", "Thompson", "emily.thompson@pittstate.edu", "Faculty", "College of Education"),
        ("Jordan", "Reed", "jordan.reed@pittstatealumni.com", "Alumni", "Kelce College of Business"),
        ("Taylor", "Nguyen", "taylor.nguyen@pittstate.edu", "Student", "College of Technology"),
    ]

    for first, last, email, role_name, dept_name in users:
        password_hash = generate_password_hash("gorillalink2025")
        bind.execute(
            sa.text(
                """
                INSERT INTO users (first_name, last_name, email, password_hash, role_id, department_id, created_at)
                VALUES (
                    :f, :l, :e, :p,
                    (SELECT id FROM roles WHERE name = :r),
                    (SELECT id FROM departments WHERE name = :d),
                    :c
                )
                """
            ),
            {
                "f": first,
                "l": last,
                "e": email,
                "p": password_hash,
                "r": role_name,
                "d": dept_name,
                "c": datetime.utcnow(),
            },
        )


def downgrade():
    bind = op.get_bind()
    bind.execute(sa.text("DELETE FROM users WHERE email LIKE '%@pittstate%'"))
