# 🔄 Automated Scholarship Updates Setup Guide

## Overview

This guide shows you how to set up automatic scholarship updates that will:
- ✅ Deactivate expired scholarships daily
- ✅ Fetch new scholarships weekly
- ✅ Update deadlines automatically
- ✅ Keep your database current without manual intervention

## Quick Setup Options

### Option 1: Render Cron Jobs (RECOMMENDED for Production)

Render supports cron jobs natively. Add to your `render.yaml`:

```yaml
services:
  # Your existing web service
  - type: web
    name: pittstate-connect
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "gunicorn app_pro:app"
    
  # NEW: Cron job for scholarship updates
  - type: cron
    name: scholarship-updater
    env: python
    schedule: "0 3 * * 0"  # Every Sunday at 3 AM
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python scholarship_scraper.py"
```

Or add via Render Dashboard:
1. Go to your Render dashboard
2. Click "New" → "Cron Job"
3. Connect your GitHub repo
4. Set schedule: `0 3 * * 0` (Sunday 3 AM)
5. Set command: `python scholarship_scraper.py`

### Option 2: GitHub Actions (FREE)

Create `.github/workflows/update-scholarships.yml`:

```yaml
name: Update Scholarships

on:
  schedule:
    # Runs every Sunday at 3 AM UTC
    - cron: '0 3 * * 0'
  workflow_dispatch:  # Allow manual trigger

jobs:
  update:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run scholarship scraper
      env:
        DATABASE_URL: ${{ secrets.DATABASE_URL }}
        SCHOLARSHIPS_COM_API_KEY: ${{ secrets.SCHOLARSHIPS_COM_API_KEY }}
        FASTWEB_API_KEY: ${{ secrets.FASTWEB_API_KEY }}
      run: |
        python scholarship_scraper.py
```

Add secrets in GitHub:
1. Go to repo Settings → Secrets and variables → Actions
2. Add `DATABASE_URL` (your production database URL)
3. Add API keys if you have them

### Option 3: Local Server Cron Job (Linux/Mac)

Edit crontab:
```bash
crontab -e
```

Add these lines:
```bash
# Update scholarships every Sunday at 3 AM
0 3 * * 0 cd /path/to/Gorilla-Link1 && python scholarship_scraper.py

# Check for expired scholarships daily at 2 AM
0 2 * * * cd /path/to/Gorilla-Link1 && python schedule_scholarship_updates.py --expired-only

# Complete refresh on 1st of each month at 4 AM
0 4 1 * * cd /path/to/Gorilla-Link1 && python scholarship_scraper.py
```

### Option 4: Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Name: "Update Scholarships"
4. Trigger: Weekly, Sunday, 3:00 AM
5. Action: Start a program
6. Program: `python.exe`
7. Arguments: `c:\path\to\Gorilla-Link1\scholarship_scraper.py`
8. Start in: `c:\path\to\Gorilla-Link1`

### Option 5: Python Scheduler (Always Running)

Keep a Python process running:

```bash
# Run the scheduler (stays running)
python schedule_scholarship_updates.py

# Or run in background (Linux/Mac)
nohup python schedule_scholarship_updates.py &

# Or use screen/tmux
screen -S scholarship-scheduler
python schedule_scholarship_updates.py
# Press Ctrl+A, then D to detach
```

## Cron Schedule Syntax

```
┌───────────── minute (0-59)
│ ┌─────────── hour (0-23)
│ │ ┌───────── day of month (1-31)
│ │ │ ┌─────── month (1-12)
│ │ │ │ ┌───── day of week (0-6, Sunday=0)
│ │ │ │ │
* * * * *
```

Examples:
- `0 3 * * 0` - Every Sunday at 3 AM
- `0 2 * * *` - Every day at 2 AM
- `0 4 1 * *` - 1st of every month at 4 AM
- `*/30 * * * *` - Every 30 minutes

## Manual Runs

You can also run updates manually anytime:

