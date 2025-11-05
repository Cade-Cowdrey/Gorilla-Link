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
    __table_args__ = {'extend_existing': True}
    
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
    __table_args__ = (
        db.UniqueConstraint('user_id', 'badge_id', name='unique_user_badge'),
        {'extend_existing': True}
    )
    
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
    
    def __repr__(self):
        return f"<UserBadge user={self.user_id} badge={self.badge_id}>"


class UserStreak(db.Model):
    """Tracks user daily/weekly streaks for engagement"""
    __tablename__ = "user_streaks"
    __table_args__ = {'extend_existing': True}
    
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
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f"<UserStreak user={self.user_id} type={self.streak_type} streak={self.current_streak}>"


class ProfileCompletionProgress(db.Model):
    """Tracks user profile completion percentage and tasks"""
    __tablename__ = "profile_completion_progress"
    __table_args__ = {'extend_existing': True}
    
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
    __table_args__ = {'extend_existing': True}
    
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
    __table_args__ = {'extend_existing': True}
    
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
    __table_args__ = {'extend_existing': True}
    
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
    __table_args__ = {'extend_existing': True}
    
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
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f"<StoryReaction story={self.story_id} user={self.user_id} type={self.reaction_type}>"


class StoryComment(db.Model):
    """Comments on success stories"""
    __tablename__ = "story_comments"
    __table_args__ = {'extend_existing': True}
    
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
    __table_args__ = {'extend_existing': True}
    
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
    __table_args__ = {'extend_existing': True}
    
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
    __table_args__ = {'extend_existing': True}
    
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
    __table_args__ = {'extend_existing': True}
    
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
    __table_args__ = {'extend_existing': True}
    
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
    __table_args__ = {'extend_existing': True}
    
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
    __table_args__ = {'extend_existing': True}
    
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
    __table_args__ = {'extend_existing': True}
    
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
    __table_args__ = {'extend_existing': True}
    
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
    __table_args__ = {'extend_existing': True}
    
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
    meta_data = db.Column(JSONB)  # Additional context - Renamed from metadata
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
    __table_args__ = {'extend_existing': True}
    
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
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # user or assistant
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=func.now())
    meta_data = db.Column(JSONB)  # Renamed from metadata to avoid SQLAlchemy conflict
    
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


# =======================
# INSTITUTIONAL FEATURES
# =======================

class UniversityVerification(db.Model):
    """Verify users are actual PSU students/alumni"""
    __tablename__ = "university_verifications"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    verification_type = db.Column(db.String(50), nullable=False)  # student, alumni, faculty, staff
    student_id = db.Column(db.String(50))  # Official PSU student ID
    graduation_year = db.Column(db.Integer)
    degree_program = db.Column(db.String(255))
    verification_method = db.Column(db.String(50))  # email, id_upload, admin_manual
    verified_at = db.Column(db.DateTime)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # Admin who verified
    verification_document = db.Column(db.String(512))  # S3 path to uploaded ID/diploma
    is_verified = db.Column(db.Boolean, default=False)
    verification_status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    rejection_reason = db.Column(db.Text)
    expires_at = db.Column(db.DateTime)  # Students need to reverify each semester
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('verification', uselist=False))
    verifier = db.relationship('User', foreign_keys=[verified_by])
    
    def __repr__(self):
        return f"<UniversityVerification user={self.user_id} type={self.verification_type} verified={self.is_verified}>"


class DepartmentAffiliation(db.Model):
    """Link users to official PSU departments"""
    __tablename__ = "department_affiliations"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    affiliation_type = db.Column(db.String(50))  # major, minor, faculty, advisor
    is_primary = db.Column(db.Boolean, default=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    user = db.relationship('User', backref=db.backref('department_affiliations', lazy='dynamic'))
    
    def __repr__(self):
        return f"<DepartmentAffiliation user={self.user_id} dept={self.department_id}>"


class AcademicRecord(db.Model):
    """Store basic academic information (FERPA compliant - no grades)"""
    __tablename__ = "academic_records"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    enrollment_status = db.Column(db.String(50))  # full_time, part_time, graduated, withdrawn
    class_year = db.Column(db.String(20))  # Freshman, Sophomore, Junior, Senior, Graduate
    expected_graduation = db.Column(db.Date)
    actual_graduation = db.Column(db.Date)
    cumulative_credits = db.Column(db.Integer)
    major_declared = db.Column(db.Boolean, default=False)
    honors_program = db.Column(db.Boolean, default=False)
    dean_list = db.Column(ARRAY(db.String))  # Semesters on dean's list
    academic_standing = db.Column(db.String(50))  # good_standing, probation, etc.
    last_updated = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = db.relationship('User', backref=db.backref('academic_record', uselist=False))
    
    def __repr__(self):
        return f"<AcademicRecord user={self.user_id} status={self.enrollment_status}>"


class EmployerPartnership(db.Model):
    """Official PSU employer partnerships"""
    __tablename__ = "employer_partnerships"
    
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(255), nullable=False)
    partnership_type = db.Column(db.String(50))  # career_fair, exclusive_posting, internship_program
    contact_name = db.Column(db.String(255))
    contact_email = db.Column(db.String(255))
    contact_phone = db.Column(db.String(50))
    partnership_level = db.Column(db.String(20))  # platinum, gold, silver, bronze
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    annual_hires = db.Column(db.Integer)
    exclusive_access = db.Column(db.Boolean, default=False)  # First access to PSU students
    logo_url = db.Column(db.String(512))
    website = db.Column(db.String(512))
    industries = db.Column(ARRAY(db.String))
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=func.now())
    
    def __repr__(self):
        return f"<EmployerPartnership {self.company_name} level={self.partnership_level}>"


