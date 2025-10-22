# ============================================================
# PittState-Connect | Flask Environment Bootstrap (.flaskenv)
# ============================================================

# ------------------------------------------------------------
# CORE APPLICATION ENTRY
# ------------------------------------------------------------
FLASK_APP=app_pro.py
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=10000
FLASK_ENV=development
DEBUG=True

# ------------------------------------------------------------
# LOGGING / VISIBILITY
# ------------------------------------------------------------
LOG_LEVEL=debug
WERKZEUG_RUN_MAIN=true
FLASK_DEBUG=1

# ------------------------------------------------------------
# AUTO RELOAD & PERFORMANCE
# ------------------------------------------------------------
FLASK_RUN_RELOAD=True
FLASK_RUN_EXTRA_FILES=templates/,static/,blueprints/

# ------------------------------------------------------------
# BRANDING / IDENTITY
# ------------------------------------------------------------
APP_NAME=PittState-Connect
UNIVERSITY_NAME=Pittsburg State University
TAGLINE=Connecting Students, Alumni, and Employers
THEME_COLOR_PRIMARY=#A6192E
THEME_COLOR_SECONDARY=#FFB81C
THEME_COLOR_ACCENT=#F2F2F2

# ------------------------------------------------------------
# DATABASE & STORAGE
# ------------------------------------------------------------
DATABASE_URL=sqlite:///pittstate_connect_local.db
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216     # 16 MB

# ------------------------------------------------------------
# EMAIL / SENDGRID MOCK
# ------------------------------------------------------------
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=apikey
MAIL_PASSWORD=your_sendgrid_api_key_here
MAIL_DEFAULT_SENDER=no-reply@pittstate-connect.local

# ------------------------------------------------------------
# SMART FEATURES / AI
# ------------------------------------------------------------
OPENAI_API_KEY=your_openai_api_key_here
AI_HELPER_ENABLED=True
AI_SMART_MATCH_ENABLED=True
AI_MODEL=gpt-4o-mini
AI_MAX_TOKENS=1500
AI_TEMPERATURE=0.4
AI_LOGGING_ENABLED=True
AI_ANALYTICS_MODE=True

# ------------------------------------------------------------
# SCHOLARSHIP HUB (ALL PHASE 2+ FEATURES)
# ------------------------------------------------------------
SCHOLARSHIP_HUB_ENABLED=True
SCHOLARSHIP_PROGRESS_METER=True
SCHOLARSHIP_AUTO_REMINDERS=True
SCHOLARSHIP_DEADLINE_TRACKER=True
SCHOLARSHIP_ESSAY_LIBRARY=True
SCHOLARSHIP_FACULTY_RECOMMENDATIONS=True
SCHOLARSHIP_PEER_MENTOR_SYSTEM=True
SCHOLARSHIP_DONOR_PORTAL=True
SCHOLARSHIP_IMPACT_STORIES=True
SCHOLARSHIP_ANALYTICS_DASHBOARD=True
SCHOLARSHIP_COST_TO_COMPLETION=True
SCHOLARSHIP_FINANCIAL_LITERACY_HUB=True
SCHOLARSHIP_FUNDING_TIMELINE=True

# ------------------------------------------------------------
# COMMUNITY & MENTORSHIP
# ------------------------------------------------------------
MENTORSHIP_PROGRAM_ENABLED=True
ALUMNI_PORTAL_ENABLED=True
DEPARTMENT_PAGES_ENABLED=True
MESSAGING_ENABLED=True
EVENTS_ENABLED=True
GROUPS_AND_ORGANIZATIONS=True
NOTIFICATIONS_ENABLED=True

# ------------------------------------------------------------
# CAREERS / EMPLOYERS / DONORS
# ------------------------------------------------------------
CAREERS_BOARD_ENABLED=True
EMPLOYER_SPONSORSHIPS_ENABLED=True
EMPLOYER_RECOMMENDATIONS_ENABLED=True
DONOR_PORTAL_ENABLED=True
DONOR_ANALYTICS_ENABLED=True
DONOR_LEADERBOARD=True

# ------------------------------------------------------------
# ANALYTICS / ENGAGEMENT / GAMIFICATION
# ------------------------------------------------------------
LEADERBOARD_ENABLED=True
BADGES_ENABLED=True
USER_ANALYTICS_ENABLED=True
USER_ENGAGEMENT_TRACKING=True
INSIGHTS_DASHBOARD=True
INSIGHTS_TIMELINE=True

# ------------------------------------------------------------
# FINANCIAL TOOLS
# ------------------------------------------------------------
FINANCIAL_LITERACY_HUB=True
COST_TO_COMPLETION_DASHBOARD=True
FUNDING_JOURNEY_TIMELINE=True
FINANCIAL_AID_ANALYTICS=True

# ------------------------------------------------------------
# LOCALHOST DEPLOYMENT PARITY (Render Mirror)
# ------------------------------------------------------------
PORT=10000
RENDER_EXTERNAL_HOSTNAME=localhost:10000
SESSION_COOKIE_SECURE=False
SESSION_COOKIE_HTTPONLY=True
PERMANENT_SESSION_LIFETIME=604800

# ------------------------------------------------------------
# SAFETY / DEBUG OVERRIDES
# ------------------------------------------------------------
SQLALCHEMY_TRACK_MODIFICATIONS=False
TESTING=False
