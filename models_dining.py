"""
Dining Hall Models - Real-time food reviews and ratings
"""
from extensions import db
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

class DiningLocation(db.Model):
    """PSU Dining locations (Café, Food Court, etc.)"""
    __tablename__ = 'dining_locations'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(255))  # Building location
    description = db.Column(db.Text)
    
    # Hours of operation (JSON: {monday: {open: '07:00', close: '21:00'}, ...})
    hours = db.Column(JSONB)
    
    accepts_meal_plan = db.Column(db.Boolean, default=True)
    cuisine_types = db.Column(ARRAY(db.String))  # ['American', 'Pizza', 'Asian']
    
    # Contact & Info
    phone = db.Column(db.String(20))
    website = db.Column(db.String(512))
    
    # Stats
    average_rating = db.Column(db.Float, default=0.0)
    total_reviews = db.Column(db.Integer, default=0)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    reviews = db.relationship('MealReview', back_populates='dining_location', lazy='dynamic')
    menu_items = db.relationship('MenuItem', back_populates='location', lazy='dynamic')
    wait_times = db.relationship('WaitTimeReport', back_populates='location', lazy='dynamic')
    
    def __repr__(self):
        return f'<DiningLocation {self.name}>'
    
    def is_open_now(self):
        """Check if location is currently open"""
        from datetime import datetime
        if not self.hours:
            return False
        
        now = datetime.now()
        day = now.strftime('%A').lower()
        
        if day not in self.hours:
            return False
        
        hours_today = self.hours[day]
        if not hours_today or 'open' not in hours_today:
            return False
        
        try:
            open_time = datetime.strptime(hours_today['open'], '%H:%M').time()
            close_time = datetime.strptime(hours_today['close'], '%H:%M').time()
            current_time = now.time()
            
            return open_time <= current_time <= close_time
        except:
            return False
    
    def get_current_wait_time(self):
        """Get most recent wait time report (within last 30 minutes)"""
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(minutes=30)
        
        recent_report = self.wait_times.filter(
            WaitTimeReport.reported_at >= cutoff
        ).order_by(WaitTimeReport.reported_at.desc()).first()
        
        if recent_report:
            return recent_report.wait_minutes
        return None


class MenuItem(db.Model):
    """Individual menu items at dining locations"""
    __tablename__ = 'menu_items'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('dining_locations.id'), nullable=False)
    
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))  # Entree, Side, Dessert, Beverage
    
    # Pricing
    price = db.Column(db.Float)
    meal_plan_swipes = db.Column(db.Integer)  # How many swipes it costs
    
    # Dietary information
    dietary_tags = db.Column(ARRAY(db.String))  # vegetarian, vegan, gluten_free, etc.
    allergens = db.Column(ARRAY(db.String))  # dairy, nuts, soy, etc.
    calories = db.Column(db.Integer)
    
    # Availability
    available_days = db.Column(ARRAY(db.String))  # ['monday', 'wednesday', 'friday']
    is_special = db.Column(db.Boolean, default=False)  # Limited time offering
    available_until = db.Column(db.DateTime)  # For limited items
    
    # Stats
    average_rating = db.Column(db.Float, default=0.0)
    total_reviews = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    location = db.relationship('DiningLocation', back_populates='menu_items')
    reviews = db.relationship('MealReview', back_populates='menu_item', lazy='dynamic')
    
    def __repr__(self):
        return f'<MenuItem {self.name}>'


class MealReview(db.Model):
    """Student reviews of meals/menu items"""
    __tablename__ = 'meal_reviews'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    dining_location_id = db.Column(db.Integer, db.ForeignKey('dining_locations.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'))  # Optional - can review location generally
    
    # Review content
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    review_text = db.Column(db.Text)
    
    # Photos
    photo_urls = db.Column(ARRAY(db.String))  # Multiple photos allowed
    
    # Meal details
    meal_type = db.Column(db.String(20))  # breakfast, lunch, dinner, snack
    
    # Engagement
    helpful_count = db.Column(db.Integer, default=0)
    reported_count = db.Column(db.Integer, default=0)
    
    # Moderation
    is_verified = db.Column(db.Boolean, default=False)  # Student verified they ate there
    is_hidden = db.Column(db.Boolean, default=False)  # Moderated/flagged
    
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = db.relationship('User', backref='meal_reviews')
    dining_location = db.relationship('DiningLocation', back_populates='reviews')
    menu_item = db.relationship('MenuItem', back_populates='reviews')
    helpful_votes = db.relationship('ReviewHelpful', back_populates='review', lazy='dynamic')
    
    def __repr__(self):
        return f'<MealReview {self.id} - {self.rating} stars>'


class ReviewHelpful(db.Model):
    """Track which users found reviews helpful"""
    __tablename__ = 'review_helpful'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('meal_reviews.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_helpful = db.Column(db.Boolean, default=True)  # True = helpful, False = not helpful
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    review = db.relationship('MealReview', back_populates='helpful_votes')
    user = db.relationship('User', backref='helpful_votes')
    
    __table_args__ = (
        db.UniqueConstraint('review_id', 'user_id', name='unique_review_user_helpful'),
        {'extend_existing': True}
    )


class WaitTimeReport(db.Model):
    """Crowdsourced wait time reports"""
    __tablename__ = 'wait_time_reports'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('dining_locations.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    wait_minutes = db.Column(db.Integer, nullable=False)  # Estimated wait time
    crowd_level = db.Column(db.String(20))  # empty, light, moderate, busy, packed
    
    reported_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    location = db.relationship('DiningLocation', back_populates='wait_times')
    user = db.relationship('User', backref='wait_time_reports')
    
    def __repr__(self):
        return f'<WaitTimeReport {self.location_id} - {self.wait_minutes}min>'


class DailySpecial(db.Model):
    """Daily specials and featured items"""
    __tablename__ = 'daily_specials'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('dining_locations.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'))
    
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    special_date = db.Column(db.Date, nullable=False)
    
    # Promotion details
    discount_percent = db.Column(db.Float)  # e.g., 20% off
    special_price = db.Column(db.Float)
    
    photo_url = db.Column(db.String(512))
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    location = db.relationship('DiningLocation', backref='specials')
    menu_item = db.relationship('MenuItem', backref='specials')
    
    def __repr__(self):
        return f'<DailySpecial {self.title}>'


class MealPlanBalance(db.Model):
    """Track student meal plan balances (if PSU provides API access)"""
    __tablename__ = 'meal_plan_balances'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Balance info
    meal_swipes_remaining = db.Column(db.Integer)
    dining_dollars_remaining = db.Column(db.Float)
    flex_dollars_remaining = db.Column(db.Float)
    
    # Plan details
    plan_name = db.Column(db.String(100))  # e.g., "Unlimited", "Block 150"
    plan_type = db.Column(db.String(50))
    semester = db.Column(db.String(20))  # "Fall 2025"
    
    # Spending analytics
    average_daily_spending = db.Column(db.Float)
    projected_end_date = db.Column(db.Date)  # When balance will run out
    
    last_transaction = db.Column(db.DateTime)
    last_synced = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    user = db.relationship('User', backref='meal_plan_balance')
    
    def __repr__(self):
        return f'<MealPlanBalance User {self.user_id}>'
    
    def calculate_projection(self):
        """Calculate when balance will run out at current rate"""
        if not self.average_daily_spending or not self.dining_dollars_remaining:
            return None
        
        from datetime import datetime, timedelta
        days_remaining = self.dining_dollars_remaining / self.average_daily_spending
        return datetime.now().date() + timedelta(days=days_remaining)
