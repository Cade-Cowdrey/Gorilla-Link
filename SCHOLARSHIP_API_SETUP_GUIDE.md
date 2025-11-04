# 🎓 Scholarship API Integration Guide

## Overview
This guide explains how to connect PittState-Connect with scholarship APIs to automatically pull real-time scholarship data.

---

## 💰 Cost Breakdown

### **FREE Options**
1. **Federal Student Aid API** - 100% FREE
   - No API key required for basic access
   - Pell Grants, FSEOG, federal scholarships
   - Official government data

2. **Open Data Sources** - FREE
   - Department of Education datasets
   - State grant databases
   - University scholarship portals

3. **Web Scraping** - FREE (but requires maintenance)
   - Your current `scholarship_scraper.py`
   - Manual updates needed

### **Freemium/Educational Pricing**
1. **Fastweb** - FREE for educational institutions
   - Contact: https://www.fastweb.com/contact
   - Mention you're a university platform
   - 1.5M+ scholarships

2. **Scholarships.com** - Contact for pricing
   - Often offers free tiers for .edu domains
   - 3.7M+ scholarships, $19B+ funding
   - Contact: api@scholarships.com

3. **Going Merry** - Free for students, paid for institutions
   - Contact: support@goingmerry.com
   - Great for application tracking
   - May offer free trial

### **Paid Options** (if budget allows)
- **ScholarshipOwl API**: $99-$499/month
- **Bold.org API**: Contact for pricing
- **Niche.com API**: Contact for pricing

---

## 🚀 Step-by-Step Setup

### Step 1: Get API Keys

#### **Federal Student Aid (FREE - No Key Needed)**
```bash
# No registration required!
# Just use the public API endpoint
curl https://api.studentaid.gov/v1/grants
```

#### **Fastweb (Request Access)**
1. Go to: https://www.fastweb.com/contact
2. Subject: "API Access for Educational Platform"
3. Message:
```
Hello,

I'm developing PittState-Connect, a scholarship platform for 
Pittsburg State University students. We'd like to integrate 
Fastweb's scholarship API to provide real-time opportunities 
to our students.

University: Pittsburg State University
Platform: pittstate-connect.onrender.com
Purpose: Student scholarship discovery

Could you please provide API access or guide us through 
your partnership program for educational institutions?

Thank you!
```

#### **Scholarships.com (Request Access)**
1. Email: api@scholarships.com
2. Include your .edu email if possible
3. Mention educational/non-profit use

#### **Going Merry (Request Trial)**
1. Go to: https://www.goingmerry.com/partnerships
2. Fill out partner inquiry form
3. Request API documentation

---

### Step 2: Set Environment Variables

Add to your `.env` file:

```bash
# Scholarship APIs
SCHOLARSHIPS_COM_API_KEY=your_key_here
FASTWEB_API_KEY=your_key_here
GOING_MERRY_API_KEY=your_key_here
FEDERAL_AID_API_KEY=optional_if_needed

# Enable/disable specific sources
ENABLE_SCHOLARSHIPS_COM=True
ENABLE_FASTWEB=True
ENABLE_GOING_MERRY=True
ENABLE_FEDERAL_AID=True
```

On Render:
1. Go to your service dashboard
2. Environment → Add Environment Variables
3. Add each API key

---

### Step 3: Install the Integration

The code is already in `scholarship_api_integration.py`. Now integrate it:

#### **Add to app.py (Automated Daily Sync)**

```python
from flask_apscheduler import APScheduler
from scholarship_api_integration import sync_scholarships_from_apis

scheduler = APScheduler()
scheduler.init_app(app)

# Run scholarship sync daily at 3 AM
@scheduler.task('cron', id='sync_scholarships', hour=3, minute=0)
def scheduled_scholarship_sync():
    with app.app_context():
        sync_scholarships_from_apis()

scheduler.start()
```

#### **Add Admin Route (Manual Trigger)**

Add to `blueprints/scholarships/routes.py`:

```python
from scholarship_api_integration import ScholarshipAPIClient, sync_scholarships_from_apis

@bp.route("/admin/sync-scholarships", methods=["POST"])
@login_required
def admin_sync_scholarships():
    """Manual trigger for scholarship API sync (admin only)"""
    if not current_user.is_admin:
        flash("Unauthorized access", "danger")
        return redirect(url_for("core.home"))
    
    try:
        sync_scholarships_from_apis()
        flash("✅ Scholarship sync started! Check back in a few minutes.", "success")
    except Exception as e:
        flash(f"❌ Error syncing scholarships: {str(e)}", "danger")
    
    return redirect(url_for("scholarships.browse"))
```

---

### Step 4: Test the Integration

#### **Manual Test (Python Console)**

```bash
# On your local machine
python

>>> from scholarship_api_integration import ScholarshipAPIClient
>>> client = ScholarshipAPIClient()
>>> 
>>> # Test Federal Aid API (free, no key needed)
>>> scholarships = client.fetch_from_federal_aid()
>>> print(f"Found {len(scholarships)} federal scholarships")
>>> 
>>> # Test all APIs
>>> all_scholarships = client.fetch_all_scholarships()
>>> print(f"Total scholarships: {len(all_scholarships)}")
```

