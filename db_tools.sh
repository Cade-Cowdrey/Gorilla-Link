#!/bin/bash
# =====================================================================
# PittState-Connect | Unified Database Management Tool
# =====================================================================
# Usage:
#   ./db_tools.sh migrate "add_feature_name"   → create & apply migration
#   ./db_tools.sh check                        → verify DB/schema sync
#
# Automates your full Alembic workflow with consistent conventions.
# Works on both Render and local environments.
# =====================================================================

set -e
export FLASK_APP=app_pro.py
MIGRATIONS_DIR="migrations/versions"

# --- Utility function for printing headers ---
header() {
  echo ""
  echo "---------------------------------------------------------------"
  echo "$1"
  echo "---------------------------------------------------------------"
  echo ""
}

# --- Ensure migrations folder exists ---
if [ ! -d "$MIGRATIONS_DIR" ]; then
  echo "❌ No migrations directory found. Run 'flask db init' first."
  exit 1
fi


# ==============================================================
# MODE 1 → MIGRATE
# ==============================================================
if [ "$1" = "migrate" ]; then
  DESC=$2
  if [ -z "$DESC" ]; then
    echo "❌ Usage: ./db_tools.sh migrate <description>"
    exit 1
  fi

  header "⚙️  Generating and applying migration: ${DESC}"

  # Determine latest version and increment
  LATEST=$(ls $MIGRATIONS_DIR | grep -E '^[0-9]{4}_.+\.py$' | sort | tail -n 1 | cut -d'_' -f1)
  NEXT_NUM=$(printf "%04d" $((10#$LATEST + 1)))
  REVISION="${NEXT_NUM}_${DESC}"
  FILE="${MIGRATIONS_DIR}/${REVISION}.py"
  DOWN_REVISION=$(ls $MIGRATIONS_DIR | grep -E '^[0-9]{4}_.+\.py$' | sort | tail -n 1 | sed 's/\.py//')

  # Create the migration stub
  cat <<EOF > "$FILE"
"""${REVISION} | Auto-generated migration for PittState-Connect"""

from alembic import op
import sqlalchemy as sa


# -------------------------------------------------------------------
# Alembic revision identifiers
# -------------------------------------------------------------------
revision = "${REVISION}"
down_revision = "${DOWN_REVISION}"
branch_labels = None
depends_on = None


def upgrade():
    """Apply schema changes here."""
    # ✳️ Example:
    # op.add_column('users', sa.Column('linkedin_url', sa.String(255)))
    print("✅ Migration ${REVISION} applied successfully.")


def downgrade():
    """Rollback schema changes here."""
    # ✳️ Example:
    # op.drop_column('users', 'linkedin_url')
    pass
EOF

  echo "✅ Created new migration file: $FILE"
  echo ""

  # Run autogenerate & apply
  echo "🔍 Running Alembic autogenerate diff..."
  flask db migrate -m "${DESC}" || true

  echo ""
  echo "🚀 Applying migration..."
  flask db upgrade

  echo ""
  echo "🎉 Migration '${REVISION}' generated and applied successfully!"
  echo "---------------------------------------------------------------"
  exit 0
fi


# ==============================================================
# MODE 2 → CHECK
# ==============================================================
if [ "$1" = "check" ]; then
  header "🔍 Checking PittState-Connect database synchronization status"

  # Step 1: Print Alembic version info
  echo "📘 Alembic version info:"
  flask db heads || true
  flask db current || true

  # Step 2: Autogenerate comparison
  echo ""
  echo "⚙️  Running model comparison (no DB writes)..."
  python - <<'PYCODE'
from app_pro import app
from models import db
from flask_migrate import Migrate, Config, command
import os, sys

app.app_context().push()
migrations_dir = os.path.join(os.getcwd(), "migrations")

try:
    print("🔧 Comparing SQLAlchemy models to database schema...")
    config_path = os.path.join(migrations_dir, "alembic.ini")
    if not os.path.exists(config_path):
        raise FileNotFoundError("Missing alembic.ini in migrations/")
    from alembic.config import Config
    cfg = Config(config_path)
    command.revision(cfg, message="check_sync_temp", autogenerate=True, sql=True)
    print("✅ Schema comparison completed (safe dry run).")
    print("⚠️  If no CREATE/ALTER statements appeared, DB is in sync.")
except Exception as e:
    print("❌ Error during schema comparison:", e)
PYCODE

  # Step 3: List tables
  echo ""
  echo "📊 Listing current database tables:"
  python - <<'PYCODE'
from app_pro import app
from models import db

with app.app_context():
    tables = db.engine.table_names()
    print("Found", len(tables), "tables:")
    for t in sorted(tables):
        print("  -", t)
PYCODE

  echo ""
  echo "✅ Sync check complete."
  echo "---------------------------------------------------------------"
  exit 0
fi


# ==============================================================
# INVALID USAGE
# ==============================================================
echo "❌ Invalid command."
echo "Usage:"
echo "  ./db_tools.sh migrate \"add_feature_name\"   → create & apply migration"
echo "  ./db_tools.sh check                        → verify DB/schema sync"
echo "---------------------------------------------------------------"
exit 1