class CareerServiceAppointment(db.Model):
    """Schedule appointments with career services advisors"""
    __tablename__ = "career_service_appointments"
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    advisor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    appointment_type = db.Column(db.String(50))  # resume_review, career_counseling, interview_prep, general
    scheduled_at = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=30)
    location = db.Column(db.String(255))  # Office room or Zoom link
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled, no_show
    student_notes = db.Column(db.Text)  # What student wants to discuss
    advisor_notes = db.Column(db.Text)  # Private advisor notes
    follow_up_required = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    student = db.relationship('User', foreign_keys=[student_id], backref=db.backref('career_appointments', lazy='dynamic'))
    advisor = db.relationship('User', foreign_keys=[advisor_id], backref=db.backref('advisor_appointments', lazy='dynamic'))
    
    def __repr__(self):
        return f"<CareerServiceAppointment student={self.student_id} advisor={self.advisor_id}>"


class InstitutionalAnnouncement(db.Model):
    """Official university announcements and alerts"""
    __tablename__ = "institutional_announcements"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    announcement_type = db.Column(db.String(50))  # urgent, maintenance, deadline, general, emergency
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, critical
    target_audience = db.Column(ARRAY(db.String))  # all, students, alumni, faculty, specific_departments
    department_ids = db.Column(ARRAY(db.Integer))  # Target specific departments
    posted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    show_as_banner = db.Column(db.Boolean, default=False)
    banner_color = db.Column(db.String(20))  # red for urgent, blue for info
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    attachments = db.Column(JSONB)  # PDFs, forms, etc.
    views_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    poster = db.relationship('User', backref=db.backref('posted_announcements', lazy='dynamic'))
    
    def __repr__(self):
        return f"<InstitutionalAnnouncement {self.title} type={self.announcement_type}>"


class ComplianceLog(db.Model):
    """Track compliance-related activities (FERPA, data access, etc.)"""
    __tablename__ = "compliance_logs"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action_type = db.Column(db.String(50), nullable=False)  # data_access, export, deletion, verification
    resource_type = db.Column(db.String(50))  # user_profile, academic_record, application
    resource_id = db.Column(db.Integer)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(512))
    justification = db.Column(db.Text)  # Why was this data accessed
    details = db.Column(JSONB)
    timestamp = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('compliance_logs_user', lazy='dynamic'))
    admin = db.relationship('User', foreign_keys=[admin_id], backref=db.backref('compliance_logs_admin', lazy='dynamic'))
    
    def __repr__(self):
        return f"<ComplianceLog action={self.action_type} user={self.user_id}>"


class DataExportRequest(db.Model):
    """GDPR/FERPA data export requests"""
    __tablename__ = "data_export_requests"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    request_type = db.Column(db.String(50))  # full_export, specific_data, deletion_request
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    file_path = db.Column(db.String(512))  # S3 path to generated export
    expires_at = db.Column(db.DateTime)  # Export links expire after 7 days
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=func.now())
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('data_export_requests', lazy='dynamic'))
    processor = db.relationship('User', foreign_keys=[processed_by])
    
    def __repr__(self):
        return f"<DataExportRequest user={self.user_id} status={self.status}>"


class SystemHealthMetric(db.Model):
    """Track system health and performance"""
    __tablename__ = "system_health_metrics"
    
    id = db.Column(db.Integer, primary_key=True)
    metric_type = db.Column(db.String(50), nullable=False)  # response_time, error_rate, active_users, db_connections
    metric_value = db.Column(db.Float, nullable=False)
    threshold_warning = db.Column(db.Float)
    threshold_critical = db.Column(db.Float)
    status = db.Column(db.String(20))  # healthy, warning, critical
    details = db.Column(JSONB)
    timestamp = db.Column(db.DateTime, default=func.now())
    
    def __repr__(self):
        return f"<SystemHealthMetric {self.metric_type}={self.metric_value}>"


class AdministratorRole(db.Model):
    """Granular admin permissions for university staff"""
    __tablename__ = "administrator_roles"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role_name = db.Column(db.String(100), nullable=False)  # career_services, registrar, department_head, super_admin
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    
    # Permissions
    can_verify_students = db.Column(db.Boolean, default=False)
    can_manage_jobs = db.Column(db.Boolean, default=False)
    can_view_analytics = db.Column(db.Boolean, default=False)
    can_manage_partnerships = db.Column(db.Boolean, default=False)
    can_send_announcements = db.Column(db.Boolean, default=False)
    can_access_reports = db.Column(db.Boolean, default=False)
    can_manage_users = db.Column(db.Boolean, default=False)
    can_export_data = db.Column(db.Boolean, default=False)
    
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    assigned_at = db.Column(db.DateTime, default=func.now())
    expires_at = db.Column(db.DateTime)  # Roles can expire (e.g., temporary admin)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('admin_roles', lazy='dynamic'))
    assigner = db.relationship('User', foreign_keys=[assigned_by])
    
    def __repr__(self):
        return f"<AdministratorRole user={self.user_id} role={self.role_name}>"


class AlumniDonation(db.Model):
    """Track alumni donations (for engagement scoring)"""
    __tablename__ = "alumni_donations"
    
    id = db.Column(db.Integer, primary_key=True)
    alumni_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    campaign_name = db.Column(db.String(255))
    donation_type = db.Column(db.String(50))  # one_time, recurring, scholarship, department
    designated_fund = db.Column(db.String(255))  # Scholarship fund, department, athletics
    is_anonymous = db.Column(db.Boolean, default=False)
    payment_method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(255))
    donated_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    alumni = db.relationship('User', backref=db.backref('donations', lazy='dynamic'))
    
    def __repr__(self):
        return f"<AlumniDonation alumni={self.alumni_id} amount=${self.amount}>"


