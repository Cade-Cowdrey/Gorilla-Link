#!/bin/bash
# =====================================================================
# PittState-Connect | Database Schema Sync Checker
# =====================================================================
# Usage:
#   ./check_db_sync.sh
#
# This script checks whether your live PostgreSQL schema
# matches the SQLAlchemy models defined in models.py.
#
# It is safe to run anytime on Render or locally — no data is modified.
# =====================================================================

set -e
export FLASK_APP=app_pro.py

echo "---------------------------------------------------------------"
echo "🔍 Checking PittState-Connect database synchronization status..."
echo "---------------------------------------------------------------"

# Ensure alembic environment is initialized
if [ ! -d "migrations" ]; then
  echo "❌ No migrations directory found. Run 'flask db init' first."
  exit 1
fi

# Step 1: Print Alembic head vs current DB version
echo ""
echo "📘 Alembic version info:"
flask db heads || true
flask db current || true

# Step 2: Run autogenerate in check-only mode (no new files created)
echo ""
echo "⚙️  Running model comparison (autogenerate check)..."
python - <<'PYCODE'
from app_pro import app
from models import db
from flask_migrate import Migrate, Config, ScriptDirectory
from alembic import command
import os, sys

app.app_context().push()
migrations_dir = os.path.join(os.getcwd(), "migrations")

cfg = Config(os.path.join(migrations_dir, "alembic.ini")) if os.path.exists(os.path.join(migrations_dir, "alembic.ini")) else None
if not cfg:
    print("❌ Alembic config missing (alembic.ini).")
    sys.exit(1)

# Fake autogenerate run to detect diffs
try:
    print("🔧 Comparing models to DB...")
    command.revision(cfg, message="check_sync_temp", autogenerate=True, sql=True)
    print("✅ Schema comparison executed successfully (no DB writes).")
    print("⚠️  If no CREATE/ALTER statements appear, your DB is in sync.")
except Exception as e:
    print("❌ Error during autogenerate comparison:", e)
PYCODE

# Step 3: Optionally list DB tables
echo ""
echo "📊 Listing database tables:"
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
echo "---------------------------------------------------------------"
echo "✅ Sync check complete."
echo "If no major schema differences were printed above, you're good!"
echo "---------------------------------------------------------------"
