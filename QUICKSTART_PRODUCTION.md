# Quick Start: Populate Production Database

## Run This on Your Render Server

### Option 1: Via Render Shell (Recommended)
1. Go to your Render dashboard
2. Click on your "gorilla-link" service  
3. Click "Shell" tab
4. Run:
```bash
python seed_data_simple.py
```

### Option 2: Via SSH
```bash
# SSH into your Render instance
ssh <your-render-instance>

# Navigate to app directory
cd /opt/render/project/src

# Run the seed script
python seed_data_simple.py
```

### Expected Output
```
============================================================
🎓 Populating Careers & Scholarships Data
============================================================

💰 Adding scholarships...
Creating scholarships table...
✅ Added 16 scholarships

💼 Adding jobs...
✅ Added 20 jobs

============================================================
✅ Database populated successfully!
============================================================

📊 Summary:
   💰 Scholarships: 16
   💼 Jobs: 20

🚀 You can now view these at:
   • http://localhost:5000/scholarships
   • http://localhost:5000/careers
```

## Verify It Worked

Visit these URLs (replace with your actual domain):
- https://gorilla-link.onrender.com/scholarships
- https://gorilla-link.onrender.com/careers

You should see:
- ✅ 16 scholarship cards with PSU logos and details
- ✅ 20 job postings from Kansas/regional companies
- ✅ Filters working (categories, salary ranges, etc.)
- ✅ Search functionality operational

## Troubleshooting

### If Tables Already Exist
The script handles this automatically. It will:
1. Delete existing data
2. Insert fresh data
3. Report success

### If You Get Permission Errors
Make sure you're running as the correct user:
```bash
sudo -u render python seed_data_simple.py
```

### If Database Is Locked
Wait a few seconds and try again. Or restart your Render service first.

## Need Help?

The script is safe to run multiple times - it's idempotent and won't create duplicates.

Full documentation: See `DATA_POPULATION_COMPLETE.md`
