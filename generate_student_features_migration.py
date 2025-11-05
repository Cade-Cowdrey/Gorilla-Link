"""
Database Migration Script for 8 New Student Features
Creates all tables for: Textbook Exchange, Housing Reviews, Student Discounts, 
Grade Explorer, Professor Reviews, Campus Wait Times, Student Events, Course Library

Run with: python generate_student_features_migration.py
"""

from app_pro import app
from extensions import db
from models_student_features import (
    TextbookListing, TextbookInterest, HousingListing, HousingReview,
    StudentDiscount, DiscountUsage, GradeDistribution, ProfessorReview,
    ProfessorProfile, CampusService, ServiceWaitReport, StudentEvent,
    EventRSVP, CourseMaterial, MaterialRating
)

def run_migration():
    """Create all tables for student features"""
    print("\n" + "="*70)
    print("🔧 CREATING DATABASE TABLES FOR STUDENT FEATURES")
    print("="*70 + "\n")
    
    with app.app_context():
        try:
            print("📝 Creating tables...")
            
            # Import models to register them
            # The db.create_all() will create all tables that don't exist
            
            # Create all tables
            db.create_all()
            
            print("\n✅ SUCCESS! All tables created:")
            print("   📚 textbook_listings")
            print("   📚 textbook_interests")
            print("   🏠 housing_listings")
            print("   🏠 housing_reviews")
            print("   💰 student_discounts")
            print("   💰 discount_usage")
            print("   📊 grade_distributions")
            print("   👨‍🏫 professor_reviews")
            print("   👨‍🏫 professor_profiles")
            print("   ⏰ campus_services")
            print("   ⏰ service_wait_reports")
            print("   📅 student_events")
            print("   📅 event_rsvps")
            print("   📁 course_materials")
            print("   📁 material_ratings")
            
            print("\n" + "="*70)
            print("✅ MIGRATION COMPLETE!")
            print("="*70)
            print("\n💡 Next steps:")
            print("   1. Run: python seed_student_features.py")
            print("   2. Start your app and test the features!")
            print("   3. Deploy to production when ready\n")
            
        except Exception as e:
            print(f"\n❌ ERROR during migration: {e}")
            raise


if __name__ == "__main__":
    run_migration()
