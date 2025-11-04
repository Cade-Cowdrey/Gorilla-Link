# 🦍 Demo Data Setup Guide

## Quick Start - Populate Demo Data

To fill your app with impressive demo data for your presentation, run:

```bash
python seed_complete_demo.py
```

⚠️ **WARNING:** This will clear existing data and replace it with demo data!

## What Gets Created

### 👥 **Users** (18 total)
- **2 Admins**: admin, jdoe
- **8 Students**: Various majors (CS, Engineering, Business, etc.)
- **4 Alumni**: Graduated professionals
- **2 Faculty**: Professors
- **2 Employers**: Tech Corp & Innovation LLC

**All passwords**: `demo123`

### 💼 **Jobs** (8 postings)
- Software Engineer @ Tech Corp ($65k-$85k)
- Data Analyst @ Innovation LLC ($55k-$70k)
- Marketing Coordinator, Project Manager, UX Designer, etc.
- Mix of remote and local positions

### 📅 **Events** (8 upcoming)
- Career Fair 2025
- Tech Talk: AI in Industry
- Alumni Networking Night
- Resume Workshop
- Hackathon 2025
- And more!

### 🎓 **Scholarships** (5 opportunities)
- Gorilla Excellence Scholarship ($5,000)
- STEM Leadership Award ($3,000)
- Community Service Grant ($2,000)
- First Generation Scholarship ($4,000)
- Athletics Scholarship ($6,000)

### 🌟 **Success Stories** (4 featured)
- From PSU to Silicon Valley
- Starting My Own Business
- Making a Difference in Healthcare
- Career Change Success

### 💬 **Forum Discussions**
- 4 categories (General, Career Advice, Student Life, Technology)
- Multiple topics with replies
- Active student engagement

### 🤝 **Mentorship**
- Active mentor-mentee matches
- Alumni mentoring students
- Real connection data

### 🎮 **Gamification**
- User points and levels
- Point transactions for activities
- Achievement tracking

### 📊 **Analytics**
- 30 days of engagement data
- Active users, signups, job applications
- Ready for dashboard visualizations

## Demo Login Credentials

### Admin Access
```
Username: admin
Password: demo123
```

### Student Account
```
Username: sarah.johnson
Password: demo123
```

### Alumni Account
```
Username: robert.smith
Password: demo123
```

### Employer Account
```
Username: hr.techcorp
Password: demo123
```

## Running on Production (Render)

1. SSH into your Render shell or use the web console
2. Run:
   ```bash
   python seed_complete_demo.py
   ```
3. Type `yes` when prompted
4. Wait ~30 seconds for completion

## Features Showcased

✅ **User Management** - Various roles and permissions  
✅ **Job Board** - Active job postings from companies  
✅ **Events System** - Upcoming campus events  
✅ **Scholarships** - Financial aid opportunities  
✅ **Success Stories** - Alumni testimonials  
✅ **Forum** - Active discussions and community  
✅ **Mentorship** - Student-alumni connections  
✅ **Gamification** - Points, levels, achievements  
✅ **Analytics** - Engagement metrics and insights  

## Presentation Tips

1. **Start at Homepage** - Shows featured content
2. **Login as Admin** - Full access to all features
3. **Show Job Board** - Real job postings
4. **Demo Events** - Upcoming career fairs
5. **View Success Stories** - Alumni testimonials
6. **Browse Forum** - Active discussions
7. **Check Analytics** - Show engagement data
8. **Highlight Mentorship** - Student-alumni connections

## Cleaning Up After Demo

To remove demo data and start fresh:
```bash
python seed_complete_demo.py
# Then type 'yes' when prompted
```

---

**Need help?** Contact your development team or check the main README.md
