"""
Scholarship Scraper Configuration
Set your API keys and settings here
"""

# =============================================================================
# API KEYS (Keep these secret!)
# =============================================================================

# Scholarships.com API
# Get your key at: https://www.scholarships.com/api
SCHOLARSHIPS_COM_API_KEY = ""  # Leave empty if not available

# Fastweb API
# Contact Fastweb for institutional API access
FASTWEB_API_KEY = ""  # Leave empty if not available

# Going Merry API
# Get your key at: https://www.goingmerry.com/api
GOING_MERRY_API_KEY = ""  # Leave empty if not available

# =============================================================================
# SCRAPER SETTINGS
# =============================================================================

# Automatically deactivate expired scholarships
AUTO_DEACTIVATE_EXPIRED = True

# Number of days before deadline to show "Deadline Soon" warning
DEADLINE_WARNING_DAYS = 14

# Number of days to extend rolling scholarship deadlines
ROLLING_DEADLINE_EXTENSION_DAYS = 180

# Minimum scholarship amount to include (set to 0 for all)
MIN_SCHOLARSHIP_AMOUNT = 500

# Maximum scholarship amount to include (set to None for all)
MAX_SCHOLARSHIP_AMOUNT = None

# Categories to include (empty list = all categories)
INCLUDE_CATEGORIES = []  # e.g., ['STEM', 'Healthcare', 'Business']

# Categories to exclude
EXCLUDE_CATEGORIES = []

# =============================================================================
# UPDATE SCHEDULE
# =============================================================================

# How often to run full updates (in days)
FULL_UPDATE_FREQUENCY_DAYS = 7

# How often to check for expired scholarships (in hours)
EXPIRATION_CHECK_FREQUENCY_HOURS = 24

# =============================================================================
# LOGGING
# =============================================================================

# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = "INFO"

# Log file location
LOG_FILE = "scholarship_updates.log"

# Keep logs for how many days
LOG_RETENTION_DAYS = 30

# =============================================================================
# NOTIFICATION SETTINGS (Future Feature)
# =============================================================================

# Send email notifications on update
SEND_EMAIL_NOTIFICATIONS = False

# Email addresses to notify
NOTIFICATION_EMAILS = []

# Send notifications for these events
NOTIFY_ON_NEW_SCHOLARSHIPS = True
NOTIFY_ON_EXPIRING_SOON = True
NOTIFY_ON_ERRORS = True

# =============================================================================
# DATABASE SETTINGS
# =============================================================================

# Backup database before major updates
BACKUP_BEFORE_UPDATE = True

# Keep only active scholarships in main queries
HIDE_EXPIRED_FROM_STUDENTS = True

# =============================================================================
# SCHOLARSHIP SOURCES
# =============================================================================

# Which sources to fetch from
FETCH_FROM_APIS = True
FETCH_FROM_MANUAL_CURATION = True
FETCH_FROM_WEB_SCRAPING = False  # Requires permission

# =============================================================================
# CUSTOM SCHOLARSHIP SOURCES
# =============================================================================

# Add your own scholarship sources here
# Format: {'name': 'Source Name', 'url': 'https://...', 'parser': 'function_name'}
CUSTOM_SOURCES = [
    # Example:
    # {
    #     'name': 'University Foundation',
    #     'url': 'https://foundation.example.edu/scholarships',
    #     'parser': 'parse_university_scholarships'
    # }
]

# =============================================================================
# INSTRUCTIONS
# =============================================================================
"""
TO USE THIS CONFIGURATION:

1. Set as Environment Variables (RECOMMENDED for production):
   export SCHOLARSHIPS_COM_API_KEY="your-key-here"
   export FASTWEB_API_KEY="your-key-here"
   export GOING_MERRY_API_KEY="your-key-here"

2. Or set in this file (for development only - don't commit to git!):
   SCHOLARSHIPS_COM_API_KEY = "your-key-here"

3. Or use a .env file:
   Create a file named .env in the project root:
   SCHOLARSHIPS_COM_API_KEY=your-key-here
   FASTWEB_API_KEY=your-key-here
   GOING_MERRY_API_KEY=your-key-here

IMPORTANT: Never commit API keys to version control!
Add .env to your .gitignore file.
"""
