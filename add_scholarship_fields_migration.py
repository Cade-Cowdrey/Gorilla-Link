"""
Migration to add new fields to Scholarship model
Run this to update your database schema
"""

from app_pro import create_app
from extensions import db

def run_migration():
    app = create_app()
    with app.app_context():
        print("🔧 Adding new fields to scholarships table...")
        
        try:
            # Add new columns
            db.engine.execute("""
                ALTER TABLE scholarships 
                ADD COLUMN IF NOT EXISTS provider VARCHAR(255),
                ADD COLUMN IF NOT EXISTS url VARCHAR(500),
                ADD COLUMN IF NOT EXISTS category VARCHAR(100),
                ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
            """)
            
            print("✅ Migration complete! New scholarship fields added.")
            print("   - provider: Organization providing the scholarship")
            print("   - url: Application URL")
            print("   - category: Scholarship category (STEM, Healthcare, etc.)")
            print("   - is_active: Whether scholarship is currently available")
            
        except Exception as e:
            print(f"⚠️  Migration error: {e}")
            print("Note: If columns already exist, this is normal.")

if __name__ == "__main__":
    run_migration()