class EventSponsor(db.Model):
    """Corporate sponsors for career fairs and events"""
    __tablename__ = "event_sponsors"
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('live_events.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('employer_partnerships.id'))
    company_name = db.Column(db.String(255), nullable=False)
    sponsorship_level = db.Column(db.String(50))  # title, platinum, gold, silver, bronze
    booth_number = db.Column(db.String(20))
    representatives = db.Column(JSONB)  # List of company reps attending
    logo_url = db.Column(db.String(512))
    website = db.Column(db.String(512))
    recruiting_positions = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    event = db.relationship('LiveEvent', backref=db.backref('sponsors', lazy='dynamic'))
    
    def __repr__(self):
        return f"<EventSponsor {self.company_name} event={self.event_id}>"


# =======================
# INSTITUTIONAL REPORTS
# =======================

class OutcomeReport(db.Model):
    """Track graduate outcomes for institutional reporting"""
    __tablename__ = "outcome_reports"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    graduation_year = db.Column(db.Integer, nullable=False)
    outcome_type = db.Column(db.String(50))  # employed, continuing_education, military, seeking, other
    
    # Employment details
    employer_name = db.Column(db.String(255))
    job_title = db.Column(db.String(255))
    salary_range = db.Column(db.String(50))
    employment_type = db.Column(db.String(50))  # full_time, part_time, contract, internship
    related_to_major = db.Column(db.Boolean)
    located_in_kansas = db.Column(db.Boolean)
    
    # Continuing education
    grad_school_name = db.Column(db.String(255))
    degree_pursuing = db.Column(db.String(100))
    
    # Survey details
    survey_completed_at = db.Column(db.DateTime)
    months_to_employment = db.Column(db.Integer)  # Time from graduation to job
    satisfaction_score = db.Column(db.Integer)  # 1-5: How well PSU prepared them
    would_recommend = db.Column(db.Boolean)
    
    # Reporting
    reported_to_ksde = db.Column(db.Boolean, default=False)  # Kansas State Dept of Ed
    reported_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = db.relationship('User', backref=db.backref('outcome_report', uselist=False))
    
    def __repr__(self):
        return f"<OutcomeReport user={self.user_id} year={self.graduation_year} outcome={self.outcome_type}>"


# =======================
# APPOINTMENT BOOKING SYSTEM
# =======================

class AdvisorAvailability(db.Model):
    """Track when career advisors are available for appointments"""
    __tablename__ = "advisor_availability"
    
    id = db.Column(db.Integer, primary_key=True)
    advisor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    day_of_week = db.Column(db.String(10), nullable=False)  # monday, tuesday, etc.
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_recurring = db.Column(db.Boolean, default=True)
    specific_date = db.Column(db.Date)  # For one-time availability changes
    is_available = db.Column(db.Boolean, default=True)
    max_appointments_per_slot = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    advisor = db.relationship('User', backref=db.backref('availability_slots', lazy='dynamic'))
    
    def __repr__(self):
        return f"<AdvisorAvailability advisor={self.advisor_id} {self.day_of_week} {self.start_time}-{self.end_time}>"


class AppointmentFeedback(db.Model):
    """Student feedback on career services appointments"""
    __tablename__ = "appointment_feedback"
    
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('career_service_appointments.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer)  # 1-5 stars
    was_helpful = db.Column(db.Boolean)
    followed_advice = db.Column(db.Boolean)
    outcome_improved = db.Column(db.Boolean)  # Did they get interview/job after?
    comments = db.Column(db.Text)
    would_recommend_advisor = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    appointment = db.relationship('CareerServiceAppointment', backref=db.backref('feedback', uselist=False))
    student = db.relationship('User', backref=db.backref('appointment_feedback', lazy='dynamic'))
    
    def __repr__(self):
        return f"<AppointmentFeedback appointment={self.appointment_id} rating={self.rating}>"


# =======================
# ANALYTICS DASHBOARD MODELS
# =======================

class DashboardMetric(db.Model):
    """Real-time metrics for administrator dashboard"""
    __tablename__ = "dashboard_metrics"
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(100), nullable=False)
    metric_category = db.Column(db.String(50))  # engagement, outcomes, financial, retention
    current_value = db.Column(db.Float, nullable=False)
    previous_value = db.Column(db.Float)
    target_value = db.Column(db.Float)
    unit = db.Column(db.String(20))  # percentage, count, dollars, days
    trend = db.Column(db.String(20))  # increasing, decreasing, stable
    time_period = db.Column(db.String(50))  # daily, weekly, monthly, semester, annual
    calculation_method = db.Column(db.Text)  # SQL query or logic used
    last_calculated = db.Column(db.DateTime, default=func.now())
    metric_metadata = db.Column(JSONB)  # Additional context (renamed from 'metadata')
    
    def calculate_change_percentage(self):
        """Calculate percentage change from previous value"""
        if not self.previous_value or self.previous_value == 0:
            return 0
        return ((self.current_value - self.previous_value) / self.previous_value) * 100
    
    def is_on_track(self):
        """Check if metric is meeting target"""
        if not self.target_value:
            return None
        return self.current_value >= self.target_value
    
    def __repr__(self):
        return f"<DashboardMetric {self.metric_name}={self.current_value}{self.unit}>"


class PlatformEngagement(db.Model):
    """Daily engagement metrics for tracking platform usage"""
    __tablename__ = "platform_engagement"
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    
    # User Activity
    daily_active_users = db.Column(db.Integer, default=0)
    new_registrations = db.Column(db.Integer, default=0)
    returning_users = db.Column(db.Integer, default=0)
    
    # Feature Usage
    job_applications_submitted = db.Column(db.Integer, default=0)
    scholarship_applications_submitted = db.Column(db.Integer, default=0)
    appointments_booked = db.Column(db.Integer, default=0)
    messages_sent = db.Column(db.Integer, default=0)
    profile_updates = db.Column(db.Integer, default=0)
    resume_downloads = db.Column(db.Integer, default=0)
    
    # Alumni Engagement
    alumni_logins = db.Column(db.Integer, default=0)
    mentorship_connections = db.Column(db.Integer, default=0)
    donations_initiated = db.Column(db.Integer, default=0)
    
    # System Health
    average_session_duration_minutes = db.Column(db.Float)
    pages_per_session = db.Column(db.Float)
    bounce_rate = db.Column(db.Float)
    
    created_at = db.Column(db.DateTime, default=func.now())
    
    def __repr__(self):
        return f"<PlatformEngagement {self.date} DAU={self.daily_active_users}>"


class CareerServicesImpact(db.Model):
    """Track ROI and effectiveness of career services integration"""
    __tablename__ = "career_services_impact"
    
    id = db.Column(db.Integer, primary_key=True)
    report_period = db.Column(db.String(20))  # weekly, monthly, semester, annual
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    
    # Efficiency Metrics
    total_appointments_booked = db.Column(db.Integer, default=0)
    appointments_via_platform = db.Column(db.Integer, default=0)
    appointments_via_traditional = db.Column(db.Integer, default=0)
    average_booking_time_seconds = db.Column(db.Float)  # Time to book via platform
    staff_hours_saved = db.Column(db.Float, default=0)
    
    # Reach Metrics
    unique_students_helped = db.Column(db.Integer, default=0)
    students_percentage_of_total = db.Column(db.Float)
    first_time_users = db.Column(db.Integer, default=0)
    repeat_users = db.Column(db.Integer, default=0)
    
    # Outcome Metrics
    students_who_got_interviews = db.Column(db.Integer, default=0)
    students_who_got_jobs = db.Column(db.Integer, default=0)
    average_days_to_interview = db.Column(db.Float)
    average_days_to_job_offer = db.Column(db.Float)
    average_starting_salary = db.Column(db.Integer)
    
    # Satisfaction Metrics
    average_appointment_rating = db.Column(db.Float)
    would_recommend_percentage = db.Column(db.Float)
    students_who_followed_advice = db.Column(db.Integer, default=0)
    
    # Financial Impact
    estimated_cost_savings = db.Column(db.Float)  # vs. hiring more staff
    alumni_giving_increase = db.Column(db.Float)
    scholarship_dollars_distributed = db.Column(db.Float)
    
    # Accreditation Ready
    outcome_data_completeness_percentage = db.Column(db.Float)  # How much grad outcome data we have
    
    created_at = db.Column(db.DateTime, default=func.now())
    generated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    generator = db.relationship('User', backref=db.backref('generated_impact_reports', lazy='dynamic'))
    
    def calculate_efficiency_gain(self):
        """Calculate percentage improvement over traditional methods"""
        if self.appointments_via_traditional == 0:
            return 0
        return ((self.appointments_via_platform - self.appointments_via_traditional) / 
                self.appointments_via_traditional) * 100
    
    def calculate_roi(self):
        """Calculate return on investment"""
        # Cost savings + alumni giving increase + scholarship value
        total_value = (self.estimated_cost_savings or 0) + \
                      (self.alumni_giving_increase or 0) + \
                      (self.scholarship_dollars_distributed or 0)
        # Platform cost (essentially zero for PSU-built platform)
        return total_value
    
    def __repr__(self):
        return f"<CareerServicesImpact {self.period_start} to {self.period_end}>"


class AdminAlert(db.Model):
    """Automated alerts for administrators about important events"""
    __tablename__ = "admin_alerts"
    
    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(50), nullable=False)  # metric_drop, high_engagement, system_issue, milestone
    severity = db.Column(db.String(20), default='info')  # info, warning, critical
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    action_required = db.Column(db.Boolean, default=False)
    action_url = db.Column(db.String(255))  # Link to take action
    related_metric = db.Column(db.String(100))
    metric_value = db.Column(db.Float)
    threshold_crossed = db.Column(db.Float)
    is_read = db.Column(db.Boolean, default=False)
    is_resolved = db.Column(db.Boolean, default=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=func.now())
    resolved_at = db.Column(db.DateTime)
    
    # Relationships
    assignee = db.relationship('User', backref=db.backref('assigned_alerts', lazy='dynamic'))
    
    def __repr__(self):
        return f"<AdminAlert {self.alert_type} severity={self.severity}>"


