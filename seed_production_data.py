"""
PittState-Connect Production Seed Data
Initializes feature flags, sample data, and system configurations.
"""

from datetime import datetime, timedelta
from flask import Flask
from extensions import db
from models import User, Role, Department, Scholarship, Event, Job
from models_extended import (
    FeatureFlag, ABTest, DataLineage, BiasMonitoring, 
    DataRetention, NotificationPreference, PushNotificationToken,
    ScholarshipExtended, AlumniProfile, AIConversation, SponsorshipTier
)
from werkzeug.security import generate_password_hash
from loguru import logger
from services.monetization_service import get_monetization_service

def seed_feature_flags():
    """Initialize all production feature flags."""
    
    logger.info("🚩 Seeding feature flags...")
    
    flags = [
        # Core Platform Features
        {
            "name": "alumni_network",
            "description": "Alumni networking and mentorship features",
            "enabled": True,
            "rollout_percentage": 100,
            "target_roles": ["alumni", "student"]
        },
        {
            "name": "employer_portal",
            "description": "Employer job posting and recruiting portal",
            "enabled": True,
            "rollout_percentage": 100,
            "target_roles": ["employer"]
        },
        {
            "name": "ai_assistant",
            "description": "AI-powered chatbot and recommendations",
            "enabled": True,
            "rollout_percentage": 75,
            "target_roles": ["student", "alumni"]
        },
        {
            "name": "scholarship_hub_v2",
            "description": "Enhanced scholarship matching and applications",
            "enabled": True,
            "rollout_percentage": 100
        },
        
        # Analytics & Intelligence
        {
            "name": "predictive_analytics",
            "description": "ML-powered predictions for retention and scholarships",
            "enabled": True,
            "rollout_percentage": 50,
            "target_roles": ["admin", "faculty"]
        },
        {
            "name": "advanced_analytics_dashboard",
            "description": "Real-time analytics with custom reports",
            "enabled": True,
            "rollout_percentage": 100,
            "target_roles": ["admin", "faculty"]
        },
        
        # Communication Suite
        {
            "name": "direct_messaging",
            "description": "Encrypted 1-on-1 and group messaging",
            "enabled": True,
            "rollout_percentage": 100
        },
        {
            "name": "video_calls",
            "description": "Integrated video calling for mentorship",
            "enabled": False,
            "rollout_percentage": 0
        },
        {
            "name": "forums",
            "description": "Topic-based discussion forums",
            "enabled": True,
            "rollout_percentage": 100
        },
        {
            "name": "webinars",
            "description": "Live webinar hosting and attendance",
            "enabled": True,
            "rollout_percentage": 80,
            "target_roles": ["faculty", "admin", "alumni"]
        },
        
        # Security & Compliance
        {
            "name": "two_factor_auth",
            "description": "TOTP-based two-factor authentication",
            "enabled": True,
            "rollout_percentage": 100
        },
        {
            "name": "webauthn",
            "description": "Hardware key authentication (FIDO2)",
            "enabled": True,
            "rollout_percentage": 50,
            "target_roles": ["admin", "faculty"]
        },
        {
            "name": "audit_logging",
            "description": "Comprehensive security audit trails",
            "enabled": True,
            "rollout_percentage": 100,
            "target_roles": ["admin"]
        },
        
        # Mobile & PWA
        {
            "name": "pwa_features",
            "description": "Progressive Web App capabilities",
            "enabled": True,
            "rollout_percentage": 100
        },
        {
            "name": "push_notifications",
            "description": "Browser and mobile push notifications",
            "enabled": True,
            "rollout_percentage": 90
        },
        
        # Monetization
        {
            "name": "premium_subscriptions",
            "description": "Premium features for alumni/employers",
            "enabled": False,
            "rollout_percentage": 0
        },
        {
            "name": "donation_portal",
            "description": "Alumni giving and scholarship funding",
            "enabled": True,
            "rollout_percentage": 100,
            "target_roles": ["alumni", "donor"]
        },
        
        # Education & Credentials
        {
            "name": "digital_badges",
            "description": "Achievement badges and micro-credentials",
            "enabled": True,
            "rollout_percentage": 100
        },
        {
            "name": "blockchain_credentials",
            "description": "Blockchain-verified credentials",
            "enabled": False,
            "rollout_percentage": 0
        },
        
        # Future Vision
        {
            "name": "metaverse_integration",
            "description": "VR/AR campus experiences",
            "enabled": False,
            "rollout_percentage": 0
        }
    ]
    
    count = 0
    for flag_data in flags:
        existing = FeatureFlag.query.filter_by(name=flag_data["name"]).first()
        if not existing:
            flag = FeatureFlag(
                name=flag_data["name"],
                description=flag_data["description"],
                enabled=flag_data["enabled"],
                rollout_percentage=flag_data["rollout_percentage"],
                target_roles=flag_data.get("target_roles"),
                created_at=datetime.utcnow()
            )
            db.session.add(flag)
            count += 1
    
    db.session.commit()
    logger.info(f"✅ Seeded {count} new feature flags (skipped {len(flags) - count} existing)")

