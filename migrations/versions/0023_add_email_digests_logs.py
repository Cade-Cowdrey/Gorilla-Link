"""Add email_digest_logs table for outbound digest send attempts."""

from alembic import op
import sqlalchemy as sa

revision = "0023_add_email_digests_logs"
down_revision = "0022_add_digests_archive"
branch_labels = None
depends_on = None


def _table_exists(conn, name: str) -> bool:
    return name in sa.inspect(conn).get_table_names()


def upgrade():
    bind = op.get_bind()
    if _table_exists(bind, "email_digest_logs"):
        return

    op.create_table(
        "email_digest_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("recipient_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("template", sa.String(100), nullable=False),  # e.g., 'weekly', 'faculty', etc.
        sa.Column("status", sa.String(50), server_default="queued"),
        sa.Column("error", sa.Text),
        sa.Column("sent_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Index("ix_email_digest_logs_recipient", "recipient_id"),
        sa.Index("ix_email_digest_logs_template", "template"),
    )


def downgrade():
    bind = op.get_bind()
    if _table_exists(bind, "email_digest_logs"):
        op.drop_table("email_digest_logs")
