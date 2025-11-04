"""
PSU Connect - Growth Features Database Models
Models for gamification, social features, and engagement systems
"""

from extensions import db
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSON, JSONB, ARRAY
import datetime


# =======================
# GAMIFICATION MODELS
# =======================

class Badge(db.Model):
    """Achievement badges that users can earn"""
    __tablename__ = "badges"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(255))  # Font Awesome icon class or image URL
    category = db.Column(db.String(50))  # resume, networking, learning, career, etc.
    points = db.Column(db.Integer, default=0)  # Points awarded for earning this badge
    criteria = db.Column(JSONB)  # JSON describing how to earn this badge
    is_active = db.Column(db.Boolean, default=True)
    rarity = db.Column(db.String(20), default='common')  # common, uncommon, rare, epic, legendary
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    user_badges = db.relationship('UserBadge', back_populates='badge', lazy=True)
    
    def __repr__(self):
        return f"<Badge {self.name}>"


class UserBadge(db.Model):
    """Tracks which badges users have earned"""
    __tablename__ = "user_badges"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badges.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=func.now())
    progress = db.Column(db.Integer, default=0)  # For badges with progress tracking
    is_showcased = db.Column(db.Boolean, default=False)  # Display on profile
    notified = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('earned_badges', lazy='dynamic'))
    badge = db.relationship('Badge', back_populates='user_badges')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'badge_id', name='unique_user_badge'),
    )
    
    def __repr__(self):
        return f"<UserBadge user={self.user_id} badge={self.badge_id}>"


class UserStreak(db.Model):
    """Tracks user daily/weekly streaks for engagement"""
    __tablename__ = "user_streaks"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    streak_type = db.Column(db.String(50), nullable=False)  # login, job_apply, learning, etc.
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_activity_date = db.Column(db.Date, nullable=False)
    started_at = db.Column(db.DateTime, default=func.now())
    streak_freezes_available = db.Column(db.Integer, default=2)  # Allow 2 missed days
    
    # Relationships
    user = db.relationship('User', backref=db.backref('streaks', lazy='dynamic'))
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'streak_type', name='unique_user_streak'),
    )
    
    def __repr__(self):
        return f"<UserStreak user={self.user_id} type={self.streak_type} streak={self.current_streak}>"


class ProfileCompletionProgress(db.Model):
    """Tracks user profile completion percentage and tasks"""
    __tablename__ = "profile_completion_progress"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    completion_percentage = db.Column(db.Integer, default=0)
    completed_tasks = db.Column(ARRAY(db.String))  # List of completed task slugs
    last_updated = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    
    # Individual task completion flags
    has_profile_photo = db.Column(db.Boolean, default=False)
    has_bio = db.Column(db.Boolean, default=False)
    has_resume = db.Column(db.Boolean, default=False)
    has_skills = db.Column(db.Boolean, default=False)  # At least 3 skills
    has_endorsements = db.Column(db.Boolean, default=False)  # At least 2
    has_connections = db.Column(db.Boolean, default=False)  # At least 5
    has_career_assessment = db.Column(db.Boolean, default=False)
    has_applied_to_job = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('profile_progress', uselist=False))
    
    def calculate_percentage(self):
        """Calculate completion percentage based on completed tasks"""
        total_tasks = 8
        completed = sum([
            self.has_profile_photo,
            self.has_bio,
            self.has_resume,
            self.has_skills,
            self.has_endorsements,
            self.has_connections,
            self.has_career_assessment,
            self.has_applied_to_job
        ])
        self.completion_percentage = int((completed / total_tasks) * 100)
        return self.completion_percentage
    
    def __repr__(self):
        return f"<ProfileProgress user={self.user_id} completion={self.completion_percentage}%>"


