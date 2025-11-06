"""
Migration to add image_url field to DiningLocation model
"""
from flask import Flask
from extensions import db
from config.config_production import ConfigProduction

app = Flask(__name__)
app.config.from_object(ConfigProduction)
db.init_app(app)

with app.app_context():
    # Add image_url column to dining_locations table
    try:
        with db.engine.connect() as conn:
            # Check if column exists first
            result = conn.execute(db.text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='dining_locations' AND column_name='image_url'
            """))
            
            if not result.fetchone():
                conn.execute(db.text("""
                    ALTER TABLE dining_locations 
                    ADD COLUMN image_url VARCHAR(512)
                """))
                conn.commit()
                print("✅ Added image_url column to dining_locations table")
            else:
                print("ℹ️ image_url column already exists")
                
    except Exception as e:
        print(f"❌ Error: {e}")
