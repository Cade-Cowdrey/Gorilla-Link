"""Add engagement columns to posts: views_count, shares_count, saves_count, last_interacted_at."""

from alembic import op
import sqlalchemy as sa

revision = "0020_add_post_engagement_columns"
down_revision = "0019_add_replies_and_badges"
branch_labels = None
depends_on = None


def _has_column(conn, table: str, column: str) -> bool:
    insp = sa.inspect(conn)
    cols = [c["name"] for c in insp.get_columns(table)] if table in insp.get_table_names() else []
    return column in cols


def upgrade():
    bind = op.get_bind()
    if "posts" not in sa.inspect(bind).get_table_names():
        return

    if not _has_column(bind, "posts", "views_count"):
        op.add_column("posts", sa.Column("views_count", sa.Integer, server_default="0", nullable=False))
    if not _has_column(bind, "posts", "shares_count"):
        op.add_column("posts", sa.Column("shares_count", sa.Integer, server_default="0", nullable=False))
    if not _has_column(bind, "posts", "saves_count"):
        op.add_column("posts", sa.Column("saves_count", sa.Integer, server_default="0", nullable=False))
    if not _has_column(bind, "posts", "last_interacted_at"):
        op.add_column("posts", sa.Column("last_interacted_at", sa.DateTime))


def downgrade():
    bind = op.get_bind()
    if "posts" not in sa.inspect(bind).get_table_names():
        return

    for col in ["last_interacted_at", "saves_count", "shares_count", "views_count"]:
        if _has_column(bind, "posts", col):
            op.drop_column("posts", col)
