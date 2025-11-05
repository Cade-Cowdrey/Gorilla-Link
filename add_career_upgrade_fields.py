"""
Migration to add career upgrade fields for recent graduates
Adds experience_level and salary_range to Job model
"""
from app_pro import app, db
from models import Job

def add_career_upgrade_fields():
    """Add new fields to Job model for career progression tracking"""
    with app.app_context():
        # Check if columns already exist
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('jobs')]
        
        if 'experience_level' not in columns:
            print("Adding experience_level column...")
            with db.engine.connect() as conn:
                conn.execute(db.text("""
                    ALTER TABLE jobs 
                    ADD COLUMN experience_level VARCHAR(50) DEFAULT 'entry'
                """))
                conn.commit()
            print("✓ Added experience_level column")
        
        if 'salary_min' not in columns:
            print("Adding salary_min column...")
            with db.engine.connect() as conn:
                conn.execute(db.text("""
                    ALTER TABLE jobs 
                    ADD COLUMN salary_min INTEGER
                """))
                conn.commit()
            print("✓ Added salary_min column")
        
        if 'salary_max' not in columns:
            print("Adding salary_max column...")
            with db.engine.connect() as conn:
                conn.execute(db.text("""
                    ALTER TABLE jobs 
                    ADD COLUMN salary_max INTEGER
                """))
                conn.commit()
            print("✓ Added salary_max column")
        
        if 'years_experience_required' not in columns:
            print("Adding years_experience_required column...")
            with db.engine.connect() as conn:
                conn.execute(db.text("""
                    ALTER TABLE jobs 
                    ADD COLUMN years_experience_required VARCHAR(20)
                """))
                conn.commit()
            print("✓ Added years_experience_required column")
        
        print("\n✅ Career upgrade fields added successfully!")
        print("\nExperience levels: entry, mid, senior, executive")
        print("Years experience: 0-1, 1-3, 3-5, 5-10, 10+")

if __name__ == "__main__":
    add_career_upgrade_fields()
