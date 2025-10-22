"""0030_future_template | Reusable Alembic migration template for PittState-Connect

Use this as a base for all future database schema updates.
Steps for usage:
1️⃣  Copy this file and rename it (e.g., 0031_add_new_table.py)
2️⃣  Update the `revision` and `down_revision` identifiers.
3️⃣  Add your schema changes under the `upgrade()` function.
4️⃣  Optionally add rollback logic under `downgrade()`.

This keeps all migrations consistent with PittState-Connect conventions.
"""

from alembic import op
import sqlalchemy as sa


# -------------------------------------------------------------------
# Alembic revision identifiers (update when copied)
# -------------------------------------------------------------------
revision = "0030_future_template"
down_revision = "0029_sync_fixes"
branch_labels = None
depends_on = None


# -------------------------------------------------------------------
# Upgrade / Downgrade Functions
# -------------------------------------------------------------------
def upgrade():
    """Apply new schema changes here."""
    # ✳️ Example usage:
    # op.add_column('scholarships', sa.Column('ai_match_score', sa.Float(), nullable=True))
    # op.create_table(
    #     'mentorship_feedback',
    #     sa.Column('id', sa.Integer, primary_key=True),
    #     sa.Column('mentor_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE')),
    #     sa.Column('mentee_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE')),
    #     sa.Column('feedback', sa.Text),
    #     sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    # )
    print("⚙️  Migration template executed — ready for customization.")


def downgrade():
    """Rollback any schema changes made in upgrade()."""
    # ✳️ Example rollback:
    # op.drop_table('mentorship_feedback')
    # op.drop_column('scholarships', 'ai_match_score')
    pass
