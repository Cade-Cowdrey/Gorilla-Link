#!/bin/bash
# -------------------------------------------------------------
# PittState-Connect | Migration Generator Helper
# -------------------------------------------------------------
# Usage:
#   ./generate_migration.sh "add_new_table"
#
# Automatically creates a new Alembic migration file in
# migrations/versions/ using the PittState-Connect conventions:
# - Sequential numbering
# - Proper Alembic header
# - Ready-to-edit upgrade/downgrade stubs
#
# Example:
#   ./generate_migration.sh "add_scholarship_ai_score"
# -------------------------------------------------------------

set -e

MIGRATIONS_DIR="migrations/versions"
LATEST=$(ls $MIGRATIONS_DIR | grep -E '^[0-9]{4}_.+\.py$' | sort | tail -n 1 | cut -d'_' -f1)
NEXT_NUM=$(printf "%04d" $((10#$LATEST + 1)))
DESC=$1

if [ -z "$DESC" ]; then
  echo "❌ Usage: ./generate_migration.sh <description>"
  exit 1
fi

FILENAME="${MIGRATIONS_DIR}/${NEXT_NUM}_${DESC}.py"
REVISION="${NEXT_NUM}_${DESC}"
DOWN_REVISION=$(ls $MIGRATIONS_DIR | grep -E '^[0-9]{4}_.+\.py$' | sort | tail -n 1 | cut -d'_' -f1)_$(ls $MIGRATIONS_DIR | sort | tail -n 1 | cut -d'_' -f2- | sed 's/\.py//')

cat <<EOF > $FILENAME
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

echo "✅ Created new migration stub:"
echo "   → $FILENAME"
echo ""
echo "Next steps:"
echo "  1️⃣ Edit the file to define your schema changes."
echo "  2️⃣ Run: flask db upgrade"