```bash
# Full update with APIs
python scholarship_scraper.py

# Manual only (skip APIs)
python scholarship_scraper.py --no-apis

# Just check for expired scholarships
python schedule_scholarship_updates.py --expired-only

# Run update immediately (from scheduler)
python schedule_scholarship_updates.py --now
```

## Monitoring Updates

### Check Logs

```bash
# View update logs
cat scholarship_updates.log

# Follow logs in real-time
tail -f scholarship_updates.log

# View last 50 lines
tail -n 50 scholarship_updates.log
```

### Check Database

```bash
# See current statistics
python -c "
from app_pro import create_app
from models import Scholarship
app = create_app()
with app.app_context():
    total = Scholarship.query.count()
    active = Scholarship.query.filter_by(is_active=True).count()
    expired = Scholarship.query.filter_by(is_active=False).count()
    print(f'Total: {total}, Active: {active}, Expired: {expired}')
"
```

### Health Check Endpoint (Optional)

Add to your Flask app:

```python
@app.route('/api/scholarships/health')
def scholarship_health():
    total = Scholarship.query.count()
    active = Scholarship.query.filter_by(is_active=True).count()
    expired = Scholarship.query.filter_by(is_active=False).count()
    
    # Get last update time (from most recent scholarship)
    latest = Scholarship.query.order_by(Scholarship.created_at.desc()).first()
    last_update = latest.created_at if latest else None
    
    return jsonify({
        'status': 'healthy',
        'total_scholarships': total,
        'active_scholarships': active,
        'expired_scholarships': expired,
        'last_update': last_update.isoformat() if last_update else None
    })
```

## Recommended Schedule

For production, we recommend:

| Task | Frequency | Time | Purpose |
|------|-----------|------|---------|
| Expire check | Daily | 2:00 AM | Deactivate past-deadline scholarships |
| Full update | Weekly | Sunday 3:00 AM | Fetch new scholarships from APIs |
| Complete refresh | Monthly | 1st, 4:00 AM | Full data refresh and cleanup |

## API Key Setup

If you have API keys, set them as environment variables:

### Render
1. Go to your service dashboard
2. Environment tab
3. Add secret files or environment variables:
   - `SCHOLARSHIPS_COM_API_KEY`
   - `FASTWEB_API_KEY`
   - `GOING_MERRY_API_KEY`

### GitHub Actions
Add to repository secrets (Settings → Secrets)

### Local Development
Create `.env` file:
```bash
SCHOLARSHIPS_COM_API_KEY=your-key-here
FASTWEB_API_KEY=your-key-here
GOING_MERRY_API_KEY=your-key-here
```

Install python-dotenv:
```bash
pip install python-dotenv
```

## Troubleshooting

### Cron job not running
```bash
# Check cron service status
systemctl status cron

# Check cron logs
grep CRON /var/log/syslog

# Test script manually
cd /path/to/Gorilla-Link1
python scholarship_scraper.py
```

### Permission issues
```bash
# Make sure Python can write to log file
chmod 666 scholarship_updates.log

# Check database permissions
ls -la instance/
```

### Database locked
If using SQLite, ensure only one process writes at a time.
For production, use PostgreSQL (already configured on Render).

## Email Notifications (Future)

To get notified when updates complete:

1. Set up email in `scholarship_config.py`:
```python
SEND_EMAIL_NOTIFICATIONS = True
NOTIFICATION_EMAILS = ['admin@pittstate.edu']
```

2. Configure email in Flask app (app_pro.py):
```python
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USERNAME = 'your-email@gmail.com'
MAIL_PASSWORD = 'your-app-password'
```

## Best Practices

✅ **DO:**
- Run updates during low-traffic hours (2-4 AM)
- Monitor logs regularly
- Keep API keys secret
- Test updates in development first
- Set up error notifications

❌ **DON'T:**
- Run updates during peak hours
- Commit API keys to git
- Run updates too frequently (respect API limits)
- Ignore error logs
- Delete scholarship data without backups

## Next Steps

1. Choose your automation method (Render cron recommended)
2. Set up the schedule
3. Monitor first few runs
4. Adjust frequency as needed
5. Add API keys when available

---

**Questions?** Check the logs or run manually to debug.
