"""Add likes_count and comments_count columns to posts, backfill comments_count"""

from alembic import op
import sqlalchemy as sa

# Revision identifiers, used by Alembic.
revision = "0020_add_post_engagement_columns"
down_revision = "0019_add_replies_and_badges"
branch_labels = None
depends_on = None


def upgrade():
    # Add new engagement columns
    op.add_column("posts", sa.Column("likes_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("posts", sa.Column("comments_count", sa.Integer(), nullable=False, server_default="0"))

    # Backfill comments_count from replies if replies table exists
    conn = op.get_bind()
    try:
        conn.execute(sa.text("""
            UPDATE posts
            SET comments_count = COALESCE(src.cnt, 0)
            FROM (
                SELECT post_id, COUNT(*)::int AS cnt
                FROM replies
                WHERE post_id IS NOT NULL
                GROUP BY post_id
            ) AS src
            WHERE posts.id = src.post_id;
        """))
    except Exception as e:
        print(f"⚠️ Skipped backfill due to missing replies table: {e}")

    # Remove server defaults now that columns are populated
    op.alter_column("posts", "likes_count", server_default=None)
    op.alter_column("posts", "comments_count", server_default=None)


def downgrade():
    # Drop the new columns if rolled back
    op.drop_column("posts", "comments_count")
    op.drop_column("posts", "likes_count")
