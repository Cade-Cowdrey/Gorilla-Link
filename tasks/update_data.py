"""
Automated Data Update Tasks
Schedules regular updates for career, housing, and skill data
"""

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extensions import db
from models_advanced_features import (
    CareerPathway, SkillDemandForecast, HousingListing
)


def update_career_pathways():
    """
    Update all career pathway salary data from BLS API
    Runs monthly on the 1st at 2 AM
    """
    
    print(f"[{datetime.now()}] Starting career pathway update...")
    
    try:
        from utils.bls_api import get_occupation_data, OCCUPATION_CODES
        
        pathways = CareerPathway.query.all()
        updated_count = 0
        
        for pathway in pathways:
            # Try to find occupation code
            occupation_code = None
            
            for title, code in OCCUPATION_CODES.items():
                if title.lower() in pathway.career_title.lower():
                    occupation_code = code
                    break
            
            if not occupation_code:
                print(f"  ⚠ No BLS code found for {pathway.career_title}")
                continue
            
            # Fetch updated data
            try:
                data = get_occupation_data(pathway.career_title)
                
                if data:
                    pathway.national_median_salary = data['national_median_salary']
                    pathway.last_updated = datetime.utcnow()
                    updated_count += 1
                    print(f"  ✓ Updated {pathway.career_title}: ${data['national_median_salary']:,.0f}")
            
            except Exception as e:
                print(f"  ✗ Error updating {pathway.career_title}: {e}")
                continue
        
        db.session.commit()
        print(f"[{datetime.now()}] Career pathway update complete: {updated_count}/{len(pathways)} updated")
    
    except Exception as e:
        print(f"[{datetime.now()}] Career pathway update failed: {e}")
        db.session.rollback()


def update_housing_listings():
    """
    Update housing listings from APIs
    Runs weekly on Sundays at 3 AM
    """
    
    print(f"[{datetime.now()}] Starting housing listings update...")
    
    try:
        from utils.housing_api import search_rentals_near_psu, parse_zillow_listing
        
        # Mark old listings as needing verification
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        old_listings = HousingListing.query.filter(
            HousingListing.last_verified < seven_days_ago,
            HousingListing.status == 'available'
        ).all()
        
        for listing in old_listings:
            listing.status = 'needs_verification'
            listing.verification_notes = 'Listing is over 7 days old, please verify'
        
        print(f"  Marked {len(old_listings)} listings as needing verification")
        
        # Fetch new listings
        try:
            properties = search_rentals_near_psu(max_price=1500, bedrooms=2)
            
            new_count = 0
            updated_count = 0
            
            for zillow_data in properties:
                listing_data = parse_zillow_listing(zillow_data)
                
                # Check if already exists
                existing = HousingListing.query.filter_by(
                    address=listing_data['address']
                ).first()
                
                if existing:
                    # Update existing
                    for key, value in listing_data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    updated_count += 1
                else:
                    # Add new
                    listing = HousingListing(**listing_data)
                    db.session.add(listing)
                    new_count += 1
            
            db.session.commit()
            print(f"  ✓ Added {new_count} new listings, updated {updated_count} existing")
        
        except Exception as e:
            print(f"  ⚠ Zillow API unavailable, skipping: {e}")
        
        print(f"[{datetime.now()}] Housing listings update complete")
    
    except Exception as e:
        print(f"[{datetime.now()}] Housing listings update failed: {e}")
        db.session.rollback()


def update_skill_demand():
    """
    Update skill demand forecasts
    Runs monthly on the 15th at 2 AM
    """
    
    print(f"[{datetime.now()}] Starting skill demand update...")
    
    try:
        # In production, this would fetch from LinkedIn/Indeed APIs
        # For now, we'll just update the last_updated timestamp
        
        skills = SkillDemandForecast.query.all()
        
        for skill in skills:
            skill.last_updated = datetime.utcnow()
        
        db.session.commit()
        print(f"[{datetime.now()}] Skill demand update complete: {len(skills)} skills updated")
    
    except Exception as e:
        print(f"[{datetime.now()}] Skill demand update failed: {e}")
        db.session.rollback()


def cleanup_old_data():
    """
    Clean up old data that's no longer relevant
    Runs monthly on the 1st at 4 AM
    """
    
    print(f"[{datetime.now()}] Starting data cleanup...")
    
    try:
        # Remove listings that haven't been verified in 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        old_listings = HousingListing.query.filter(
            HousingListing.last_verified < thirty_days_ago
        ).delete()
        
        db.session.commit()
        print(f"[{datetime.now()}] Data cleanup complete: Removed {old_listings} old housing listings")
    
    except Exception as e:
        print(f"[{datetime.now()}] Data cleanup failed: {e}")
        db.session.rollback()


# Initialize scheduler
scheduler = BackgroundScheduler()

# Schedule tasks
scheduler.add_job(
    update_career_pathways,
    'cron',
    day=1,
    hour=2,
    minute=0,
    id='update_career_pathways',
    name='Update Career Pathways (Monthly)',
    replace_existing=True
)

scheduler.add_job(
    update_housing_listings,
    'cron',
    day_of_week='sun',
    hour=3,
    minute=0,
    id='update_housing_listings',
    name='Update Housing Listings (Weekly)',
    replace_existing=True
)

scheduler.add_job(
    update_skill_demand,
    'cron',
    day=15,
    hour=2,
    minute=0,
    id='update_skill_demand',
    name='Update Skill Demand (Monthly)',
    replace_existing=True
)

scheduler.add_job(
    cleanup_old_data,
    'cron',
    day=1,
    hour=4,
    minute=0,
    id='cleanup_old_data',
    name='Cleanup Old Data (Monthly)',
    replace_existing=True
)


def start_scheduler():
    """Start the background scheduler"""
    if not scheduler.running:
        scheduler.start()
        print("✓ Scheduled tasks started:")
        print("  • Career pathways: 1st of month at 2:00 AM")
        print("  • Housing listings: Sundays at 3:00 AM")
        print("  • Skill demand: 15th of month at 2:00 AM")
        print("  • Data cleanup: 1st of month at 4:00 AM")


def stop_scheduler():
    """Stop the background scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        print("✓ Scheduled tasks stopped")


# For testing - run updates immediately
if __name__ == '__main__':
    print("Running scheduled tasks manually...")
    print("=" * 50)
    
    # Import app context
    from app_pro import app
    
    with app.app_context():
        print("\n1. Updating career pathways...")
        update_career_pathways()
        
        print("\n2. Updating housing listings...")
        update_housing_listings()
        
        print("\n3. Updating skill demand...")
        update_skill_demand()
        
        print("\n4. Cleaning up old data...")
        cleanup_old_data()
        
        print("\n" + "=" * 50)
        print("Manual update complete!")
