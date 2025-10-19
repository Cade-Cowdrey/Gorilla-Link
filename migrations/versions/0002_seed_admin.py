"""Seed initial admin role and account."""

from alembic import op
import sqlalchemy as sa
from datetime import datetime
from werkzeug.security import generate_password_hash

revision = "0002_seed_admin"
down_revision = "0001_initial_full"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()

    roles = [
        ("Admin", "System administrator with full access."),
        ("Faculty", "PSU faculty member."),
        ("Student", "Current student."),
        ("Alumni", "Pitt State alumnus/alumna."),
    ]

    for name, desc in roles:
        bind.execute(
            sa.text("INSERT INTO roles (name, description, created_at) VALUES (:n, :d, :c)"),
            {"n": name, "d": desc, "c": datetime.utcnow()},
        )

    admin_email = "admin@pittstate-connect.edu"
    password_hash = generate_password_hash("gorillalink2025")

    bind.execute(
        sa.text(
            """
            INSERT INTO users (first_name, last_name, email, password_hash, role_id, is_active, created_at)
            VALUES ('System', 'Admin', :e, :p, 
                (SELECT id FROM roles WHERE name='Admin'), true, :c)
            """
        ),
        {"e": admin_email, "p": password_hash, "c": datetime.utcnow()},
    )


def downgrade():
    bind = op.get_bind()
    bind.execute(sa.text("DELETE FROM users WHERE email='admin@pittstate-connect.edu'"))
    bind.execute(sa.text("DELETE FROM roles"))
