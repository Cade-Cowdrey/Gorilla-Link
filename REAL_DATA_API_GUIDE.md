# 🔌 REAL DATA API INTEGRATION GUIDE

## Overview
This guide explains how to integrate **real-time data APIs** for Career Intelligence and Housing AI features instead of using demo data.

---

## 📊 CAREER INTELLIGENCE - Bureau of Labor Statistics (BLS) API

### 1. Get Free BLS API Key

**Website**: https://www.bls.gov/developers/

**Steps**:
1. Visit https://data.bls.gov/registrationEngine/
2. Register with your email
3. Receive API key via email (v2.0 is free, 500 queries/day)
4. Add to your `.env` file:
   ```
   BLS_API_KEY=your_api_key_here
   ```

### 2. BLS API Endpoints We Use

**Salary Data**:
- Endpoint: `https://api.bls.gov/publicAPI/v2/timeseries/data/`
- Series IDs for common occupations:
  - Software Developers: `OEUM000000151250`
  - Management Analysts: `OEUM000000131111`
  - Registered Nurses: `OEUM000000291141`

**Job Openings**:
- Endpoint: Same as above
- Series IDs format: `OEUM[area][occupation]`

### 3. Integration Code

Create `utils/bls_api.py`:

```python
import requests
import os
from datetime import datetime

BLS_API_KEY = os.getenv('BLS_API_KEY')
BLS_BASE_URL = 'https://api.bls.gov/publicAPI/v2/timeseries/data/'

def fetch_occupation_data(series_id, start_year, end_year):
    """Fetch BLS data for specific occupation"""
    
    headers = {'Content-type': 'application/json'}
    data = {
        'seriesid': [series_id],
        'startyear': str(start_year),
        'endyear': str(end_year),
        'registrationkey': BLS_API_KEY
    }
    
    response = requests.post(BLS_BASE_URL, json=data, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"BLS API error: {response.status_code}")


def get_median_salary(occupation_code):
    """Get median salary for occupation"""
    current_year = datetime.now().year
    
    data = fetch_occupation_data(
        f'OEUM000000{occupation_code}',
        current_year - 1,
        current_year
    )
    
    # Parse most recent salary
    try:
        series = data['Results']['series'][0]
        latest = series['data'][0]
        return float(latest['value']) * 1000  # BLS returns in thousands
    except:
        return None


def get_job_growth_rate(occupation_code):
    """Get projected job growth rate"""
    # Use BLS Employment Projections data
    # https://www.bls.gov/emp/data/
    
    # This requires a different endpoint
    pass  # Implement based on needs


# Common occupation codes for PSU majors
OCCUPATION_CODES = {
    'Software Developer': '151252',
    'Management Analyst': '131111',
    'Registered Nurse': '291141',
    'Teacher': '252021',
    'Accountant': '132011',
    # Add more as needed
}
```

**Usage in seed script**:
```python
from utils.bls_api import get_median_salary, OCCUPATION_CODES

# Get real salary data
software_dev_salary = get_median_salary(OCCUPATION_CODES['Software Developer'])

pathway = CareerPathway(
    career_title='Software Developer',
    national_median_salary=software_dev_salary,
    # ... rest of fields
)
```

### 4. Alternative: LinkedIn Talent Insights API

**Better for skill demand data**

**Website**: https://developer.linkedin.com/

**Features**:
- Real-time skill demand
- Salary ranges by location
- Company hiring trends
- Skill gaps analysis

**Cost**: Requires LinkedIn partnership (not free)

**Integration**:
```python
import requests

LINKEDIN_API_KEY = os.getenv('LINKEDIN_API_KEY')

def get_skill_demand(skill_name, location='Kansas City'):
    """Fetch skill demand from LinkedIn"""
    
    url = f'https://api.linkedin.com/v2/talent-insights/skills/{skill_name}'
    headers = {'Authorization': f'Bearer {LINKEDIN_API_KEY}'}
    params = {'location': location}
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        return {
            'demand_score': data.get('demandScore'),
            'job_postings': data.get('jobPostings'),
            'salary_median': data.get('salaryMedian'),
            'trend': data.get('trend')
        }
```

