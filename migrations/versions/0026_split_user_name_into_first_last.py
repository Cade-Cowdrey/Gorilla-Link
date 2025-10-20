"""split user name into first/last and drop legacy name


# revision identifiers, used by Alembic.
revision = '0026_split_user_name'
down_revision = '0025_seed_demo_jobs_events_connections'
branch_labels = None
depends_on = None




def _has_column(bind, table, column):
insp = reflection.Inspector.from_engine(bind)
return any(col['name'] == column for col in insp.get_columns(table))




def upgrade():
bind = op.get_bind()


# 1) Add first/last columns if missing
if not _has_column(bind, 'users', 'first_name'):
op.add_column('users', sa.Column('first_name', sa.String(length=120), nullable=False, server_default=''))
if not _has_column(bind, 'users', 'last_name'):
op.add_column('users', sa.Column('last_name', sa.String(length=120), nullable=False, server_default=''))


# 2) If a legacy `name` column exists, best-effort split → first/last, then drop it
if _has_column(bind, 'users', 'name'):
op.execute(sa.text(
"""
UPDATE users
SET first_name = CASE
WHEN name IS NULL OR name = '' THEN first_name
WHEN position(' ' in name) = 0 THEN name
ELSE split_part(name, ' ', 1)
END,
last_name = CASE
WHEN name IS NULL OR name = '' THEN last_name
WHEN position(' ' in name) = 0 THEN last_name
ELSE trim(substring(name from position(' ' in name)+1))
END
"""
))
with op.batch_alter_table('users') as batch:
batch.drop_column('name')


# 3) Remove server defaults
with op.batch_alter_table('users') as batch:
batch.alter_column('first_name', server_default=None)
batch.alter_column('last_name', server_default=None)




def downgrade():
bind = op.get_bind()


# Recreate legacy `name` for downgrade path
if not _has_column(bind, 'users', 'name'):
op.add_column('users', sa.Column('name', sa.String(length=255), nullable=True))
op.execute(sa.text(
"""
UPDATE users
SET name = trim(coalesce(first_name,'') || ' ' || coalesce(last_name,''))
"""
))


with op.batch_alter_table('users') as batch:
if _has_column(bind, 'users', 'first_name'):
batch.drop_column('first_name')
if _has_column(bind, 'users', 'last_name'):
batch.drop_column('last_name')
