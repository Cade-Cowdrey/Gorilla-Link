PittState-Connect Addons & Seeder Pack
=====================================

1. Copy the files into your project:
   - migrations/versions/0027_pittstate_connect_addons.py
   - seed_pittstate_connect.py

2. Run migrations:
   flask db upgrade

3. Seed data:
   python seed_pittstate_connect.py

4. Expected output:
   ✅ Seeding complete!
   ---------------------------------
   5 Scholarships
   5 Scholarship Applications
   5 Essays
   5 Reminders
   5 Financial Literacy Resources
   5 Cost-to-Completion Records
   5 Funding Journey Steps
   5 Faculty Recommendations
   5 Leaderboard Entries
   5 Peer Mentors
   5 Donors
   5 Donations
   5 Impact Stories
   ---------------------------------

Troubleshooting
---------------
• If Flask is not found → install dependencies:
      pip install -r requirements.txt

• If migration fails ("locked" or "no such table") → rerun:
      flask db upgrade

• If duplicates appear → clear DB and rerun seeder once.

• On Render:
      - Open Shell tab
      - Run same two commands
      - Check logs for '✅ Seeding complete!'

Contact: Cade-Cowdrey PittState-Connect Project
