"""Create digests_archive table (safe if already exists)."""

from alembic import op
import sqlalchemy as sa

revision = "0022_add_digests_archive"
down_revision = "0021_add_likes_model"
branch_labels = None
depends_on = None


def _table_exists(conn, name: str) -> bool:
    return name in sa.inspect(conn).get_table_names()


def upgrade():
    bind = op.get_bind()
    if _table_exists(bind, "digests_archive"):
        return

    op.create_table(
        "digests_archive",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("digest_id", sa.Integer, sa.ForeignKey("digests.id", ondelete="CASCADE")),
        sa.Column("snapshot", sa.Text, nullable=False),  # JSON text snapshot
        sa.Column("archived_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Index("ix_digests_archive_digest_id", "digest_id"),
    )


def downgrade():
    bind = op.get_bind()
    if _table_exists(bind, "digests_archive"):
        op.drop_table("digests_archive")