def seed_ab_tests():
    """Initialize A/B tests for key features."""
    
    logger.info("🧪 Seeding A/B tests...")
    
    tests = [
        {
            "name": "scholarship_matching_algorithm",
            "description": "Test ML vs rule-based matching",
            "feature_flag_name": "scholarship_hub_v2",
            "variants": {
                "control": {"algorithm": "rule_based", "description": "Traditional keyword matching"},
                "treatment": {"algorithm": "ml_based", "description": "Machine learning recommendations"}
            },
            "traffic_split": {"control": 50, "treatment": 50},
            "metrics": ["application_rate", "acceptance_rate", "user_satisfaction"],
            "start_date": datetime.utcnow(),
            "end_date": datetime.utcnow() + timedelta(days=30)
        },
        {
            "name": "ai_chatbot_ui",
            "description": "Test sidebar vs modal UI",
            "feature_flag_name": "ai_assistant",
            "variants": {
                "sidebar": {"ui": "sidebar", "description": "Persistent sidebar chat"},
                "modal": {"ui": "modal", "description": "Pop-up modal chat"}
            },
            "traffic_split": {"sidebar": 50, "modal": 50},
            "metrics": ["engagement_rate", "completion_rate", "satisfaction_score"],
            "start_date": datetime.utcnow(),
            "end_date": datetime.utcnow() + timedelta(days=21)
        }
    ]
    
    count = 0
    for test_data in tests:
        existing = ABTest.query.filter_by(name=test_data["name"]).first()
        if not existing:
            test = ABTest(
                name=test_data["name"],
                description=test_data["description"],
                feature_flag_name=test_data["feature_flag_name"],
                variants=test_data["variants"],
                traffic_split=test_data["traffic_split"],
                metrics=test_data["metrics"],
                start_date=test_data["start_date"],
                end_date=test_data["end_date"],
                active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(test)
            count += 1
    
    db.session.commit()
    logger.info(f"✅ Seeded {count} new A/B tests")

def seed_sample_users():
    """Create sample users for testing."""
    
    logger.info("👥 Seeding sample users...")
    
    # Create admin role if not exists
    admin_role = Role.query.filter_by(name="admin").first()
    if not admin_role:
        admin_role = Role(name="admin", description="System Administrator")
        db.session.add(admin_role)
        db.session.commit()
    
    # Create sample admin
    admin = User.query.filter_by(email="admin@pittstate.edu").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin@pittstate.edu",
            password_hash=generate_password_hash("AdminPassword123!"),
            role_id=admin_role.id,
            created_at=datetime.utcnow()
        )
        db.session.add(admin)
        logger.info("✅ Created admin user: admin@pittstate.edu")
    
    # Create sample student role
    student_role = Role.query.filter_by(name="student").first()
    if not student_role:
        student_role = Role(name="student", description="Current Student")
        db.session.add(student_role)
        db.session.commit()
    
    # Create sample student
    student = User.query.filter_by(email="student@gus.pittstate.edu").first()
    if not student:
        student = User(
            username="john_doe",
            email="student@gus.pittstate.edu",
            password_hash=generate_password_hash("StudentPass123!"),
            role_id=student_role.id,
            created_at=datetime.utcnow()
        )
        db.session.add(student)
        logger.info("✅ Created student user: student@gus.pittstate.edu")
    
    db.session.commit()

def seed_departments():
    """Create sample departments."""
    
    logger.info("🏢 Seeding departments...")
    
    departments = [
        {"name": "College of Technology", "description": "Engineering Technology, Graphics, and Manufacturing"},
        {"name": "Kelce College of Business", "description": "Business Administration and Economics"},
        {"name": "College of Education", "description": "Teacher Education and Leadership"},
        {"name": "College of Arts & Sciences", "description": "Humanities, Social Sciences, and Natural Sciences"},
        {"name": "College of STEM", "description": "Science, Technology, Engineering, and Mathematics"}
    ]
    
    count = 0
    for dept_data in departments:
        existing = Department.query.filter_by(name=dept_data["name"]).first()
        if not existing:
            dept = Department(
                name=dept_data["name"],
                description=dept_data["description"],
                created_at=datetime.utcnow()
            )
            db.session.add(dept)
            count += 1
    
    db.session.commit()
    logger.info(f"✅ Seeded {count} new departments")

