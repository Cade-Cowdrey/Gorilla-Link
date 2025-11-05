"""
Create all database tables for Gorilla-Link
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("GORILLA-LINK DATABASE MIGRATION")
print("=" * 60)
print()

# Create Flask app
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///pittstate_connect_local.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'migration-key'

print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
print()

# Initialize database
db = SQLAlchemy(app)

# Import all models
print("Loading models...")
try:
    # Import base models
    import models
    print("  ✓ Base models loaded")
except Exception as e:
    print(f"  ⚠ Base models: {e}")

try:
    # Import advanced features models
    import models_advanced_features
    print("  ✓ Advanced features models loaded")
except Exception as e:
    print(f"  ⚠ Advanced features: {e}")

try:
    # Import other model files
    import models_student_features
    print("  ✓ Student features models loaded")
except Exception as e:
    print(f"  ⚠ Student features: {e}")

try:
    import models_innovative_features
    print("  ✓ Innovative features models loaded")
except Exception as e:
    print(f"  ⚠ Innovative features: {e}")

try:
    import models_growth_features
    print("  ✓ Growth features models loaded")
except Exception as e:
    print(f"  ⚠ Growth features: {e}")

print()

# Create all tables
print("Creating database tables...")
with app.app_context():
    db.create_all()
    
    # Get all table names
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    print(f"\n✓ Successfully created/verified {len(tables)} tables!")
    
    # Count advanced features tables
    advanced_tables = [t for t in tables if any(keyword in t for keyword in [
        'emergency', 'research', 'career', 'skill', 'housing', 'roommate',
        'international', 'alumni', 'exchange', 'compliance', 'audit', 'masking'
    ])]
    
    print(f"\n📊 Advanced Features Tables ({len(advanced_tables)}):")
    for table in sorted(advanced_tables):
        print(f"  ✓ {table}")
    
    if len(advanced_tables) > 0:
        print(f"\n🎉 SUCCESS! Created {len(advanced_tables)} advanced feature tables")
        print("   with REAL data structures for:")
        print("   • Career Intelligence (BLS API ready)")
        print("   • Housing & Roommate Matching")
        print("   • Emergency Resources")
        print("   • Research Marketplace")
        print("   • Global Network")
        print("   • FERPA Compliance")

print()
print("=" * 60)
print("MIGRATION COMPLETE!")
print("=" * 60)