class IntegrationLog(db.Model):
    """Track integrations with other PSU systems"""
    __tablename__ = "integration_logs"
    
    id = db.Column(db.Integer, primary_key=True)
    integration_name = db.Column(db.String(100), nullable=False)  # mygus, banner, canvas, handshake
    action = db.Column(db.String(50), nullable=False)  # sync, export, import, api_call
    status = db.Column(db.String(20), nullable=False)  # success, failure, partial
    records_processed = db.Column(db.Integer, default=0)
    records_failed = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    execution_time_seconds = db.Column(db.Float)
    api_endpoint = db.Column(db.String(255))
    request_payload = db.Column(JSONB)
    response_payload = db.Column(JSONB)
    initiated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    initiator = db.relationship('User', backref=db.backref('integration_actions', lazy='dynamic'))
    
    def __repr__(self):
        return f"<IntegrationLog {self.integration_name} {self.action} status={self.status}>"


class ExportableReport(db.Model):
    """Pre-generated reports for administrators to download"""
    __tablename__ = "exportable_reports"
    
    id = db.Column(db.Integer, primary_key=True)
    report_name = db.Column(db.String(255), nullable=False)
    report_type = db.Column(db.String(50), nullable=False)  # engagement, outcomes, financial, accreditation
    description = db.Column(db.Text)
    file_format = db.Column(db.String(10))  # pdf, csv, xlsx, json
    file_path = db.Column(db.String(500))
    file_size_bytes = db.Column(db.Integer)
    period_covered = db.Column(db.String(100))  # "Fall 2024", "January 2025", etc.
    generated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_public = db.Column(db.Boolean, default=False)
    download_count = db.Column(db.Integer, default=0)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    generator = db.relationship('User', backref=db.backref('generated_reports', lazy='dynamic'))
    
    def __repr__(self):
        return f"<ExportableReport {self.report_name} type={self.report_type}>"


# ==============================================================================
# SCHOLARSHIP INTEGRATION MODELS
# ==============================================================================

