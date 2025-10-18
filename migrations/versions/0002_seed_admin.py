"""Seed default System Admin account"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from werkzeug.security import generate_password_hash


# Revision identifiers
revision = '0002_seed_admin'
down_revision = '0001_initial_full'
branch_labels = None
depends_on = None


def upgrade():
    # Define a lightweight users table reference (to insert data)
    users = table(
        'users',
        column('name', sa.String),
        column('email', sa.String),
        column('password_hash', sa.String),
        column('role', sa.String)
    )

    # Pre-hash the default password using Werkzeug
    password_hash = generate_password_hash("Admin123!")

    op.bulk_insert(users, [
        {
            'name': 'System Admin',
            'email': 'admin@pittstate.edu',
            'password_hash': password_hash,
            'role': 'admin'
        }
    ])


def downgrade():
    # Remove admin user if rolling back
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM users WHERE email='admin@pittstate.edu'"))