class UserPoints(db.Model):
    """Tracks user points/reputation for gamification"""
    __tablename__ = "user_points"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    total_points = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    points_to_next_level = db.Column(db.Integer, default=100)
    rank = db.Column(db.String(50), default='Novice')  # Novice, Intermediate, Advanced, Expert, Master
    last_points_earned = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('points', uselist=False))
    transactions = db.relationship('PointTransaction', back_populates='user_points', lazy='dynamic')
    
    def add_points(self, amount, reason):
        """Add points and check for level up"""
        self.total_points += amount
        self.last_points_earned = datetime.datetime.utcnow()
        
        # Check for level up
        while self.total_points >= self.points_to_next_level:
            self.level += 1
            self.points_to_next_level = self.level * 100  # 100, 200, 300, etc.
            
            # Update rank based on level
            if self.level >= 50:
                self.rank = 'Master'
            elif self.level >= 30:
                self.rank = 'Expert'
            elif self.level >= 15:
                self.rank = 'Advanced'
            elif self.level >= 5:
                self.rank = 'Intermediate'
        
        # Log transaction
        transaction = PointTransaction(
            user_points_id=self.id,
            amount=amount,
            reason=reason,
            balance_after=self.total_points
        )
        db.session.add(transaction)
    
    def __repr__(self):
        return f"<UserPoints user={self.user_id} points={self.total_points} level={self.level}>"