class ScholarshipMatch(db.Model):
    """AI-matched scholarships from real APIs"""
    __tablename__ = 'scholarship_matches'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Scholarship Details
    title = db.Column(db.String(255), nullable=False)
    provider = db.Column(db.String(255))
    amount = db.Column(db.Integer)  # Scholarship amount in dollars
    deadline = db.Column(db.DateTime)
    description = db.Column(db.Text)
    requirements = db.Column(db.JSON)  # List of requirements
    url = db.Column(db.String(500))
    source = db.Column(db.String(50))  # scholarships.com, fastweb, college_board
    
    # Match Details
    match_score = db.Column(db.Float)  # 0-100 how well student matches
    is_eligible = db.Column(db.Boolean, default=True)
    missing_requirements = db.Column(db.JSON)  # What student needs
    recommendations = db.Column(db.JSON)  # Action items
    
    # Status Tracking
    status = db.Column(db.String(50), default='matched')  # matched, applied, awarded, declined
    applied_at = db.Column(db.DateTime)
    awarded_at = db.Column(db.DateTime)
    awarded_amount = db.Column(db.Integer)  # Actual amount if different
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_synced = db.Column(db.DateTime, default=datetime.utcnow)
    is_renewable = db.Column(db.Boolean, default=False)
    essay_required = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('scholarship_matches', lazy='dynamic'))
    
    def days_until_deadline(self):
        """Calculate days remaining until deadline"""
        if not self.deadline:
            return None
        delta = self.deadline - datetime.utcnow()
        return max(0, delta.days)
    
    def is_deadline_soon(self):
        """Check if deadline is within 2 weeks"""
        days = self.days_until_deadline()
        return days is not None and days < 14
    
    def __repr__(self):
        return f"<ScholarshipMatch {self.title} - ${self.amount} - {self.match_score}%>"


class ScholarshipApplication(db.Model):
    """Track scholarship application progress"""
    __tablename__ = 'scholarship_applications'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    scholarship_match_id = db.Column(db.Integer, db.ForeignKey('scholarship_matches.id'))
    
    # Application Details
    scholarship_name = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Integer)
    deadline = db.Column(db.DateTime)
    
    # Progress Tracking
    status = db.Column(db.String(50), default='not_started')  # not_started, in_progress, submitted, awarded, rejected
    progress_percentage = db.Column(db.Integer, default=0)
    
    # Requirements Checklist
    essay_completed = db.Column(db.Boolean, default=False)
    recommendation_letters_count = db.Column(db.Integer, default=0)
    recommendation_letters_required = db.Column(db.Integer, default=0)
    transcript_submitted = db.Column(db.Boolean, default=False)
    
    # Timestamps
    started_at = db.Column(db.DateTime)
    submitted_at = db.Column(db.DateTime)
    result_received_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Result
    awarded = db.Column(db.Boolean)
    awarded_amount = db.Column(db.Integer)
    award_notification = db.Column(db.Text)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('scholarship_applications', lazy='dynamic'))
    scholarship_match = db.relationship('ScholarshipMatch', backref='applications')
    
    def update_progress(self):
        """Calculate application progress percentage"""
        total_items = 1  # Base application
        completed_items = 0
        
        if self.essay_completed:
            completed_items += 1
        total_items += 1
        
        if self.recommendation_letters_required > 0:
            total_items += self.recommendation_letters_required
            completed_items += min(self.recommendation_letters_count, self.recommendation_letters_required)
        
        if self.transcript_submitted:
            completed_items += 1
        total_items += 1
        
        self.progress_percentage = int((completed_items / total_items) * 100)
        return self.progress_percentage
    
    def __repr__(self):
        return f"<ScholarshipApplication {self.scholarship_name} - {self.status}>"


# ==============================================================================
# LINKEDIN INTEGRATION MODELS
# ==============================================================================

class LinkedInProfile(db.Model):
    """Store LinkedIn profile data for graduate outcome tracking"""
    __tablename__ = 'linkedin_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    
    # LinkedIn Data
    linkedin_id = db.Column(db.String(100), unique=True)
    profile_url = db.Column(db.String(500))
    headline = db.Column(db.String(255))
    current_position = db.Column(db.String(255))
    current_company = db.Column(db.String(255))
    industry = db.Column(db.String(100))
    location = db.Column(db.String(255))
    
    # Career Data
    total_experience_years = db.Column(db.Integer)
    skills = db.Column(db.JSON)  # Array of skills
    endorsements_count = db.Column(db.Integer)
    connections_count = db.Column(db.Integer)
    
    # Employment History
    employment_history = db.Column(db.JSON)  # Array of {title, company, start_date, end_date, description}
    
    # OAuth Tokens
    access_token = db.Column(db.String(500))
    refresh_token = db.Column(db.String(500))
    token_expires_at = db.Column(db.DateTime)
    
    # Sync Status
    last_synced = db.Column(db.DateTime)
    sync_enabled = db.Column(db.Boolean, default=True)
    sync_frequency = db.Column(db.String(20), default='weekly')  # daily, weekly, monthly
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('linkedin_profile', uselist=False))
    
    def is_token_valid(self):
        """Check if OAuth token is still valid"""
        if not self.token_expires_at:
            return False
        return datetime.utcnow() < self.token_expires_at
    
    def get_current_role(self):
        """Get current employment role"""
        if self.employment_history:
            # Return most recent position
            sorted_history = sorted(
                self.employment_history, 
                key=lambda x: x.get('start_date', ''), 
                reverse=True
            )
            if sorted_history:
                return sorted_history[0]
        return None
    
    def __repr__(self):
        return f"<LinkedInProfile {self.user.email} - {self.current_position}>"


# ==============================================================================
# EMAIL NOTIFICATION MODELS
# ==============================================================================

class EmailNotification(db.Model):
    """Track sent email notifications"""
    __tablename__ = 'email_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Email Details
    notification_type = db.Column(db.String(50), nullable=False)  # appointment_confirmation, scholarship_match, job_alert
    subject = db.Column(db.String(255))
    body = db.Column(db.Text)
    recipient_email = db.Column(db.String(255))
    
    # Status
    status = db.Column(db.String(50), default='queued')  # queued, sent, failed, bounced
    sent_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    
    # Engagement Tracking
    opened_at = db.Column(db.DateTime)
    clicked_at = db.Column(db.DateTime)
    unsubscribed = db.Column(db.Boolean, default=False)
    
    # Related Entities
    related_entity_type = db.Column(db.String(50))  # appointment, scholarship, job
    related_entity_id = db.Column(db.Integer)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('email_notifications', lazy='dynamic'))
    
    def __repr__(self):
        return f"<EmailNotification {self.notification_type} to {self.recipient_email} - {self.status}>"


