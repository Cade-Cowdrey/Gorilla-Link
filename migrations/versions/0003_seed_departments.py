"""Seed initial PSU academic departments."""

from alembic import op
import sqlalchemy as sa
from datetime import datetime

revision = "0003_seed_departments"
down_revision = "0002_seed_admin"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()

    departments = [
        "Kelce College of Business",
        "College of Technology",
        "College of Education",
        "College of Arts & Sciences",
        "School of Construction",
        "School of Nursing",
        "School of Automotive Technology",
        "Department of Computer Science",
        "Department of Biology",
        "Department of Psychology",
    ]

    for dept in departments:
        bind.execute(
            sa.text(
                "INSERT INTO departments (name, description, created_at) VALUES (:n, :d, :c)"
            ),
            {
                "n": dept,
                "d": f"{dept} — official academic division of Pittsburg State University.",
                "c": datetime.utcnow(),
            },
        )


def downgrade():
    bind = op.get_bind()
    bind.execute(sa.text("DELETE FROM departments"))