### 5. Free Alternative: Indeed API

**Website**: https://opensource.indeedeng.io/api-documentation/

**Features**:
- Job postings by skill
- Salary estimates
- Trending skills

**Integration**:
```python
import requests

def search_indeed_jobs(skill, location='Pittsburg, KS'):
    """Search Indeed for jobs requiring skill"""
    
    url = 'http://api.indeed.com/ads/apisearch'
    params = {
        'publisher': os.getenv('INDEED_PUBLISHER_ID'),
        'q': skill,
        'l': location,
        'format': 'json',
        'v': '2'
    }
    
    response = requests.get(url, params=params)
    return response.json()
```

---

## 🏠 HOUSING AI - Zillow API Integration

### 1. Get Zillow API Key

**Website**: https://www.zillow.com/howto/api/APIOverview.htm

**Note**: Zillow's free API was discontinued in 2021. Alternatives:

#### Option A: RapidAPI - Zillow Data
**Website**: https://rapidapi.com/apimaker/api/zillow-com1/

**Cost**: Free tier (100 requests/month)

**Setup**:
```bash
# Install
pip install requests

# Add to .env
RAPIDAPI_KEY=your_key_here
```

**Integration Code** (`utils/zillow_api.py`):
```python
import requests
import os

RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')
RAPIDAPI_HOST = "zillow-com1.p.rapidapi.com"

def search_rentals_near_psu(max_price=1000, bedrooms=2):
    """Search for rental properties near PSU"""
    
    url = "https://zillow-com1.p.rapidapi.com/propertyExtendedSearch"
    
    querystring = {
        "location": "Pittsburg, KS",
        "status_type": "ForRent",
        "home_type": "Apartments",
        "maxPrice": str(max_price),
        "beds": str(bedrooms),
        "sort": "Price_Low_High"
    }
    
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }
    
    response = requests.get(url, headers=headers, params=querystring)
    
    if response.status_code == 200:
        return response.json()['props']
    else:
        raise Exception(f"Zillow API error: {response.status_code}")


def parse_zillow_listing(zillow_data):
    """Convert Zillow data to our HousingListing format"""
    
    return {
        'property_name': zillow_data.get('address', {}).get('streetAddress'),
        'address': zillow_data.get('address', {}).get('streetAddress'),
        'city': zillow_data.get('address', {}).get('city'),
        'state': zillow_data.get('address', {}).get('state'),
        'zip_code': zillow_data.get('address', {}).get('zipcode'),
        'property_type': 'apartment',
        'bedrooms': zillow_data.get('bedrooms'),
        'bathrooms': zillow_data.get('bathrooms'),
        'square_feet': zillow_data.get('livingArea'),
        'monthly_rent': zillow_data.get('price'),
        'photos': zillow_data.get('imgSrc'),
        'latitude': zillow_data.get('latitude'),
        'longitude': zillow_data.get('longitude'),
        # Calculate distance to PSU
        'distance_to_campus_miles': calculate_distance(
            zillow_data.get('latitude'),
            zillow_data.get('longitude'),
            37.4108,  # PSU coordinates
            -94.7046
        ),
        'status': 'available',
        'is_verified': False,  # Verify manually
        'last_verified': datetime.utcnow()
    }


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates"""
    from math import radians, cos, sin, asin, sqrt
    
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    miles = 3956 * c
    return round(miles, 2)
```

**Usage**:
```python
from utils.zillow_api import search_rentals_near_psu, parse_zillow_listing

# Fetch real listings
zillow_listings = search_rentals_near_psu(max_price=1000, bedrooms=2)

# Add to database
for zillow_data in zillow_listings:
    listing_data = parse_zillow_listing(zillow_data)
    listing = HousingListing(**listing_data)
    db.session.add(listing)

db.session.commit()
```