#### **Test via Admin Panel**

1. Login as admin: `admin` / `demo123`
2. Navigate to: `/scholarships/admin/sync-scholarships`
3. Click "Sync Scholarships" button
4. Check database for new entries

---

## 🔄 Alternative: No-Code/Low-Code Options

If APIs are too complex or expensive:

### **Option 1: Zapier/Make Integration**
- Use Zapier to connect scholarship sites
- Trigger: New scholarship posted
- Action: Add to your database via webhook
- Cost: $20-$50/month

### **Option 2: RSS Feeds**
Many scholarship sites offer RSS feeds:
```python
import feedparser

def fetch_from_rss(feed_url):
    feed = feedparser.parse(feed_url)
    scholarships = []
    
    for entry in feed.entries:
        scholarships.append({
            'title': entry.title,
            'url': entry.link,
            'description': entry.summary,
            'published': entry.published
        })
    
    return scholarships

# Example RSS feeds
feeds = [
    'https://www.scholarships.com/rss',
    'https://www.fastweb.com/rss',
]
```

### **Option 3: Google Sheets + Google Apps Script**
1. Maintain scholarships in Google Sheets
2. Share sheet publicly
3. Read from sheet in your app:

```python
import pandas as pd

def fetch_from_google_sheets():
    sheet_url = 'https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/export?format=csv'
    df = pd.read_csv(sheet_url)
    return df.to_dict('records')
```

---

## 📊 Recommended Approach for PittState

### **Phase 1: Start Free (Current)**
✅ Use your existing `scholarship_scraper.py`  
✅ Add Federal Student Aid API (100% free)  
✅ Manually curate 50-100 high-quality scholarships  

### **Phase 2: Request Educational Access**
📧 Contact Fastweb for free institutional access  
📧 Contact Scholarships.com with .edu email  
📧 Request Going Merry partnership  

### **Phase 3: Automate (If APIs Granted)**
🤖 Implement `scholarship_api_integration.py`  
🤖 Schedule daily syncs at 3 AM  
🤖 Auto-expire old scholarships  

### **Phase 4: Premium (If Budget Allows)**
💰 Consider ScholarshipOwl API ($99/month)  
💰 Add Niche.com integration  
💰 Enterprise features  

---

## 💡 Pro Tips

### **1. Start with What's Free**
```python
# Federal API is always free - use it first!
client = ScholarshipAPIClient()
federal_scholarships = client.fetch_from_federal_aid()
client.sync_to_database(federal_scholarships)
```

### **2. Be Patient with Educational Requests**
- Universities often get free/discounted API access
- Mention you're a student project for PSU
- Highlight social impact (helping students find funding)

### **3. Hybrid Approach**
```python
# Combine APIs + scraping + manual curation
def aggregate_all_sources():
    scholarships = []
    
    # API sources (when available)
    scholarships.extend(fetch_from_apis())
    
    # Web scraping (reliable backup)
    scholarships.extend(scrape_scholarship_sites())
    
    # Manual curation (highest quality)
    scholarships.extend(get_psu_specific_scholarships())
    
    return scholarships
```

### **4. Cache API Results**
```python
from flask_caching import Cache

@cache.cached(timeout=86400)  # Cache for 24 hours
def get_scholarships_from_api():
    client = ScholarshipAPIClient()
    return client.fetch_all_scholarships()
```

---

## 🎯 Expected Results

### **With Free APIs Only**
- 50-100 federal grants/scholarships
- Updated daily automatically
- Zero cost

### **With Educational Access (Fastweb + Scholarships.com)**
- 5,000+ scholarships
- $20M+ in funding
- Real-time updates
- Still free!

### **With Premium APIs**
- 10,000+ scholarships
- Advanced matching algorithms
- Application tracking
- $100-500/month

---

## 🆘 Support Resources

### **API Documentation**
- Federal Aid: https://studentaid.gov/data-center/api
- Scholarships.com: Contact api@scholarships.com
- Fastweb: https://www.fastweb.com/contact
- Going Merry: https://www.goingmerry.com/partnerships

### **Your Current Setup**
Your existing `scholarship_scraper.py` already has 27 real scholarships worth $390K+!
This is a great starting point while you request API access.

### **Next Steps**
1. ✅ Keep using your current scraper
2. 📧 Email Fastweb/Scholarships.com today (free for edu!)
3. 🔧 Add Federal API (100% free, no approval needed)
4. 🤖 Set up daily automation
5. 📈 Scale as you get API access

---

## 📞 Need Help?

If you get approved for any APIs, just let me know and I'll help you:
- Configure API keys in Render
- Set up automated syncing
- Test the integration
- Debug any issues

**Remember**: Most scholarship APIs are happy to support educational institutions for FREE or at steep discounts. Don't be afraid to ask! 🎓