class PointTransaction(db.Model):
    """Log of all point transactions"""
    __tablename__ = "point_transactions"
    
    id = db.Column(db.Integer, primary_key=True)
    user_points_id = db.Column(db.Integer, db.ForeignKey('user_points.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)  # Can be negative for spending points
    reason = db.Column(db.String(255), nullable=False)
    balance_after = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    user_points = db.relationship('UserPoints', back_populates='transactions')
    
    def __repr__(self):
        return f"<PointTransaction {self.amount} points - {self.reason}>"


# =======================
# SOCIAL FEATURES
# =======================

class SuccessStory(db.Model):
    """User success stories and achievements to share with community"""
    __tablename__ = "success_stories"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    story_type = db.Column(db.String(50), nullable=False)  # job_offer, promotion, graduation, internship, etc.
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    company_name = db.Column(db.String(255))
    position = db.Column(db.String(255))
    salary_range = db.Column(db.String(100))  # Optional, e.g., "$60K-$80K"
    tags = db.Column(ARRAY(db.String))
    image_url = db.Column(db.String(512))
    is_featured = db.Column(db.Boolean, default=False)
    is_public = db.Column(db.Boolean, default=True)
    views_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = db.relationship('User', backref=db.backref('success_stories', lazy='dynamic'))
    reactions = db.relationship('StoryReaction', back_populates='story', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('StoryComment', back_populates='story', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<SuccessStory {self.title}>"


class StoryReaction(db.Model):
    """Reactions to success stories (like, celebrate, insightful, etc.)"""
    __tablename__ = "story_reactions"
    
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('success_stories.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reaction_type = db.Column(db.String(20), nullable=False)  # like, celebrate, insightful, love, support
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    story = db.relationship('SuccessStory', back_populates='reactions')
    user = db.relationship('User', backref=db.backref('story_reactions', lazy='dynamic'))
    
    __table_args__ = (
        db.UniqueConstraint('story_id', 'user_id', name='unique_story_reaction'),
    )
    
    def __repr__(self):
        return f"<StoryReaction story={self.story_id} user={self.user_id} type={self.reaction_type}>"


class StoryComment(db.Model):
    """Comments on success stories"""
    __tablename__ = "story_comments"
    
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('success_stories.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('story_comments.id'))  # For nested replies
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    story = db.relationship('SuccessStory', back_populates='comments')
    user = db.relationship('User', backref=db.backref('story_comments', lazy='dynamic'))
    replies = db.relationship('StoryComment', backref=db.backref('parent_comment', remote_side=[id]), lazy='dynamic')
    
    def __repr__(self):
        return f"<StoryComment story={self.story_id} user={self.user_id}>"


class Referral(db.Model):
    """Referral program tracking"""
    __tablename__ = "referrals"
    
    id = db.Column(db.Integer, primary_key=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    referred_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    referral_code = db.Column(db.String(50), unique=True, nullable=False)
    referred_email = db.Column(db.String(255))  # Email of person referred (before signup)
    status = db.Column(db.String(20), default='pending')  # pending, completed, rewarded
    reward_type = db.Column(db.String(50))  # premium_month, points, feature_unlock
    reward_value = db.Column(db.Integer)
    referred_at = db.Column(db.DateTime, default=func.now())
    completed_at = db.Column(db.DateTime)  # When referred user completes signup
    rewarded_at = db.Column(db.DateTime)  # When referrer receives reward
    
    # Relationships
    referrer = db.relationship('User', foreign_keys=[referrer_id], backref=db.backref('referrals_made', lazy='dynamic'))
    referred_user = db.relationship('User', foreign_keys=[referred_user_id], backref=db.backref('referred_by', uselist=False))
    
    def __repr__(self):
        return f"<Referral code={self.referral_code} status={self.status}>"


class DirectMessage(db.Model):
    """Direct messaging system (InMail-style)"""
    __tablename__ = "direct_messages"
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(255))
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    is_archived = db.Column(db.Boolean, default=False)
    message_type = db.Column(db.String(20), default='regular')  # regular, inmail (uses credit)
    credits_used = db.Column(db.Integer, default=0)  # InMail credits consumed
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref=db.backref('messages_sent', lazy='dynamic'))
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref=db.backref('messages_received', lazy='dynamic'))
    
    def __repr__(self):
        return f"<DirectMessage from={self.sender_id} to={self.recipient_id}>"


class UserMessageCredits(db.Model):
    """Tracks InMail-style messaging credits"""
    __tablename__ = "user_message_credits"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    credits_available = db.Column(db.Integer, default=5)  # Free tier: 5/month
    credits_used_this_month = db.Column(db.Integer, default=0)
    unlimited = db.Column(db.Boolean, default=False)  # Premium users get unlimited
    last_refill = db.Column(db.DateTime, default=func.now())
    next_refill = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('message_credits', uselist=False))
    
    def refill_credits(self):
        """Refill monthly credits"""
        if not self.unlimited:
            self.credits_available = 5
            self.credits_used_this_month = 0
            self.last_refill = datetime.datetime.utcnow()
            self.next_refill = self.last_refill + datetime.timedelta(days=30)
    
    def use_credit(self):
        """Use one message credit"""
        if self.unlimited:
            return True
        if self.credits_available > 0:
            self.credits_available -= 1
            self.credits_used_this_month += 1
            return True
        return False
    
    def __repr__(self):
        return f"<MessageCredits user={self.user_id} available={self.credits_available}>"


# =======================
# DISCUSSION FORUMS
# =======================

class ForumCategory(db.Model):
    """Forum categories (Career Advice, Technical Help, etc.)"""
    __tablename__ = "forum_categories"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))  # Font Awesome icon
    color = db.Column(db.String(20))  # Hex color for category badge
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    topics = db.relationship('ForumTopic', back_populates='category', lazy='dynamic')
    
    def __repr__(self):
        return f"<ForumCategory {self.name}>"


class ForumTopic(db.Model):
    """Forum discussion topics"""
    __tablename__ = "forum_topics"
    
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('forum_categories.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tags = db.Column(ARRAY(db.String))
    views_count = db.Column(db.Integer, default=0)
    is_pinned = db.Column(db.Boolean, default=False)
    is_locked = db.Column(db.Boolean, default=False)
    is_solved = db.Column(db.Boolean, default=False)
    best_answer_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'))
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    last_activity_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    category = db.relationship('ForumCategory', back_populates='topics')
    user = db.relationship('User', backref=db.backref('forum_topics', lazy='dynamic'))
    posts = db.relationship('ForumPost', back_populates='topic', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<ForumTopic {self.title}>"


class ForumPost(db.Model):
    """Replies to forum topics"""
    __tablename__ = "forum_posts"
    
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('forum_topics.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    parent_post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'))  # For nested replies
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
    is_best_answer = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    topic = db.relationship('ForumTopic', back_populates='posts')
    user = db.relationship('User', backref=db.backref('forum_posts', lazy='dynamic'))
    replies = db.relationship('ForumPost', backref=db.backref('parent_post', remote_side=[id]), lazy='dynamic')
    votes = db.relationship('ForumVote', back_populates='post', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<ForumPost topic={self.topic_id} user={self.user_id}>"


class ForumVote(db.Model):
    """Upvotes/downvotes on forum posts"""
    __tablename__ = "forum_votes"
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vote_type = db.Column(db.String(10), nullable=False)  # upvote, downvote
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    post = db.relationship('ForumPost', back_populates='votes')
    user = db.relationship('User', backref=db.backref('forum_votes', lazy='dynamic'))
    
    __table_args__ = (
        db.UniqueConstraint('post_id', 'user_id', name='unique_forum_vote'),
    )
    
    def __repr__(self):
        return f"<ForumVote post={self.post_id} user={self.user_id} type={self.vote_type}>"


# =======================
# MENTORSHIP
# =======================

class MentorshipProgram(db.Model):
    """Structured mentorship programs"""
    __tablename__ = "mentorship_programs"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    duration_weeks = db.Column(db.Integer, default=8)
    max_mentees = db.Column(db.Integer, default=3)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    matches = db.relationship('MentorshipMatch', back_populates='program', lazy='dynamic')
    
    def __repr__(self):
        return f"<MentorshipProgram {self.name}>"


class MentorProfile(db.Model):
    """Mentor-specific profile information"""
    __tablename__ = "mentor_profiles"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    expertise_areas = db.Column(ARRAY(db.String))
    industries = db.Column(ARRAY(db.String))
    current_company = db.Column(db.String(255))
    current_position = db.Column(db.String(255))
    years_experience = db.Column(db.Integer)
    max_mentees = db.Column(db.Integer, default=3)
    current_mentees_count = db.Column(db.Integer, default=0)
    is_accepting_mentees = db.Column(db.Boolean, default=True)
    availability = db.Column(db.String(255))  # e.g., "Weekends, 2 hours/week"
    bio = db.Column(db.Text)
    rating = db.Column(db.Float, default=0.0)
    total_ratings = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    user = db.relationship('User', backref=db.backref('mentor_profile', uselist=False))
    matches_as_mentor = db.relationship('MentorshipMatch', foreign_keys='MentorshipMatch.mentor_id', back_populates='mentor', lazy='dynamic')
    
    def __repr__(self):
        return f"<MentorProfile user={self.user_id}>"


class MenteeProfile(db.Model):
    """Mentee-specific profile and goals"""
    __tablename__ = "mentee_profiles"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    career_goals = db.Column(db.Text)
    interests = db.Column(ARRAY(db.String))
    target_industries = db.Column(ARRAY(db.String))
    preferred_mentor_traits = db.Column(ARRAY(db.String))
    availability = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    user = db.relationship('User', backref=db.backref('mentee_profile', uselist=False))
    matches_as_mentee = db.relationship('MentorshipMatch', foreign_keys='MentorshipMatch.mentee_id', back_populates='mentee', lazy='dynamic')
    
    def __repr__(self):
        return f"<MenteeProfile user={self.user_id}>"


class MentorshipMatch(db.Model):
    """Active mentorship relationships"""
    __tablename__ = "mentorship_matches"
    
    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey('mentorship_programs.id'))
    mentor_id = db.Column(db.Integer, db.ForeignKey('mentor_profiles.id'), nullable=False)
    mentee_id = db.Column(db.Integer, db.ForeignKey('mentee_profiles.id'), nullable=False)
    status = db.Column(db.String(20), default='active')  # active, completed, cancelled
    match_score = db.Column(db.Float)  # AI compatibility score
    started_at = db.Column(db.DateTime, default=func.now())
    scheduled_end_at = db.Column(db.DateTime)
    ended_at = db.Column(db.DateTime)
    meetings_completed = db.Column(db.Integer, default=0)
    goals_achieved = db.Column(JSONB)
    mentor_rating = db.Column(db.Integer)  # 1-5 stars
    mentee_rating = db.Column(db.Integer)  # 1-5 stars
    feedback = db.Column(db.Text)
    
    # Relationships
    program = db.relationship('MentorshipProgram', back_populates='matches')
    mentor = db.relationship('MentorProfile', foreign_keys=[mentor_id], back_populates='matches_as_mentor')
    mentee = db.relationship('MenteeProfile', foreign_keys=[mentee_id], back_populates='matches_as_mentee')
    sessions = db.relationship('MentorshipSession', back_populates='match', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<MentorshipMatch mentor={self.mentor_id} mentee={self.mentee_id}>"


class MentorshipSession(db.Model):
    """Individual mentorship meetings"""
    __tablename__ = "mentorship_sessions"
    
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('mentorship_matches.id'), nullable=False)
    scheduled_at = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled
    meeting_link = db.Column(db.String(512))  # Zoom/Google Meet link
    agenda = db.Column(db.Text)
    notes = db.Column(db.Text)
    action_items = db.Column(JSONB)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    match = db.relationship('MentorshipMatch', back_populates='sessions')
    
    def __repr__(self):
        return f"<MentorshipSession match={self.match_id} at={self.scheduled_at}>"


# =======================
# ANALYTICS & RECOMMENDATIONS
# =======================

class UserAnalytics(db.Model):
    """Aggregated user analytics and metrics"""
    __tablename__ = "user_analytics"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Profile metrics
    profile_views_total = db.Column(db.Integer, default=0)
    profile_views_this_week = db.Column(db.Integer, default=0)
    profile_views_this_month = db.Column(db.Integer, default=0)
    
    # Resume metrics
    resume_downloads = db.Column(db.Integer, default=0)
    resume_shares = db.Column(db.Integer, default=0)
    
    # Job application metrics
    applications_sent = db.Column(db.Integer, default=0)
    applications_viewed = db.Column(db.Integer, default=0)
    applications_response_rate = db.Column(db.Float, default=0.0)
    interviews_scheduled = db.Column(db.Integer, default=0)
    offers_received = db.Column(db.Integer, default=0)
    
    # Engagement metrics
    connections_count = db.Column(db.Integer, default=0)
    messages_sent = db.Column(db.Integer, default=0)
    forum_posts_count = db.Column(db.Integer, default=0)
    success_stories_count = db.Column(db.Integer, default=0)
    
    # Learning metrics
    courses_enrolled = db.Column(db.Integer, default=0)
    courses_completed = db.Column(db.Integer, default=0)
    total_learning_hours = db.Column(db.Float, default=0.0)
    
    # Rankings
    percentile_rank = db.Column(db.Float)  # Top X% of users
    
    last_updated = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = db.relationship('User', backref=db.backref('analytics', uselist=False))
    
    def __repr__(self):
        return f"<UserAnalytics user={self.user_id}>"


class Recommendation(db.Model):
    """AI-generated recommendations for users"""
    __tablename__ = "recommendations"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recommendation_type = db.Column(db.String(50), nullable=False)  # job, alumni, course, event, mentor
    item_id = db.Column(db.Integer, nullable=False)  # ID of recommended item
    item_type = db.Column(db.String(50), nullable=False)  # job_posting, user, learning_resource, etc.
    score = db.Column(db.Float, nullable=False)  # Recommendation confidence score (0-1)
    reasoning = db.Column(db.Text)  # Why this was recommended
    is_viewed = db.Column(db.Boolean, default=False)
    is_dismissed = db.Column(db.Boolean, default=False)
    is_acted_upon = db.Column(db.Boolean, default=False)  # User applied/connected/enrolled
    created_at = db.Column(db.DateTime, default=func.now())
    expires_at = db.Column(db.DateTime)  # Recommendations can expire
    
    # Relationships
    user = db.relationship('User', backref=db.backref('recommendations', lazy='dynamic'))
    
    def __repr__(self):
        return f"<Recommendation user={self.user_id} type={self.recommendation_type} score={self.score}>"


class UserBehavior(db.Model):
    """Track user behavior for recommendation engine"""
    __tablename__ = "user_behavior"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)  # view, click, apply, save, share
    item_type = db.Column(db.String(50), nullable=False)  # job, profile, course, event
    item_id = db.Column(db.Integer, nullable=False)
    metadata = db.Column(JSONB)  # Additional context
    timestamp = db.Column(db.DateTime, default=func.now())
    session_id = db.Column(db.String(255))
    
    # Relationships
    user = db.relationship('User', backref=db.backref('behaviors', lazy='dynamic'))
    
    def __repr__(self):
        return f"<UserBehavior user={self.user_id} action={self.action_type}>"


# =======================
# AUTO-APPLY SYSTEM
# =======================

class AutoApplyQueue(db.Model):
    """Queue of jobs to auto-apply to"""
    __tablename__ = "auto_apply_queue"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job_postings.id'), nullable=False)
    resume_id = db.Column(db.Integer, db.ForeignKey('resumes.id'))
    cover_letter_id = db.Column(db.Integer)
    status = db.Column(db.String(20), default='queued')  # queued, processing, submitted, failed
    scheduled_for = db.Column(db.DateTime)
    processed_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    application_id = db.Column(db.Integer)  # ID of created application
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    user = db.relationship('User', backref=db.backref('auto_apply_queue', lazy='dynamic'))
    
    def __repr__(self):
        return f"<AutoApplyQueue user={self.user_id} job={self.job_id} status={self.status}>"


# =======================
# NOTIFICATIONS
# =======================

class NotificationPreference(db.Model):
    """User notification preferences"""
    __tablename__ = "notification_preferences"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Email notifications
    email_job_matches = db.Column(db.Boolean, default=True)
    email_messages = db.Column(db.Boolean, default=True)
    email_applications = db.Column(db.Boolean, default=True)
    email_events = db.Column(db.Boolean, default=True)
    email_weekly_digest = db.Column(db.Boolean, default=True)
    
    # Push notifications
    push_job_matches = db.Column(db.Boolean, default=True)
    push_messages = db.Column(db.Boolean, default=True)
    push_applications = db.Column(db.Boolean, default=True)
    push_events = db.Column(db.Boolean, default=True)
    push_achievements = db.Column(db.Boolean, default=True)
    
    # In-app notifications
    inapp_all = db.Column(db.Boolean, default=True)
    
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = db.relationship('User', backref=db.backref('notification_preferences', uselist=False))
    
    def __repr__(self):
        return f"<NotificationPreference user={self.user_id}>"


class PushSubscription(db.Model):
    """Web push notification subscriptions"""
    __tablename__ = "push_subscriptions"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    endpoint = db.Column(db.Text, nullable=False, unique=True)
    p256dh_key = db.Column(db.Text, nullable=False)
    auth_key = db.Column(db.Text, nullable=False)
    user_agent = db.Column(db.String(512))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=func.now())
    last_used = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('push_subscriptions', lazy='dynamic'))
    
    def __repr__(self):
        return f"<PushSubscription user={self.user_id}>"