#### Option B: Apartments.com Partnership

**Contact**: Business development team
**Cost**: Negotiated (typically requires revenue share)
**Better for**: Student housing specifically

#### Option C: Web Scraping (with permission)

**Legal**: Must comply with terms of service
**Tools**: Beautiful Soup, Scrapy
**Sources**: Craigslist (allows scraping), local rental sites

**Example** (`utils/housing_scraper.py`):
```python
import requests
from bs4 import BeautifulSoup

def scrape_craigslist_pittsburg():
    """Scrape Craigslist for Pittsburg rentals"""
    
    url = "https://kansascity.craigslist.org/search/apa?query=pittsburg&availabilityMode=0"
    
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    listings = []
    for result in soup.find_all('li', class_='result-row'):
        title = result.find('a', class_='result-title').text
        price = result.find('span', class_='result-price').text
        href = result.find('a', class_='result-title')['href']
        
        listings.append({
            'title': title,
            'monthly_rent': float(price.replace('$', '').replace(',', '')),
            'url': href
        })
    
    return listings
```

---

## 🔄 AUTOMATED DATA UPDATES

### Create Scheduled Tasks

**File**: `tasks/update_career_data.py`

```python
from apscheduler.schedulers.background import BackgroundScheduler
from utils.bls_api import get_median_salary
from models_advanced_features import CareerPathway

def update_all_career_pathways():
    """Update all career pathway salary data"""
    
    pathways = CareerPathway.query.all()
    
    for pathway in pathways:
        try:
            # Fetch updated salary data
            new_salary = get_median_salary(pathway.occupation_code)
            
            if new_salary:
                pathway.national_median_salary = new_salary
                pathway.last_updated = datetime.utcnow()
        
        except Exception as e:
            print(f"Error updating {pathway.career_title}: {e}")
    
    db.session.commit()
    print(f"Updated {len(pathways)} career pathways")


def update_housing_listings():
    """Update housing listings from APIs"""
    from utils.zillow_api import search_rentals_near_psu, parse_zillow_listing
    
    # Mark old listings as potentially outdated
    HousingListing.query.filter(
        HousingListing.last_verified < datetime.utcnow() - timedelta(days=7)
    ).update({'status': 'needs_verification'})
    
    # Fetch new listings
    zillow_listings = search_rentals_near_psu(max_price=1500, bedrooms=2)
    
    for zillow_data in zillow_listings:
        listing_data = parse_zillow_listing(zillow_data)
        
        # Check if already exists
        existing = HousingListing.query.filter_by(
            address=listing_data['address']
        ).first()
        
        if existing:
            # Update existing
            for key, value in listing_data.items():
                setattr(existing, key, value)
        else:
            # Add new
            listing = HousingListing(**listing_data)
            db.session.add(listing)
    
    db.session.commit()
    print(f"Updated housing listings")


# Schedule tasks
scheduler = BackgroundScheduler()

# Update career data monthly (1st of month at 2 AM)
scheduler.add_job(
    update_all_career_pathways,
    'cron',
    day=1,
    hour=2
)

# Update housing listings weekly (Sundays at 3 AM)
scheduler.add_job(
    update_housing_listings,
    'cron',
    day_of_week='sun',
    hour=3
)

scheduler.start()
```

**Add to `app_pro.py`**:
```python
from tasks.update_career_data import scheduler

# Start scheduler when app starts
with app.app_context():
    scheduler.start()
```

---

## 📋 SETUP CHECKLIST

### For Career Intelligence:
- [ ] Get BLS API key (free, 500 requests/day)
- [ ] Add `BLS_API_KEY` to `.env`
- [ ] Install dependencies: `pip install requests`
- [ ] Create `utils/bls_api.py`
- [ ] Update seed script to use real BLS data
- [ ] Schedule monthly updates

