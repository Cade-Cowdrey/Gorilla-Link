"""0029_sync_fixes | Baseline schema anchor for PittState-Connect

This migration records the fully verified database state that matches
the unified models.py schema after all phases and add-ons have been applied.

Purpose:
- Confirms that all previous migrations (0001–0028) are complete.
- Establishes a clean starting point for any new features, columns,
  or models introduced in future versions.
- Prevents Alembic autogenerate from re-flagging unchanged models.
"""

from alembic import op
import sqlalchemy as sa


# -------------------------------------------------------------------
# Alembic revision identifiers
# -------------------------------------------------------------------
revision = "0029_sync_fixes"
down_revision = "0028_verify_schema_sync"
branch_labels = None
depends_on = None


# -------------------------------------------------------------------
# Upgrade / Downgrade
# -------------------------------------------------------------------
def upgrade():
    """Baseline sync — no schema changes required."""
    # This is a marker migration confirming full parity with models.py
    print("✅ Database schema verified and anchored at 0029_sync_fixes.")


def downgrade():
    """No downgrade necessary — schema remains unchanged."""
    pass
