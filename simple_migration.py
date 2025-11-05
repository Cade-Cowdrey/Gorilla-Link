"""
Simple database migration - creates tables without loading full app
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set database URL
os.environ['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///pittstate_connect_local.db')

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Create minimal app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///pittstate_connect_local.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import models first
print("Importing models...")
from models_advanced_features import *

# Initialize db
db = SQLAlchemy()
db.init_app(app)

# Create tables
print("\nCreating database tables...")
with app.app_context():
    db.create_all()
    
    # Count tables
    tables = db.metadata.tables.keys()
    print(f"\n✓ Successfully created {len(tables)} tables!")
    
    print("\nTables created:")
    for table in sorted(tables):
        print(f"  - {table}")

print("\n✓ Migration complete!")
