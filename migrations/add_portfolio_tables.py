"""
Migration: Add Portfolio Tables
Creates tables for professional portfolios, experiences, projects, awards, and skills
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from extensions import db
from sqlalchemy import text

def upgrade():
    """Create portfolio tables"""
    
    with db.engine.connect() as conn:
        # Create portfolios table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS portfolios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                slug VARCHAR(120) NOT NULL UNIQUE,
                headline VARCHAR(255),
                about TEXT,
                profile_image VARCHAR(512),
                phone VARCHAR(20),
                email VARCHAR(255),
                linkedin_url VARCHAR(512),
                github_url VARCHAR(512),
                twitter_url VARCHAR(512),
                website_url VARCHAR(512),
                resume_url VARCHAR(512),
                is_public BOOLEAN DEFAULT 1,
                theme VARCHAR(50) DEFAULT 'light',
                custom_css TEXT,
                views INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """))
        
        # Create portfolio_experiences table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS portfolio_experiences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                title VARCHAR(255) NOT NULL,
                company VARCHAR(255) NOT NULL,
                location VARCHAR(255),
                start_date DATE NOT NULL,
                end_date DATE,
                description TEXT,
                bullets TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
            );
        """))
        
        # Create portfolio_projects table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS portfolio_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                title VARCHAR(255) NOT NULL,
                subtitle VARCHAR(255),
                description TEXT,
                date VARCHAR(100),
                impact TEXT,
                project_url VARCHAR(512),
                github_url VARCHAR(512),
                demo_url VARCHAR(512),
                image_url VARCHAR(512),
                tags TEXT,
                display_order INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
            );
        """))
        
        # Create portfolio_awards table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS portfolio_awards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                date DATE,
                issuer VARCHAR(255),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
            );
        """))
        
        # Create portfolio_skills table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS portfolio_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                name VARCHAR(100) NOT NULL,
                category VARCHAR(100),
                proficiency INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
            );
        """))
        
        # Create indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_portfolios_slug ON portfolios(slug);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_portfolios_user_id ON portfolios(user_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_portfolio_experiences_portfolio_id ON portfolio_experiences(portfolio_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_portfolio_projects_portfolio_id ON portfolio_projects(portfolio_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_portfolio_awards_portfolio_id ON portfolio_awards(portfolio_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_portfolio_skills_portfolio_id ON portfolio_skills(portfolio_id);"))
        
        conn.commit()
    
    print("Portfolio tables created successfully!")

def downgrade():
    """Drop portfolio tables"""
    with db.engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS portfolio_skills CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS portfolio_awards CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS portfolio_projects CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS portfolio_experiences CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS portfolios CASCADE;"))
        conn.commit()
    
    print("✅ Portfolio tables dropped successfully!")

if __name__ == "__main__":
    from app_pro import app
    
    with app.app_context():
        print("Running portfolio tables migration...")
        upgrade()
        print("Migration complete!")
