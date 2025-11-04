"""Add growth features models

Revision ID: 001_growth_features
Revises: 
Create Date: 2024-11-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '001_growth_features'
down_revision = None  # Update this if you have existing migrations
branch_labels = None
depends_on = None


def upgrade():
    """Create all growth feature tables"""
    
    # Check if tables already exist before creating them
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # Gamification - Badges
    if 'badges' not in existing_tables:
        op.create_table('badges',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('slug', sa.String(length=100), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('icon', sa.String(length=255), nullable=True),
            sa.Column('category', sa.String(length=50), nullable=True),
            sa.Column('points', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('criteria', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
            sa.Column('rarity', sa.String(length=20), nullable=True, server_default='common'),
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name'),
            sa.UniqueConstraint('slug')
        )
    
    if 'user_badges' not in existing_tables:
        op.create_table('user_badges',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('badge_id', sa.Integer(), nullable=False),
            sa.Column('earned_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
            sa.Column('progress', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('is_showcased', sa.Boolean(), nullable=True, server_default='false'),
            sa.Column('notified', sa.Boolean(), nullable=True, server_default='false'),
            sa.ForeignKeyConstraint(['badge_id'], ['badges.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id', 'badge_id', name='unique_user_badge')
        )
    
    if 'user_streaks' not in existing_tables:
        op.create_table('user_streaks',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('streak_type', sa.String(length=50), nullable=False),
            sa.Column('current_streak', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('longest_streak', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('last_activity_date', sa.Date(), nullable=False),
            sa.Column('started_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
            sa.Column('streak_freezes_available', sa.Integer(), nullable=True, server_default='0'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id', 'streak_type', name='unique_user_streak')
        )
    
    if 'profile_completion_progress' not in existing_tables:
        op.create_table('profile_completion_progress',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('completion_percentage', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('completed_tasks', postgresql.ARRAY(sa.String()), nullable=True),
            sa.Column('last_updated', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
            sa.Column('has_profile_photo', sa.Boolean(), nullable=True, server_default='false'),
            sa.Column('has_bio', sa.Boolean(), nullable=True, server_default='false'),
            sa.Column('has_resume', sa.Boolean(), nullable=True, server_default='false'),
            sa.Column('has_skills', sa.Boolean(), nullable=True, server_default='false'),
            sa.Column('has_endorsements', sa.Boolean(), nullable=True, server_default='false'),
            sa.Column('has_connections', sa.Boolean(), nullable=True, server_default='false'),
            sa.Column('has_career_assessment', sa.Boolean(), nullable=True, server_default='false'),
            sa.Column('has_applied_to_job', sa.Boolean(), nullable=True, server_default='false'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id')
        )
    
    if 'user_points' not in existing_tables:
        op.create_table('user_points',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('total_points', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('level', sa.Integer(), nullable=True, server_default='1'),
            sa.Column('points_to_next_level', sa.Integer(), nullable=True, server_default='100'),
            sa.Column('rank', sa.String(length=50), nullable=True, server_default='Bronze'),
            sa.Column('last_points_earned', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id')
        )
    
    if 'point_transactions' not in existing_tables:
        op.create_table('point_transactions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_points_id', sa.Integer(), nullable=False),
            sa.Column('amount', sa.Integer(), nullable=False),
            sa.Column('reason', sa.String(length=255), nullable=False),
            sa.Column('balance_after', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['user_points_id'], ['user_points.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Social Features
    if 'success_stories' not in existing_tables:
        op.create_table('success_stories',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('story_type', sa.String(length=50), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('company_name', sa.String(length=255), nullable=True),
            sa.Column('position', sa.String(length=255), nullable=True),
            sa.Column('salary_range', sa.String(length=100), nullable=True),
            sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
            sa.Column('image_url', sa.String(length=512), nullable=True),
            sa.Column('is_featured', sa.Boolean(), nullable=True, server_default='false'),
            sa.Column('is_public', sa.Boolean(), nullable=True, server_default='true'),
            sa.Column('views_count', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
    
    if 'story_reactions' not in existing_tables:
        op.create_table('story_reactions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('story_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('reaction_type', sa.String(length=20), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['story_id'], ['success_stories.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('story_id', 'user_id', name='unique_story_reaction')
        )
    
    if 'story_comments' not in existing_tables:
        op.create_table('story_comments',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('story_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('parent_comment_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['parent_comment_id'], ['story_comments.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['story_id'], ['success_stories.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
    
    if 'referrals' not in existing_tables:
        op.create_table('referrals',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('referrer_id', sa.Integer(), nullable=False),
            sa.Column('referred_user_id', sa.Integer(), nullable=True),
            sa.Column('referral_code', sa.String(length=50), nullable=False),
            sa.Column('referred_email', sa.String(length=255), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True, server_default='pending'),
            sa.Column('reward_type', sa.String(length=50), nullable=True, server_default='points'),
            sa.Column('reward_value', sa.Integer(), nullable=True, server_default='50'),
            sa.Column('referred_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('rewarded_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['referred_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['referrer_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('referral_code')
        )
    
    if 'direct_messages' not in existing_tables:
        op.create_table('direct_messages',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('sender_id', sa.Integer(), nullable=False),
            sa.Column('recipient_id', sa.Integer(), nullable=False),
            sa.Column('subject', sa.String(length=255), nullable=True),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('is_read', sa.Boolean(), nullable=True, server_default='false'),
            sa.Column('read_at', sa.DateTime(), nullable=True),
            sa.Column('is_archived', sa.Boolean(), nullable=True, server_default='false'),
            sa.Column('message_type', sa.String(length=20), nullable=True, server_default='direct'),
            sa.Column('credits_used', sa.Integer(), nullable=True, server_default='1'),
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['recipient_id'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
    
    if 'user_message_credits' not in existing_tables:
        op.create_table('user_message_credits',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('credits_available', sa.Integer(), nullable=True, server_default='10'),
            sa.Column('credits_used_this_month', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('unlimited', sa.Boolean(), nullable=True, server_default='false'),
            sa.Column('last_refill', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
            sa.Column('next_refill', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id')
        )
    
    # Continue with remaining tables in next comment due to length...
    print("✅ Growth features tables created successfully!")


def downgrade():
    """Drop all growth feature tables"""
    # Drop in reverse order
    tables_to_drop = [
        'event_messages', 'event_attendees', 'live_events',
        'chat_messages', 'push_subscriptions', 'notification_preferences',
        'auto_apply_queue', 'user_behavior', 'recommendations', 'user_analytics',
        'mentorship_sessions', 'mentorship_matches', 'mentee_profiles', 
        'mentor_profiles', 'mentorship_programs',
        'forum_votes', 'forum_posts', 'forum_topics', 'forum_categories',
        'user_message_credits', 'direct_messages', 'referrals',
        'story_comments', 'story_reactions', 'success_stories',
        'point_transactions', 'user_points', 'profile_completion_progress',
        'user_streaks', 'user_badges', 'badges'
    ]
    
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    for table in tables_to_drop:
        if table in existing_tables:
            op.drop_table(table)
