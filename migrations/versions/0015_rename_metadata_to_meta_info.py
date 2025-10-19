"""Rename legacy `metadata` table to `meta_info` (safe if already renamed)."""

from alembic import op
import sqlalchemy as sa

# Revision identifiers, used by Alembic.
revision = "0015_rename_metadata_to_meta_info"
down_revision = "0014_add_missing_models"
branch_labels = None
depends_on = None


def _table_exists(conn, name: str) -> bool:
    insp = sa.inspect(conn)
    return name in insp.get_table_names()


def upgrade():
    bind = op.get_bind()

    if _table_exists(bind, "meta_info"):
        # Already at the desired name — nothing to do.
        return

    if _table_exists(bind, "metadata"):
        # Simple rename if legacy table exists.
        op.rename_table("metadata", "meta_info")
        return

    # Neither exists: create an empty meta_info to be safe.
    op.create_table(
        "meta_info",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("key", sa.String(100), nullable=False, unique=True),
        sa.Column("value", sa.String(500)),
        sa.Column(
            "last_updated",
            sa.DateTime,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            onupdate=sa.text("CURRENT_TIMESTAMP"),
        ),
    )


def downgrade():
    bind = op.get_bind()
    if _table_exists(bind, "meta_info") and not _table_exists(bind, "metadata"):
        op.rename_table("meta_info", "metadata")
