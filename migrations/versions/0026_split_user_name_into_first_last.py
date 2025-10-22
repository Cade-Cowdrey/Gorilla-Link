"""Split user.name into first_name and last_name

This migration updates the users table to deprecate the single `name` column
and replace it with separate `first_name` and `last_name` columns.
It is part of the PittState-Connect schema normalization update.
"""

from alembic import op
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = "0026_split_user_name_into_first_last"
down_revision = "0025_seed_demo_jobs_events_connections"
branch_labels = None
depends_on = None


def upgrade():
    """Perform schema upgrade to split user full name into first and last fields."""
    with op.batch_alter_table("users", schema=None) as batch_op:
        # Add new columns
        batch_op.add_column(sa.Column("first_name", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("last_name", sa.String(length=80), nullable=True))

        # Optional: migrate data if the old 'name' field exists
        connection = op.get_bind()
        inspector = sa.inspect(connection)
        columns = [col["name"] for col in inspector.get_columns("users")]

        if "name" in columns:
            connection.execute(sa.text("""
                UPDATE users
                SET first_name = SPLIT_PART(name, ' ', 1),
                    last_name = CASE
                        WHEN POSITION(' ' IN name) > 0 THEN SUBSTRING(name FROM POSITION(' ' IN name) + 1)
                        ELSE ''
                    END
            """))

            # Drop the old 'name' column
            batch_op.drop_column("name")

    print("✅ Split user.name -> first_name, last_name completed successfully.")


def downgrade():
    """Revert schema back to single user.name column."""
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("name", sa.String(length=160), nullable=True))
        batch_op.drop_column("first_name")
        batch_op.drop_column("last_name")

    print("⏪ Reverted to single user.name column.")
