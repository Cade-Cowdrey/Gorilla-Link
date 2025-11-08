"""
Test login functionality and create a test user
"""
from app_pro import app
from extensions import db
from models import User

def test_login():
    with app.app_context():
        # Ensure tables exist
        db.create_all()
        print("[INFO] Database tables verified/created")
        # Check if any users exist
        user_count = User.query.count()
        print(f"[INFO] Total users in database: {user_count}")
        
        if user_count > 0:
            users = User.query.limit(5).all()
            print("\n[INFO] Sample users:")
            for user in users:
                print(f"  - {user.first_name} {user.last_name} ({user.email}) - Has password: {bool(user.password_hash)}")
        
        # Create a test user if none exist
        test_email = "test@pittstate.edu"
        test_user = User.query.filter_by(email=test_email).first()
        
        if not test_user:
            print(f"\n[INFO] Creating test user...")
            test_user = User(
                first_name="Test",
                last_name="User",
                email=test_email
            )
            test_user.set_password("password123")
            db.session.add(test_user)
            db.session.commit()
            print(f"[SUCCESS] Test user created!")
            print(f"  Email: {test_email}")
            print(f"  Password: password123")
        else:
            print(f"\n[INFO] Test user already exists: {test_email}")
            # Update password to known value
            test_user.set_password("password123")
            db.session.commit()
            print(f"  Password reset to: password123")
        
        # Test password verification
        print(f"\n[INFO] Testing password verification...")
        if test_user.check_password("password123"):
            print("[SUCCESS] Password verification works!")
        else:
            print("[ERROR] Password verification failed!")

if __name__ == "__main__":
    test_login()