class NotificationPreference(db.Model):
    """User preferences for email notifications"""
    __tablename__ = 'notification_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    
    # Notification Settings
    email_enabled = db.Column(db.Boolean, default=True)
    sms_enabled = db.Column(db.Boolean, default=False)
    push_enabled = db.Column(db.Boolean, default=True)
    
    # Type-specific Settings
    appointment_reminders = db.Column(db.Boolean, default=True)
    scholarship_matches = db.Column(db.Boolean, default=True)
    job_alerts = db.Column(db.Boolean, default=True)
    event_notifications = db.Column(db.Boolean, default=True)
    mentorship_messages = db.Column(db.Boolean, default=True)
    platform_updates = db.Column(db.Boolean, default=False)
    
    # Frequency Settings
    digest_frequency = db.Column(db.String(20), default='daily')  # immediate, daily, weekly
    quiet_hours_start = db.Column(db.Time)  # Don't send during these hours
    quiet_hours_end = db.Column(db.Time)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('notification_preferences', uselist=False))
    
    def __repr__(self):
        return f"<NotificationPreference {self.user.email}>"


# ==============================================================================
# AI CAREER COACH MODELS
# ==============================================================================

class AIChatSession(db.Model):
    """AI Career Coach chat sessions"""
    __tablename__ = 'ai_chat_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Session Details
    title = db.Column(db.String(255), default='Career Coaching Session')
    session_type = db.Column(db.String(50), default='general')  # general, resume, interview, career_planning
    is_active = db.Column(db.Boolean, default=True)
    
    # Metadata
    message_count = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_message_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    
    # Rating
    rating = db.Column(db.Integer)  # 1-5 stars
    feedback = db.Column(db.Text)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('ai_chat_sessions', lazy='dynamic'))
    
    def __repr__(self):
        return f"<AIChatSession {self.id} - {self.user.email}>"


class AIChatMessage(db.Model):
    """Individual messages in AI chat sessions"""
    __tablename__ = 'ai_chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('ai_chat_sessions.id'), nullable=False)
    
    # Message Content
    role = db.Column(db.String(20), nullable=False)  # user, assistant, system
    content = db.Column(db.Text, nullable=False)
    
    # AI Model Details
    model = db.Column(db.String(50))  # gpt-4, gpt-3.5-turbo
    tokens_used = db.Column(db.Integer)
    cost = db.Column(db.Float)  # Estimated cost in USD
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    session = db.relationship('AIChatSession', backref=db.backref('messages', lazy='dynamic'))
    
    def __repr__(self):
        return f"<AIChatMessage {self.role}: {self.content[:50]}...>"


# ==============================================================================
# EMPLOYER PORTAL MODELS
# ==============================================================================

class EmployerProfile(db.Model):
    """Employer company profiles"""
    __tablename__ = 'employer_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Company Information
    company_name = db.Column(db.String(255), nullable=False)
    industry = db.Column(db.String(100))
    company_size = db.Column(db.String(50))  # 1-10, 11-50, 51-200, 201-500, 500+
    website = db.Column(db.String(500))
    logo_url = db.Column(db.String(500))
    
    # Location
    headquarters_location = db.Column(db.String(255))
    hiring_locations = db.Column(db.JSON)  # Array of locations
    
    # Description
    description = db.Column(db.Text)
    culture = db.Column(db.Text)
    benefits = db.Column(db.JSON)  # Array of benefits
    
    # Contact Information
    recruiter_name = db.Column(db.String(255))
    recruiter_email = db.Column(db.String(255))
    recruiter_phone = db.Column(db.String(50))
    
    # Subscription
    subscription_tier = db.Column(db.String(50), default='free')  # free, basic, premium
    subscription_expires_at = db.Column(db.DateTime)
    job_posts_remaining = db.Column(db.Integer, default=3)  # Free tier gets 3 posts
    
    # Verification
    is_verified = db.Column(db.Boolean, default=False)
    verified_at = db.Column(db.DateTime)
    verified_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('employer_profile', uselist=False))
    verifier = db.relationship('User', foreign_keys=[verified_by])
    
    def can_post_job(self):
        """Check if employer can post more jobs"""
        if self.subscription_tier == 'premium':
            return True
        return self.job_posts_remaining > 0
    
    def __repr__(self):
        return f"<EmployerProfile {self.company_name}>"


class EmployerJobPosting(db.Model):
    """Job postings from employer portal"""
    __tablename__ = 'employer_job_postings'
    
    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey('employer_profiles.id'), nullable=False)
    
    # Job Details
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.JSON)  # Array of requirements
    responsibilities = db.Column(db.JSON)  # Array of responsibilities
    
    # Compensation
    salary_min = db.Column(db.Integer)
    salary_max = db.Column(db.Integer)
    salary_currency = db.Column(db.String(10), default='USD')
    hourly_rate = db.Column(db.Float)
    benefits = db.Column(db.JSON)
    
    # Location
    location = db.Column(db.String(255))
    remote_policy = db.Column(db.String(50))  # onsite, hybrid, remote
    
    # Employment Details
    employment_type = db.Column(db.String(50))  # full_time, part_time, contract, internship
    experience_level = db.Column(db.String(50))  # entry, mid, senior, executive
    education_required = db.Column(db.String(100))
    
    # Application
    application_url = db.Column(db.String(500))
    application_email = db.Column(db.String(255))
    application_instructions = db.Column(db.Text)
    
    # Status
    status = db.Column(db.String(50), default='draft')  # draft, active, filled, closed
    posted_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    filled_at = db.Column(db.DateTime)
    
    # Metrics
    views_count = db.Column(db.Integer, default=0)
    applications_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employer = db.relationship('EmployerProfile', backref=db.backref('job_postings', lazy='dynamic'))
    
    def is_active(self):
        """Check if job posting is currently active"""
        if self.status != 'active':
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True
    
    def days_remaining(self):
        """Days until posting expires"""
        if not self.expires_at:
            return None
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)
    
    def __repr__(self):
        return f"<EmployerJobPosting {self.title} at {self.employer.company_name}>"