### For Housing AI:
- [ ] Choose API provider (RapidAPI recommended)
- [ ] Get API key
- [ ] Add `RAPIDAPI_KEY` to `.env`
- [ ] Create `utils/zillow_api.py`
- [ ] Test API integration
- [ ] Schedule weekly updates

### For Skill Demand:
- [ ] Choose provider (LinkedIn or Indeed)
- [ ] Get API access
- [ ] Create integration utility
- [ ] Update `seed_skill_demand()` function
- [ ] Schedule monthly updates

---

## 💰 COST BREAKDOWN

### FREE Options:
- ✅ BLS API: FREE (500 requests/day)
- ✅ Indeed API: FREE (with attribution)
- ✅ RapidAPI Zillow: FREE tier (100 requests/month)

### PAID Options (Optional):
- 💰 LinkedIn Talent Insights: $$$$ (enterprise pricing)
- 💰 Burning Glass Technologies: $$$ (requires partnership)
- 💰 Apartments.com API: $$ (revenue share model)

### Recommended Setup:
**Total Cost: $0/month**
- BLS API for salary data (free)
- Indeed API for skill demand (free)
- RapidAPI Zillow for housing (free tier sufficient)

---

## 🎯 PRODUCTION DEPLOYMENT

### 1. Environment Variables

Add to `.env`:
```bash
# Career Intelligence
BLS_API_KEY=your_bls_key_here

# Skill Demand
INDEED_PUBLISHER_ID=your_indeed_id_here

# Housing Data
RAPIDAPI_KEY=your_rapidapi_key_here

# Update Schedule
UPDATE_CAREER_DATA=monthly
UPDATE_HOUSING_DATA=weekly
UPDATE_SKILL_DATA=monthly
```

### 2. Install Dependencies

```bash
pip install requests beautifulsoup4 apscheduler
```

### 3. Run Initial Data Load

```bash
python seed_advanced_features.py
```

### 4. Enable Scheduled Updates

Make sure `tasks/update_career_data.py` is imported in `app_pro.py`

---

## 📊 DATA FRESHNESS

### Career Data:
- **Update Frequency**: Monthly
- **Source**: BLS (released quarterly, use latest)
- **Stale After**: 90 days

### Housing Data:
- **Update Frequency**: Weekly
- **Source**: Zillow/Craigslist
- **Stale After**: 7 days

### Skill Demand:
- **Update Frequency**: Monthly
- **Source**: LinkedIn/Indeed
- **Stale After**: 30 days

---

## ✅ VERIFICATION

After integration, verify:

1. **Career Data**:
   ```python
   pathway = CareerPathway.query.first()
   print(f"Salary: ${pathway.national_median_salary}")
   print(f"Source: {pathway.data_source}")
   print(f"Updated: {pathway.last_updated}")
   ```

2. **Housing Data**:
   ```python
   listing = HousingListing.query.first()
   print(f"Property: {listing.property_name}")
   print(f"Rent: ${listing.monthly_rent}")
   print(f"Verified: {listing.last_verified}")
   ```

3. **Skill Data**:
   ```python
   skill = SkillDemandForecast.query.first()
   print(f"Skill: {skill.skill_name}")
   print(f"Demand: {skill.current_demand_score}")
   print(f"Source: {skill.data_source}")
   ```

---

## 🆘 TROUBLESHOOTING

### BLS API Rate Limits
- **Problem**: 500 requests/day limit hit
- **Solution**: Cache data, update less frequently, or get v2 key

### Housing API Costs
- **Problem**: Free tier not enough
- **Solution**: Use multiple sources (Zillow + Craigslist + local sites)

### Data Quality Issues
- **Problem**: Missing fields from APIs
- **Solution**: Set default values, mark as needs_verification

---

*Last Updated: November 5, 2025*
*For questions: Check API documentation or contact provider support*
