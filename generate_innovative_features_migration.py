"""
Migration script for innovative features
Creates tables for 8 game-changing features that PSU doesn't have
"""

from app_pro import app
from extensions import db

# Import all innovative feature models
from models_innovative_features import (
    # Rideshare models
    RideShare,
    RideRequest,
    
    # Study groups
    StudyGroup,
    StudyGroupMember,
    
    # Wellness tracker
    WellnessCheckIn,
    WellnessResource,
    
    # Lost & Found
    LostItem,
    
    # Sublease marketplace
    SubleasePosting,
    
    # Parking exchange
    ParkingSpot,
    
    # Tutoring marketplace
    TutorProfile,
    TutoringSession,
    
    # Free stuff board
    FreeStuff
)

def create_tables():
    """Create all innovative feature tables"""
    with app.app_context():
        print("Creating innovative feature tables...")
        
        # Create all tables
        db.create_all()
        
        print("✅ All tables created successfully!")
        print("\nCreated 12 models across 8 features:")
        print("  🚗 Rideshare: RideShare, RideRequest")
        print("  📚 Study Groups: StudyGroup, StudyGroupMember")
        print("  💚 Wellness: WellnessCheckIn, WellnessResource")
        print("  🔑 Lost & Found: LostItem")
        print("  🏠 Sublease: SubleasePosting")
        print("  🅿️ Parking: ParkingSpot")
        print("  👨‍🏫 Tutoring: TutorProfile, TutoringSession")
        print("  🎁 Free Stuff: FreeStuff")
        print("\nNext steps:")
        print("1. Run seed_innovative_features.py to populate sample data")
        print("2. Create templates for each feature")
        print("3. Test all routes")
        print("4. Deploy to production!")

if __name__ == '__main__':
    create_tables()
