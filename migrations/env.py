# ================================================================
# 🦍 PittState-Connect — Alembic Environment Configuration
# ================================================================
from __future__ import with_statement
import logging
from alembic import context
from sqlalchemy import engine_from_config, pool
from flask import current_app

# ------------------------------------------------
# Logging
# ------------------------------------------------
logger = logging.getLogger("alembic.env")

# Retrieve config from Flask app
config = context.config
target_metadata = current_app.extensions["migrate"].db.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode (no DB connection)."""
    url = current_app.config.get("SQLALCHEMY_DATABASE_URI")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode (with active DB connection)."""
    connectable = current_app.extensions["migrate"].db.engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=True,  # ✅ Allows ALTER TABLE changes on SQLite / Postgres safely
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
