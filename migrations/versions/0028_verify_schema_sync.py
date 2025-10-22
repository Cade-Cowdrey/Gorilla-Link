"""Schema verification for PittState-Connect final build

This migration performs a read-only comparison between the database schema
and the SQLAlchemy model metadata defined in models.py. It does NOT alter
the database but prints a diagnostic summary in the console and logs
mismatches to 'migrations/schema_verification_log.txt'.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, MetaData, Table
from models import db

import os
import datetime


# Revision identifiers
revision = "0028_verify_schema_sync"
down_revision = "0027_pittstate_connect_addons"
branch_labels = None
depends_on = None


def upgrade():
    """Perform schema verification — no actual changes."""
    bind = op.get_bind()
    inspector = inspect(bind)

    log_path = os.path.join("migrations", "schema_verification_log.txt")
    os.makedirs("migrations", exist_ok=True)

    with open(log_path, "w") as f:
        f.write(f"🧩 PittState-Connect Schema Verification Report\n")
        f.write(f"Timestamp: {datetime.datetime.utcnow()}\n\n")

        db_metadata = db.metadata
        model_tables = set(db_metadata.tables.keys())
        db_tables = set(inspector.get_table_names())

        missing_in_db = model_tables - db_tables
        extra_in_db = db_tables - model_tables

        f.write("=== Table Comparison ===\n")
        f.write(f"Tables defined in models.py: {len(model_tables)}\n")
        f.write(f"Tables in DB: {len(db_tables)}\n\n")

        if missing_in_db:
            f.write("❌ Missing tables (in models.py but not in DB):\n")
            for t in sorted(missing_in_db):
                f.write(f"  - {t}\n")
        else:
            f.write("✅ All model tables exist in the database.\n")

        if extra_in_db:
            f.write("\n⚠️ Extra tables (exist in DB but not in models.py):\n")
            for t in sorted(extra_in_db):
                f.write(f"  - {t}\n")

        # Check columns
        f.write("\n=== Column Comparison ===\n")
        for table_name in sorted(model_tables & db_tables):
            model_table = Table(table_name, db_metadata)
            db_cols = {col["name"] for col in inspector.get_columns(table_name)}
            model_cols = {col.name for col in model_table.columns}

            missing_cols = model_cols - db_cols
            extra_cols = db_cols - model_cols

            if missing_cols or extra_cols:
                f.write(f"\n⚠️ Table '{table_name}' mismatch:\n")
                if missing_cols:
                    f.write(f"  ❌ Missing columns in DB: {sorted(missing_cols)}\n")
                if extra_cols:
                    f.write(f"  ⚠️ Extra columns in DB: {sorted(extra_cols)}\n")
            else:
                f.write(f"✅ {table_name} matches models.py\n")

        f.write("\n✅ Verification complete.\n")

    print("\n🧩 Schema verification finished.")
    print("View detailed report in migrations/schema_verification_log.txt")


def downgrade():
    """No changes to revert — this is a diagnostic migration only."""
    print("⏪ No downgrade action (diagnostic only).")
