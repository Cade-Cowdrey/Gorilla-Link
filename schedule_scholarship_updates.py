"""
Automated Scholarship Update Scheduler
Runs the scholarship scraper on a schedule to keep scholarships current
Can be run as a cron job or scheduled task
"""

import schedule
import time
from datetime import datetime
import logging
from scholarship_scraper import ScholarshipScraper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scholarship_updates.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def run_scholarship_update():
    """Run the scholarship scraper"""
    logger.info("=" * 60)
    logger.info("Starting scheduled scholarship update")
    logger.info("=" * 60)
    
    try:
        scraper = ScholarshipScraper()
        scraper.run(skip_apis=False)  # Set to True to skip API calls
        
        logger.info("Scholarship update completed successfully")
    except Exception as e:
        logger.error(f"Error during scholarship update: {e}", exc_info=True)


def schedule_updates():
    """Setup the update schedule"""
    logger.info("🕐 Scholarship Update Scheduler Started")
    logger.info("=" * 60)
    logger.info("Schedule:")
    logger.info("  - Daily: Deactivate expired scholarships (2:00 AM)")
    logger.info("  - Weekly: Full update with APIs (Sunday 3:00 AM)")
    logger.info("  - Monthly: Complete refresh (1st of month, 4:00 AM)")
    logger.info("=" * 60)
    
    # Daily: Just deactivate expired (lightweight)
    schedule.every().day.at("02:00").do(deactivate_expired_only)
    
    # Weekly: Full update including APIs (Sunday at 3 AM)
    schedule.every().sunday.at("03:00").do(run_scholarship_update)
    
    # Monthly: Complete refresh (1st of month at 4 AM)
    schedule.every().month.do(run_complete_refresh)
    
    # Keep the scheduler running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


def deactivate_expired_only():
    """Quick daily check to deactivate expired scholarships"""
    logger.info("Running daily expiration check...")
    try:
        scraper = ScholarshipScraper()
        scraper.deactivate_expired_scholarships()
        scraper.reactivate_rolling_scholarships()
        logger.info("Daily expiration check complete")
    except Exception as e:
        logger.error(f"Error during expiration check: {e}", exc_info=True)


def run_complete_refresh():
    """Complete monthly refresh"""
    logger.info("Running complete monthly refresh...")
    try:
        scraper = ScholarshipScraper()
        scraper.run(skip_apis=False)
        logger.info("Monthly refresh complete")
    except Exception as e:
        logger.error(f"Error during monthly refresh: {e}", exc_info=True)


if __name__ == "__main__":
    import sys
    
    if "--now" in sys.argv:
        # Run immediately instead of scheduling
        logger.info("Running scholarship update immediately...")
        run_scholarship_update()
    elif "--expired-only" in sys.argv:
        # Just check for expired scholarships
        logger.info("Checking for expired scholarships only...")
        deactivate_expired_only()
    else:
        # Start the scheduler
        schedule_updates()