# ==============================================================================
# AI SUCCESS PREDICTOR MODELS
# ==============================================================================

class StudentRiskScore(db.Model):
    """AI-predicted risk scores for student intervention"""
    __tablename__ = 'student_risk_scores'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Risk Assessment
    overall_risk_score = db.Column(db.Float)  # 0-100, higher = more at risk
    risk_level = db.Column(db.String(20))  # low, medium, high, critical
    
    # Component Scores
    academic_risk = db.Column(db.Float)  # Based on GPA, course load
    engagement_risk = db.Column(db.Float)  # Based on platform activity
    career_readiness_risk = db.Column(db.Float)  # Based on applications, appointments
    financial_risk = db.Column(db.Float)  # Based on scholarship applications
    
    # Factors
    contributing_factors = db.Column(db.JSON)  # Array of risk factors
    protective_factors = db.Column(db.JSON)  # Array of positive factors
    
    # Recommendations
    recommended_interventions = db.Column(db.JSON)  # Array of suggested actions
    priority_level = db.Column(db.Integer)  # 1-5, higher = more urgent
    
    # Status
    intervention_status = db.Column(db.String(50), default='identified')  # identified, contacted, in_progress, resolved
    assigned_advisor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    contacted_at = db.Column(db.DateTime)
    resolved_at = db.Column(db.DateTime)
    
    # Model Details
    model_version = db.Column(db.String(50))
    prediction_confidence = db.Column(db.Float)  # 0-1
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Historical
    previous_score = db.Column(db.Float)
    score_trend = db.Column(db.String(20))  # improving, stable, declining
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('risk_scores', lazy='dynamic'))
    assigned_advisor = db.relationship('User', foreign_keys=[assigned_advisor_id])
    
    def needs_immediate_attention(self):
        """Check if student needs immediate intervention"""
        return self.risk_level in ['high', 'critical'] and self.intervention_status == 'identified'
    
    def get_top_concerns(self, limit=3):
        """Get top N contributing factors"""
        if not self.contributing_factors:
            return []
        return self.contributing_factors[:limit]
    
    def __repr__(self):
        return f"<StudentRiskScore {self.user.email} - {self.risk_level} ({self.overall_risk_score})>"


# ==============================================================================
# FREE CERTIFICATIONS & SKILLS HUB
# ==============================================================================

class FreeCertification(db.Model):
    """Curated free certifications from Google, Microsoft, AWS, etc."""
    __tablename__ = 'free_certifications'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Certification Details
    title = db.Column(db.String(255), nullable=False)
    provider = db.Column(db.String(100), nullable=False)  # Google, Microsoft, AWS, HubSpot, etc.
    category = db.Column(db.String(100))  # Technology, Marketing, Business, Safety, etc.
    subcategory = db.Column(db.String(100))  # Programming, Cloud, Analytics, etc.
    
    # Description
    description = db.Column(db.Text)
    skills_gained = db.Column(db.JSON)  # Array of skills learned
    
    # Course Details
    duration_hours = db.Column(db.Integer)  # Estimated time to complete
    difficulty_level = db.Column(db.String(50))  # beginner, intermediate, advanced
    language = db.Column(db.String(50), default='English')
    
    # Links
    course_url = db.Column(db.String(500), nullable=False)
    certificate_url = db.Column(db.String(500))  # Link to get certificate after completion
    provider_logo_url = db.Column(db.String(500))
    
    # Value Indicators
    industry_recognition = db.Column(db.String(50))  # high, medium, low
    resume_boost_score = db.Column(db.Integer)  # 0-100, how much it helps resume
    job_relevance_score = db.Column(db.Integer)  # 0-100, how relevant to jobs
    salary_impact = db.Column(db.String(100))  # "$5K-$10K increase", "Entry-level requirement", etc.
    
    # Prerequisites
    prerequisites = db.Column(db.JSON)  # Array of requirements
    recommended_for_majors = db.Column(db.JSON)  # Array of majors this is relevant for
    recommended_for_careers = db.Column(db.JSON)  # Array of career paths
    
    # Engagement
    views_count = db.Column(db.Integer, default=0)
    enrollments_count = db.Column(db.Integer, default=0)
    completions_count = db.Column(db.Integer, default=0)
    average_rating = db.Column(db.Float)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    verified_by_psu = db.Column(db.Boolean, default=False)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_verified = db.Column(db.DateTime)
    
    def get_completion_rate(self):
        """Calculate completion rate percentage"""
        if self.enrollments_count == 0:
            return 0
        return (self.completions_count / self.enrollments_count) * 100
    
    def is_quick_win(self):
        """Check if certification can be completed quickly (under 10 hours)"""
        return self.duration_hours and self.duration_hours <= 10
    
    def __repr__(self):
        return f"<FreeCertification {self.title} by {self.provider}>"


