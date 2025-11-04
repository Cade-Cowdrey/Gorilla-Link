# 🦍 Demo Data Setup Guide

## Quick Start - Populate Demo Data

To fill your app with impressive demo data for your presentation, run:

```bash
python seed_complete_demo.py
```

⚠️ **WARNING:** This will clear existing data and replace it with demo data!

## What Gets Created

### 👥 **Users** (40 total)
- **2 Admins**: admin, admin2
- **17 Students**: student, student2, student3... (various majors)
- **8 Alumni**: alumni, alumni2, alumni3... (graduated professionals)
- **4 Faculty**: faculty, faculty2, faculty3, faculty4
- **4 Employers**: employer, employer2, employer3, employer4

**All passwords**: `demo123`

### 💼 **Jobs** (60 postings)
- **Tech/CS** (15): Software Engineer, DevOps, Web Dev, Cybersecurity, etc.
- **Business** (12): Data Analyst, Marketing, Sales, Project Manager, etc.
- **Engineering** (8): Mechanical, Electrical, Civil, Quality Engineer, etc.
- **Healthcare** (6): RN, Nurse Practitioner, Physical Therapist, etc.
- **Education** (4): Academic Advisor, Career Counselor, Training, etc.
- **Creative** (5): Graphic Designer, Content Writer, Social Media, etc.
- Various locations (Remote, Kansas City, Wichita, Pittsburg, Joplin)
- Salary info and detailed descriptions

### 📅 **Events** (40 upcoming)
- **Career Dev** (12): Career fairs, workshops, mock interviews, panels
- **Networking** (8): Alumni nights, speed networking, industry mixers
- **Tech/Innovation** (6): Hackathons, bootcamps, pitch competitions
- **Campus Life** (8): Homecoming, concerts, cultural festivals
- **Academic** (6): Research symposium, study skills, grad school prep
- Events scheduled from 2 days to 60 days out

### 🎓 **Scholarships** (31 opportunities)
- **Academic Excellence** (5): Merit awards ($2,500-$8,000)
- **STEM Fields** (6): CS, Engineering, Math, Biology
- **Business/Social Sciences** (4): Business, Entrepreneurship, Psychology
- **Healthcare** (3): Nursing and allied health
- **Special Populations** (6): First-gen, veterans, transfer, international
- **Community/Service** (4): Volunteer and campus involvement
- **Athletics/Arts** (3): Sports, performing arts, visual arts

### 🌟 **Success Stories** (16 featured)
- Tech careers (Google, startups, tech leads)
- Business success (own companies, corporate leadership)
- Healthcare journeys (nurses, nurse practitioners)
- Engineering innovations (aerospace, PE licenses)
- Career changes (non-traditional students)
- Graduate school (PhD programs)
- Community impact (nonprofits, service)

### 💬 **Forum Discussions**
- 4 categories (Career Advice, Academic Help, Campus Life, Tech Discussion)
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
Username: student
Password: demo123
```
(Also: student2, student3... through student15)

### Alumni Account
```
Username: alumni
Password: demo123
```
(Also: alumni2, alumni3... through alumni8)

### Faculty Account
```
Username: faculty
Password: demo123
```
(Also: faculty2, faculty3, faculty4)

### Employer Account
```
Username: employer
Password: demo123
```
(Also: employer2, employer3, employer4)

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
