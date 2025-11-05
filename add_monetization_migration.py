"""
Database migration for Employer Monetization features
Run this to add all monetization tables to your database
"""

from flask import Flask
from extensions import db
from models_monetization import (
    EmployerSubscription, EmployerTier, SubscriptionStatus,
    ScholarshipSponsorship, CareerFairParticipation, 
    JobBoost, EmployerBrandingPackage, RevenueTransaction
)
from datetime import datetime

def add_monetization_tables(app):
    """Add all monetization tables to database"""
    with app.app_context():
        print("Creating monetization tables...")
        
        # Create all tables defined in models_monetization.py
        db.create_all()
        
        print("✅ Successfully created:")
        print("   - employer_subscriptions")
        print("   - scholarship_sponsorships")
        print("   - career_fair_participation")
        print("   - job_boosts")
        print("   - employer_branding_packages")
        print("   - revenue_transactions")
        
        # Create default subscriptions for existing employers
        from models import User  # Import your User model
        
        employers = User.query.filter_by(user_type='employer').all()
        print(f"\n📊 Found {len(employers)} existing employers")
        
        created_count = 0
        for employer in employers:
            # Check if subscription already exists
            existing = EmployerSubscription.query.filter_by(user_id=employer.id).first()
            if not existing:
                subscription = EmployerSubscription(
                    user_id=employer.id,
                    tier=EmployerTier.FREE,
                    status=SubscriptionStatus.ACTIVE,
                    subscription_start_date=datetime.utcnow()
                )
                db.session.add(subscription)
                created_count += 1
        
        if created_count > 0:
            db.session.commit()
            print(f"✅ Created {created_count} FREE tier subscriptions for existing employers")
        else:
            print("✅ All employers already have subscriptions")
        
        print("\n🎉 Monetization database migration complete!")
        print("\n📝 Next steps:")
        print("   1. Set Stripe API keys in environment variables")
        print("   2. Create Stripe products and prices")
        print("   3. Deploy to production")
        print("   4. Start sending emails to employers!")

if __name__ == '__main__':
    # Import your Flask app
    # Adjust this import based on your app structure
    from app import app  # or from app_pro import app
    
    add_monetization_tables(app)