def seed_scholarships():
    """Create sample scholarships."""
    
    logger.info("💰 Seeding scholarships...")
    
    dept_tech = Department.query.filter_by(name="College of Technology").first()
    dept_business = Department.query.filter_by(name="Kelce College of Business").first()
    
    scholarships = [
        {
            "name": "PSU Academic Excellence Scholarship",
            "description": "Merit-based scholarship for high-achieving students",
            "amount": 5000.00,
            "deadline": datetime.utcnow() + timedelta(days=90),
            "requirements": "3.5 GPA minimum, full-time enrollment",
            "department_id": None
        },
        {
            "name": "Technology Innovation Grant",
            "description": "For students pursuing technology degrees",
            "amount": 3000.00,
            "deadline": datetime.utcnow() + timedelta(days=60),
            "requirements": "2.8 GPA minimum, technology major",
            "department_id": dept_tech.id if dept_tech else None
        },
        {
            "name": "Business Leadership Scholarship",
            "description": "For future business leaders",
            "amount": 2500.00,
            "deadline": datetime.utcnow() + timedelta(days=75),
            "requirements": "Business major, leadership experience",
            "department_id": dept_business.id if dept_business else None
        }
    ]
    
    count = 0
    for sch_data in scholarships:
        existing = Scholarship.query.filter_by(name=sch_data["name"]).first()
        if not existing:
            scholarship = Scholarship(
                name=sch_data["name"],
                description=sch_data["description"],
                amount=sch_data["amount"],
                deadline=sch_data["deadline"],
                requirements=sch_data["requirements"],
                department_id=sch_data["department_id"],
                created_at=datetime.utcnow()
            )
            db.session.add(scholarship)
            count += 1
    
    db.session.commit()
    logger.info(f"✅ Seeded {count} new scholarships")

def seed_events():
    """Create sample events."""
    
    logger.info("📅 Seeding events...")
    
    events = [
        {
            "name": "Career Fair Fall 2024",
            "description": "Connect with employers from across Kansas",
            "date": datetime.utcnow() + timedelta(days=45),
            "location": "Overman Student Center",
            "capacity": 500
        },
        {
            "name": "Alumni Homecoming Weekend",
            "description": "Celebrate Gorilla pride with fellow alumni",
            "date": datetime.utcnow() + timedelta(days=30),
            "location": "PSU Campus",
            "capacity": 1000
        },
        {
            "name": "Tech Industry Networking Night",
            "description": "Meet tech professionals and explore opportunities",
            "date": datetime.utcnow() + timedelta(days=20),
            "location": "Kelce College Auditorium",
            "capacity": 150
        }
    ]
    
    count = 0
    for event_data in events:
        existing = Event.query.filter_by(name=event_data["name"]).first()
        if not existing:
            event = Event(
                name=event_data["name"],
                description=event_data["description"],
                date=event_data["date"],
                location=event_data["location"],
                capacity=event_data["capacity"],
                created_at=datetime.utcnow()
            )
            db.session.add(event)
            count += 1
    
    db.session.commit()
    logger.info(f"✅ Seeded {count} new events")

def seed_data_retention_policies():
    """Initialize data retention policies for FERPA/GDPR compliance."""
    
    logger.info("🗂️ Seeding data retention policies...")
    
    policies = [
        {
            "entity_type": "page_view",
            "retention_days": 90,
            "policy": "Analytics data for page views",
            "legal_basis": "Legitimate interest",
            "deletion_method": "hard"
        },
        {
            "entity_type": "api_usage",
            "retention_days": 180,
            "policy": "API usage logs for debugging",
            "legal_basis": "Legitimate interest",
            "deletion_method": "hard"
        },
        {
            "entity_type": "audit_log",
            "retention_days": 2555,  # 7 years for compliance
            "policy": "Security audit logs",
            "legal_basis": "Legal obligation",
            "deletion_method": "soft"
        },
        {
            "entity_type": "user_inactive",
            "retention_days": 1095,  # 3 years
            "policy": "Inactive user accounts",
            "legal_basis": "Consent",
            "deletion_method": "soft"
        }
    ]
    
    count = 0
    for policy_data in policies:
        existing = DataRetention.query.filter_by(entity_type=policy_data["entity_type"]).first()
        if not existing:
            policy = DataRetention(
                entity_type=policy_data["entity_type"],
                retention_days=policy_data["retention_days"],
                policy=policy_data["policy"],
                legal_basis=policy_data["legal_basis"],
                deletion_method=policy_data["deletion_method"],
                active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(policy)
            count += 1
    
    db.session.commit()
    logger.info(f"✅ Seeded {count} new data retention policies")

def seed_sponsorship_tiers():
    """Initialize employer sponsorship tiers."""
    
    logger.info("💼 Seeding employer sponsorship tiers...")
    
    service = get_monetization_service()
    success = service.initialize_sponsorship_tiers()
    
    if success:
        logger.info("✅ Seeded employer sponsorship tiers (free, bronze, silver, gold, platinum)")
    else:
        logger.error("❌ Failed to seed sponsorship tiers")

def seed_all():
    """Run all seed functions."""
    
    logger.info("🌱 Starting production data seeding...")
    
    try:
        seed_feature_flags()
        seed_ab_tests()
        seed_sample_users()
        seed_departments()
        seed_scholarships()
        seed_events()
        seed_data_retention_policies()
        seed_sponsorship_tiers()
        
        logger.info("🎉 Production seed data complete!")
        logger.info("📝 Default credentials:")
        logger.info("   Admin: admin@pittstate.edu / AdminPassword123!")
        logger.info("   Student: student@gus.pittstate.edu / StudentPass123!")
        logger.info("💼 Employer Tiers: Free, Bronze ($499/yr), Silver ($1,499/yr), Gold ($2,999/yr), Platinum ($5,999/yr)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Seed data failed: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    from app_pro import app
    
    with app.app_context():
        seed_all()
