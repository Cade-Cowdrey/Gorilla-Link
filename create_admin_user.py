"""
Create an admin user for testing login
Run this on your production server to create a test account
"""
from app_pro import app
from extensions import db
from models import User, Role

def create_admin_user():
    with app.app_context():
        print("=" * 60)
        print("🔐 Creating Admin User")
        print("=" * 60)
        
        # Check if user table exists
        try:
            existing_user = User.query.filter_by(email='admin@pittstate.edu').first()
            if existing_user:
                print("\n⚠️  Admin user already exists!")
                print(f"   Email: admin@pittstate.edu")
                print(f"   Username: {existing_user.username}")
                return
        except Exception as e:
            print(f"\n⚠️  User table may not exist: {e}")
            print("   Creating tables...")
            db.create_all()
        
        # Get or create student role
        try:
            student_role = Role.query.filter_by(name='student').first()
            if not student_role:
                student_role = Role(name='student', description='Student')
                db.session.add(student_role)
                db.session.commit()
        except Exception as e:
            print(f"⚠️  Could not create role: {e}")
            student_role = None
        
        # Create admin user
        try:
            admin = User(
                username='admin',
                email='admin@pittstate.edu',
                full_name='Admin User',
                is_active=True,
                role_id=student_role.id if student_role else None
            )
            admin.set_password('admin123')  # Change this password!
            
            db.session.add(admin)
            db.session.commit()
            
            print("\n✅ Admin user created successfully!")
            print("\n📋 Login Credentials:")
            print("   Email: admin@pittstate.edu")
            print("   Password: admin123")
            print("\n⚠️  IMPORTANT: Change this password after first login!")
            print("\n🚀 You can now log in at:")
            print("   https://gorilla-link.onrender.com/auth/login")
            
        except Exception as e:
            print(f"\n❌ Error creating admin user: {e}")
            db.session.rollback()
        
        print("\n" + "=" * 60)

if __name__ == '__main__':
    create_admin_user()
