"""Legacy duplicate: ensure digests_archive exists (noop if already created)."""

from alembic import op
import sqlalchemy as sa

revision = "3a2b5f1a1e4a_add_digests_archive"
down_revision = "0023_add_email_digests_logs"
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
        sa.Column("snapshot", sa.Text, nullable=False),
        sa.Column("archived_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def downgrade():
    bind = op.get_bind()
    if _table_exists(bind, "digests_archive"):
        op.drop_table("digests_archive")