class UserCertificationProgress(db.Model):
    """Track student progress through free certifications"""
    __tablename__ = 'user_certification_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    certification_id = db.Column(db.Integer, db.ForeignKey('free_certifications.id'), nullable=False)
    
    # Progress Tracking
    status = db.Column(db.String(50), default='not_started')  # not_started, in_progress, completed, abandoned
    progress_percentage = db.Column(db.Integer, default=0)
    
    # Timestamps
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Certification Results
    certificate_issued = db.Column(db.Boolean, default=False)
    certificate_url = db.Column(db.String(500))  # Link to earned certificate
    certificate_id = db.Column(db.String(255))  # Certificate verification ID
    score = db.Column(db.Integer)  # If certification has scoring
    
    # Engagement
    time_spent_hours = db.Column(db.Float, default=0.0)
    modules_completed = db.Column(db.Integer, default=0)
    total_modules = db.Column(db.Integer)
    
    # User Feedback
    rating = db.Column(db.Integer)  # 1-5 stars
    review = db.Column(db.Text)
    would_recommend = db.Column(db.Boolean)
    
    # Resume Integration
    added_to_resume = db.Column(db.Boolean, default=False)
    added_to_linkedin = db.Column(db.Boolean, default=False)
    shared_with_employers = db.Column(db.Boolean, default=False)
    
    # Reminder Settings
    reminders_enabled = db.Column(db.Boolean, default=True)
    last_reminder_sent = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('certifications', lazy='dynamic'))
    certification = db.relationship('FreeCertification', backref='user_progress')
    
    def calculate_time_remaining(self):
        """Estimate hours remaining based on progress"""
        if not self.certification.duration_hours:
            return None
        total_hours = self.certification.duration_hours
        completed_hours = (self.progress_percentage / 100) * total_hours
        return max(0, total_hours - completed_hours)
    
    def is_stalled(self):
        """Check if user hasn't made progress in 7+ days"""
        if not self.last_activity:
            return False
        days_since_activity = (datetime.utcnow() - self.last_activity).days
        return days_since_activity >= 7 and self.status == 'in_progress'
    
    def days_to_complete(self):
        """Calculate days since enrollment to completion"""
        if not self.completed_at or not self.enrolled_at:
            return None
        return (self.completed_at - self.enrolled_at).days
    
    def __repr__(self):
        return f"<UserCertificationProgress {self.user.email} - {self.certification.title} - {self.status}>"


class CertificationRecommendation(db.Model):
    """AI-recommended certifications based on user profile"""
    __tablename__ = 'certification_recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    certification_id = db.Column(db.Integer, db.ForeignKey('free_certifications.id'), nullable=False)
    
    # Recommendation Details
    recommendation_score = db.Column(db.Float)  # 0-100, how relevant this cert is
    recommendation_reason = db.Column(db.Text)  # Why this cert was recommended
    
    # Context
    based_on = db.Column(db.JSON)  # Array of factors: major, career goals, resume gaps, etc.
    priority = db.Column(db.String(20))  # high, medium, low
    
    # Impact Prediction
    estimated_salary_boost = db.Column(db.String(50))  # "$5K-$10K", "10-15%", etc.
    job_match_improvement = db.Column(db.Integer)  # Percentage improvement in job matching
    skills_gap_filled = db.Column(db.JSON)  # Array of skills this cert addresses
    
    # Status
    viewed = db.Column(db.Boolean, default=False)
    enrolled = db.Column(db.Boolean, default=False)
    dismissed = db.Column(db.Boolean, default=False)
    
    # Timestamps
    recommended_at = db.Column(db.DateTime, default=datetime.utcnow)
    viewed_at = db.Column(db.DateTime)
    enrolled_at = db.Column(db.DateTime)
    dismissed_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('certification_recommendations', lazy='dynamic'))
    certification = db.relationship('FreeCertification')
    
    def is_urgent(self):
        """Check if this cert should be completed soon (job deadline, etc.)"""
        return self.priority == 'high' and not self.enrolled
    
    def __repr__(self):
        return f"<CertificationRecommendation {self.certification.title} for {self.user.email}>"


class CertificationPathway(db.Model):
    """Curated learning paths (sequences of certifications)"""
    __tablename__ = 'certification_pathways'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Pathway Details
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))  # Technology, Marketing, Business, etc.
    
    # Target Audience
    target_career = db.Column(db.String(255))  # "Software Developer", "Digital Marketer", etc.
    target_salary_range = db.Column(db.String(100))  # "$50K-$70K", "$70K-$90K", etc.
    difficulty_level = db.Column(db.String(50))  # beginner, intermediate, advanced
    
    # Pathway Structure
    certification_sequence = db.Column(db.JSON)  # Ordered array of certification IDs
    total_duration_hours = db.Column(db.Integer)
    total_certifications = db.Column(db.Integer)
    
    # Value Indicators
    completion_rate = db.Column(db.Float)  # Percentage of users who complete full pathway
    average_salary_after = db.Column(db.Integer)  # Average salary of completers
    job_placement_rate = db.Column(db.Float)  # Percentage who get relevant job
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    verified_by_career_services = db.Column(db.Boolean, default=False)
    
    # Engagement
    enrollments_count = db.Column(db.Integer, default=0)
    completions_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_certifications(self):
        """Get ordered list of certifications in this pathway"""
        if not self.certification_sequence:
            return []
        return FreeCertification.query.filter(
            FreeCertification.id.in_(self.certification_sequence)
        ).all()
    
    def __repr__(self):
        return f"<CertificationPathway {self.title}>"


class UserPathwayProgress(db.Model):
    """Track student progress through certification pathways"""
    __tablename__ = 'user_pathway_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pathway_id = db.Column(db.Integer, db.ForeignKey('certification_pathways.id'), nullable=False)
    
    # Progress
    status = db.Column(db.String(50), default='in_progress')  # in_progress, completed, abandoned
    certifications_completed = db.Column(db.Integer, default=0)
    current_certification_id = db.Column(db.Integer, db.ForeignKey('free_certifications.id'))
    progress_percentage = db.Column(db.Integer, default=0)
    
    # Timestamps
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    estimated_completion_date = db.Column(db.DateTime)
    
    # Outcomes
    got_job = db.Column(db.Boolean)
    salary_before = db.Column(db.Integer)
    salary_after = db.Column(db.Integer)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('pathway_progress', lazy='dynamic'))
    pathway = db.relationship('CertificationPathway')
    current_certification = db.relationship('FreeCertification')
    
    def calculate_salary_increase(self):
        """Calculate salary increase from pathway completion"""
        if self.salary_before and self.salary_after:
            increase = self.salary_after - self.salary_before
            percentage = (increase / self.salary_before) * 100
            return {'amount': increase, 'percentage': percentage}
        return None
    
    def __repr__(self):
        return f"<UserPathwayProgress {self.user.email} - {self.pathway.title}>"

