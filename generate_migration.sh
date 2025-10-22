#!/bin/bash
# =====================================================================
# PittState-Connect | One-Step Migration Generator & Sync Script
# =====================================================================
# Usage:
#   ./generate_migration.sh "add_feature_name"
#
# This automates your full Alembic workflow:
#   1️⃣  Auto-increments the version number.
#   2️⃣  Creates a new migration stub using PittState-Connect conventions.
#   3️⃣  Runs Flask-Migrate's autogenerate check.
#   4️⃣  Applies the migration immediately to keep database in sync.
#
# Example:
#   ./generate_migration.sh "add_financial_literacy_models"
#
# =====================================================================

set -e
export FLASK_APP=app_pro.py

MIGRATIONS_DIR="migrations/versions"
DESC=$1

if [ -z "$DESC" ]; then
  echo "❌ Usage: ./generate_migration.sh <description>"
  exit 1
fi

# Determine latest version and increment
LATEST=$(ls $MIGRATIONS_DIR | grep -E '^[0-9]{4}_.+\.py$' | sort | tail -n 1 | cut -d'_' -f1)
NEXT_NUM=$(printf "%04d" $((10#$LATEST + 1)))
REVISION="${NEXT_NUM}_${DESC}"
FILE="${MIGRATIONS_DIR}/${REVISION}.py"

# Identify previous migration for down_revision
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

echo ""
echo "---------------------------------------------------------------"
echo "✅ Created new migration file:"
echo "   → $FILE"
echo "---------------------------------------------------------------"
echo ""

# Step 1: Run autogenerate to check model diffs
echo "🔍 Running Alembic autogenerate check..."
flask db migrate -m "${DESC}" || true

# Step 2: Apply the new migration to database
echo "⚙️  Applying migration..."
flask db upgrade

echo ""
echo "🎉 Migration '${REVISION}' generated and applied successfully!"
echo "📁 File saved at: ${FILE}"
echo "---------------------------------------------------------------"
