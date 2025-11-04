"""
Generate database migrations for all production models.
Run this script to create migrations for Feature Flags, Data Governance, and Notification Hub.
"""

import subprocess
import sys
from loguru import logger

def generate_migrations():
    """Generate Flask-Migrate migrations for all new models."""
    
    logger.info("🔄 Generating database migrations...")
    
    try:
        # Generate migration
        result = subprocess.run(
            [
                sys.executable, "-m", "flask", "db", "migrate",
                "-m", "Add production models: feature flags, data governance, notifications"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info("✅ Migration generated successfully:")
        logger.info(result.stdout)
        
        # Apply migration
        logger.info("🔄 Applying migration to database...")
        result = subprocess.run(
            [sys.executable, "-m", "flask", "db", "upgrade"],
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info("✅ Migration applied successfully:")
        logger.info(result.stdout)
        
        logger.info("🎉 Database is now up to date with all production models!")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Migration failed: {e}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = generate_migrations()
    sys.exit(0 if success else 1)
