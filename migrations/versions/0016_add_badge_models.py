"""Ensure badge tables exist (noop if already created)."""

from alembic import op
import sqlalchemy as sa

revision = "0016_add_badge_models"
down_revision = "0015_rename_metadata_to_meta_info"
branch_labels = None
depends_on = None


def _table_exists(conn, name: str) -> bool:
    return name in sa.inspect(conn).get_table_names()


def upgrade():
    bind = op.get_bind()

    if not _table_exists(bind, "badges"):
        op.create_table(
            "badges",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("slug", sa.String(120), unique=True),
            sa.Column("description", sa.Text),
            sa.Column("icon", sa.String(255)),
            sa.Column("category", sa.String(100), server_default="achievement"),
            sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        )

    if not _table_exists(bind, "user_badges"):
        op.create_table(
            "user_badges",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE")),
            sa.Column("badge_id", sa.Integer, sa.ForeignKey("badges.id", ondelete="CASCADE")),
            sa.Column("awarded_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),
        )


def downgrade():
    bind = op.get_bind()
    if _table_exists(bind, "user_badges"):
        op.drop_table("user_badges")
    if _table_exists(bind, "badges"):
        op.drop_table("badges")