class ChatMessage(db.Model):
    """AI career coach chat messages"""
    __tablename__ = "chat_messages"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # user or assistant
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=func.now())
    metadata = db.Column(JSONB)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('chat_messages', lazy='dynamic', order_by='ChatMessage.created_at'))
    
    def __repr__(self):
        return f"<ChatMessage user={self.user_id} role={self.role}>"


# =======================
# LIVE EVENTS MODELS
# =======================

class LiveEvent(db.Model):
    """Virtual career fairs, webinars, and Q&A sessions"""
    __tablename__ = "live_events"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    event_type = db.Column(db.String(50))  # career_fair, webinar, workshop, q_and_a
    host_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    meeting_link = db.Column(db.String(500))
    max_attendees = db.Column(db.Integer)
    is_public = db.Column(db.Boolean, default=True)
    recording_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    host = db.relationship('User', backref=db.backref('hosted_events', lazy='dynamic'))
    
    def __repr__(self):
        return f"<LiveEvent {self.title}>"


class EventAttendee(db.Model):
    """Tracks event registrations and attendance"""
    __tablename__ = "event_attendees"
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('live_events.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    registered_at = db.Column(db.DateTime, default=func.now())
    attended = db.Column(db.Boolean, default=False)
    
    # Relationships
    event = db.relationship('LiveEvent', backref=db.backref('attendees', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('events_attending', lazy='dynamic'))
    
    def __repr__(self):
        return f"<EventAttendee event={self.event_id} user={self.user_id}>"


class EventMessage(db.Model):
    """Chat messages and Q&A in live events"""
    __tablename__ = "event_messages"
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('live_events.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_question = db.Column(db.Boolean, default=False)
    is_answered = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    event = db.relationship('LiveEvent', backref=db.backref('messages', lazy='dynamic'))
    user = db.relationship('User')
    
    def __repr__(self):
        return f"<EventMessage event={self.event_id} user={self.user_id}>"
