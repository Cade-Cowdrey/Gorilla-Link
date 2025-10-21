from app_pro import app
from extensions import db
from models import (
    Scholarship, ScholarshipApplication, Essay, Reminder, FinancialLiteracyResource,
    CostToCompletion, FundingJourney, FacultyRecommendation, LeaderboardEntry,
    PeerMentor, Donor, Donation, ImpactStory
)
from datetime import date, datetime, timedelta
import random

def seed_data():
    with app.app_context():
        print("🌱 Starting PittState-Connect seed...")

        db.create_all()

        # Skip if data already exists
        if Scholarship.query.first():
            print("⚠️  Tables already contain data — skipping seeds to avoid duplicates.")
            return

        scholarships = [
            Scholarship(title="Gorilla Scholars Excellence Award",
                        description="Awarded to high-achieving PSU students.",
                        amount=2000, deadline=date(2025,12,1), department="Arts & Sciences"),
            Scholarship(title="College of Technology Leadership Grant",
                        description="Recognizes leadership in applied sciences.",
                        amount=1500, deadline=date(2025,11,15), department="Technology"),
            Scholarship(title="Crimson & Gold Academic Achievement Fund",
                        description="Supports academic excellence across majors.",
                        amount=1000, deadline=date(2025,10,30), department="General Studies"),
            Scholarship(title="Kelce College of Business Emerging Leaders",
                        description="Entrepreneurial excellence scholarship.",
                        amount=2500, deadline=date(2025,12,10), department="Business"),
            Scholarship(title="Nursing Advancement Scholarship",
                        description="Encourages excellence in health and nursing fields.",
                        amount=1800, deadline=date(2025,11,1), department="Nursing")
        ]
        db.session.add_all(scholarships)
        db.session.flush()

        apps = [ScholarshipApplication(user_id=i+1, scholarship_id=s.id,
                                       status=random.choice(["draft","submitted","awarded","rejected"]),
                                       progress=random.randint(0,100),
                                       submitted_at=datetime.utcnow())
                for i, s in enumerate(scholarships)]
        db.session.add_all(apps)

        essays = [Essay(user_id=i+1, title=f"Scholarship Essay {i+1}",
                        content="My journey as a Gorilla at PSU...", last_updated=datetime.utcnow())
                  for i in range(5)]
        db.session.add_all(essays)

        reminders = [Reminder(user_id=i+1, scholarship_id=scholarships[i].id,
                              due_at=datetime.utcnow()+timedelta(days=7*(i+1)),
                              note="Submit documents before deadline")
                     for i in range(5)]
        db.session.add_all(reminders)

        resources = [
            FinancialLiteracyResource(title="Budget Like a Gorilla", url="https://psu.edu/budgeting", category="Budgeting"),
            FinancialLiteracyResource(title="Understanding Student Loans", url="https://psu.edu/loans", category="Loans"),
            FinancialLiteracyResource(title="Scholarship Search Tips", url="https://psu.edu/scholarships", category="Aid"),
            FinancialLiteracyResource(title="Smart Credit Habits", url="https://psu.edu/credit", category="Credit"),
            FinancialLiteracyResource(title="Investing 101 for Students", url="https://psu.edu/investing", category="Investing")
        ]
        db.session.add_all(resources)

        ctc = [CostToCompletion(user_id=i+1, estimated_tuition_remaining=5000*(i+1),
                                est_graduation_date=date(2026,5,15)) for i in range(5)]
        db.session.add_all(ctc)

        journeys = [FundingJourney(user_id=i+1, step=step, timestamp=datetime.utcnow())
                    for i, step in enumerate(["FAFSA Submitted","Dept Scholarship","Donor Award","Grant Received","Tuition Cleared"])]
        db.session.add_all(journeys)

        recs = [FacultyRecommendation(applicant_user_id=i+1,
                                      faculty_name=f"Prof. {name}",
                                      file_url=f"https://s3.psu.edu/recs/{name.lower()}.pdf")
                for i, name in enumerate(["Stein","Johnson","Martinez","Nguyen","Patel"])]
        db.session.add_all(recs)

        leaders = [LeaderboardEntry(user_id=i+1, points=100*(i+1)) for i in range(5)]
        db.session.add_all(leaders)

        peers = [PeerMentor(mentor_user_id=i+1, mentee_user_id=(i+2)) for i in range(5)]
        db.session.add_all(peers)

        donors = [
            Donor(name="Crimson & Gold Alumni Fund", organization="PSU Alumni Association", contact_email="alumni@pittstate.edu"),
            Donor(name="Gorilla Gear Industries", organization="Local Sponsor", contact_email="info@gorillagear.com"),
            Donor(name="Kelce Business Partners", organization="Kelce College Network", contact_email="kelce@pittstate.edu"),
            Donor(name="College of Technology Advisory Board", organization="Industry Advisory", contact_email="techboard@pittstate.edu"),
            Donor(name="Community Health Foundation", organization="Health & Nursing", contact_email="health@pittstate.edu")
        ]
        db.session.add_all(donors)
        db.session.flush()

        donations = [Donation(donor_id=d.id, amount=1000*(i+1), note="Annual support for student success")
                     for i, d in enumerate(donors)]
        db.session.add_all(donations)

        stories = [
            ImpactStory(title="From Gorilla to Graduate",
                        body="Scholarships from PSU made my dream possible.",
                        photo_url="https://psu.edu/images/impact1.jpg",
                        published_at=datetime.utcnow()),
            ImpactStory(title="Engineering Success Story",
                        body="College of Technology alumni fund changed my path.",
                        photo_url="https://psu.edu/images/impact2.jpg",
                        published_at=datetime.utcnow()),
            ImpactStory(title="Healthcare Heroes at PSU",
                        body="Nursing scholarships empowered me to serve others.",
                        photo_url="https://psu.edu/images/impact3.jpg",
                        published_at=datetime.utcnow()),
            ImpactStory(title="Business Leaders of Tomorrow",
                        body="Kelce College donors shaped my entrepreneurial journey.",
                        photo_url="https://psu.edu/images/impact4.jpg",
                        published_at=datetime.utcnow()),
            ImpactStory(title="Crimson & Gold Community Impact",
                        body="PSU students give back through donor-funded projects.",
                        photo_url="https://psu.edu/images/impact5.jpg",
                        published_at=datetime.utcnow())
        ]
        db.session.add_all(stories)

        db.session.commit()

        print("✅ Seeding complete!")
        print("---------------------------------")
        print("5 Scholarships\n5 Scholarship Applications\n5 Essays\n5 Reminders\n5 Financial Literacy Resources\n"
              "5 Cost-to-Completion Records\n5 Funding Journey Steps\n5 Faculty Recommendations\n5 Leaderboard Entries\n"
              "5 Peer Mentors\n5 Donors\n5 Donations\n5 Impact Stories")
        print("---------------------------------")

if __name__ == "__main__":
    seed_data()
