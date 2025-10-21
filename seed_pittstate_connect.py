# seed_pittstate_connect.py
# -------------------------------------------------------------
# Populates the PittState-Connect database with PSU-themed demo data.
# Safe for testing and UI previews.
# -------------------------------------------------------------

from datetime import datetime, timedelta, date
from faker import Faker
import random
from extensions import db
from models import *

fake = Faker()

def seed_all():
    print("🌱 Starting PSU demo data seed...")

    # ---------------------------------------------
    # Roles
    # ---------------------------------------------
    roles = ["Admin", "Student", "Alumni", "Faculty", "Employer", "Donor"]
    for r in roles:
        if not Role.query.filter_by(name=r).first():
            db.session.add(Role(name=r, description=f"{r} role"))
    db.session.commit()

    # ---------------------------------------------
    # Users
    # ---------------------------------------------
    demo_users = []
    for i in range(1, 6):
        student = User(
            email=f"student{i}@pittstate.edu",
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            role=Role.query.filter_by(name="Student").first(),
            verified=True,
        )
        student.set_password("password123")
        demo_users.append(student)

    for i in range(1, 4):
        alumni = User(
            email=f"alumni{i}@pittstate.edu",
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            role=Role.query.filter_by(name="Alumni").first(),
            verified=True,
        )
        alumni.set_password("password123")
        demo_users.append(alumni)

    admin_user = User(
        email="admin@pittstate.edu",
        first_name="Gus",
        last_name="Gorilla",
        role=Role.query.filter_by(name="Admin").first(),
        verified=True,
    )
    admin_user.set_password("adminpass")

    db.session.add_all(demo_users + [admin_user])
    db.session.commit()

    # ---------------------------------------------
    # Departments & Faculty
    # ---------------------------------------------
    dept_names = [
        "College of Technology",
        "Kelce College of Business",
        "College of Education",
        "College of Arts & Sciences",
        "School of Construction"
    ]
    departments = []
    for name in dept_names:
        d = Department(name=name, building=fake.street_name(), phone=fake.phone_number(), website=f"https://www.pittstate.edu/{name.split()[0].lower()}")
        departments.append(d)
    db.session.add_all(departments)
    db.session.commit()

    faculty_members = []
    for d in departments:
        for i in range(2):
            f = Faculty(name=fake.name(), department=d, email=f"{fake.first_name().lower()}@pittstate.edu", title=random.choice(["Professor", "Advisor", "Coordinator"]))
            faculty_members.append(f)
    db.session.add_all(faculty_members)
    db.session.commit()

    # ---------------------------------------------
    # Scholarships
    # ---------------------------------------------
    scholarships = []
    for i in range(5):
        s = Scholarship(
            title=f"Pitt State Gorilla Scholarship {i+1}",
            description=fake.paragraph(nb_sentences=3),
            amount=random.randint(1000, 5000),
            deadline=date.today() + timedelta(days=random.randint(30, 120)),
            department=random.choice(dept_names),
            is_active=True,
        )
        scholarships.append(s)
    db.session.add_all(scholarships)
    db.session.commit()

    # Scholarship Applications
    for u in demo_users[:3]:
        for s in random.sample(scholarships, 2):
            app = ScholarshipApplication(user=u, scholarship=s, status=random.choice(["draft", "submitted", "awarded"]), progress=random.randint(20, 100))
            db.session.add(app)
    db.session.commit()

    # Essays
    for u in demo_users[:2]:
        e = Essay(user=u, title="My PSU Journey", content=fake.paragraph(nb_sentences=5))
        db.session.add(e)
    db.session.commit()

    # ---------------------------------------------
    # Groups & Messages
    # ---------------------------------------------
    group = Group(name="Gorilla Scholars", description="A community for top-performing PSU students.")
    db.session.add(group)
    db.session.commit()

    members = [GroupMember(group=group, user=u, role="member") for u in demo_users[:4]]
    db.session.add_all(members)
    db.session.commit()

    for m in members:
        msg = GroupMessage(group=group, sender=m.user, content=fake.sentence())
        db.session.add(msg)
    db.session.commit()

    # ---------------------------------------------
    # Mentorships
    # ---------------------------------------------
    for i in range(2):
        mentor = random.choice(demo_users)
        mentee = random.choice(demo_users)
        if mentor.id != mentee.id:
            mship = Mentorship(mentor=mentor, mentee=mentee, notes="Helping with career readiness and scholarships.")
            db.session.add(mship)
    db.session.commit()

    # ---------------------------------------------
    # Events
    # ---------------------------------------------
    events = []
    for i in range(5):
        ev = Event(
            title=f"Gorilla Networking Night {i+1}",
            date=date.today() + timedelta(days=i*7),
            location=random.choice(["Overman Student Center", "Kelce Atrium", "Bicknell Center"]),
            description="Meet with employers and alumni for professional development."
        )
        events.append(ev)
    db.session.add_all(events)
    db.session.commit()

    for ev in events:
        rsvp = EventRSVP(event=ev, user=random.choice(demo_users))
        db.session.add(rsvp)
    db.session.commit()

    # ---------------------------------------------
    # Badges
    # ---------------------------------------------
    badges = [
        Badge(slug="gorilla-scholar", name="Gorilla Scholar", description="Awarded for academic excellence."),
        Badge(slug="community-champion", name="Community Champion", description="Active in PSU community initiatives."),
        Badge(slug="career-leader", name="Career Leader", description="Demonstrated career engagement.")
    ]
    db.session.add_all(badges)
    db.session.commit()

    for u in demo_users[:3]:
        ub = UserBadge(user=u, badge=random.choice(badges), reason="For outstanding participation in PSU programs.")
        db.session.add(ub)
    db.session.commit()

    # ---------------------------------------------
    # Donors & Impact Stories
    # ---------------------------------------------
    donors = []
    for i in range(3):
        d = Donor(name=fake.name(), organization=random.choice(["PSU Foundation", "Gorilla Pride Alumni", "Commerce Bank"]), contact_email=fake.email())
        donors.append(d)
    db.session.add_all(donors)
    db.session.commit()

    for d in donors:
        donation = Donation(donor=d, amount=random.randint(1000, 10000), note="Supporting PSU scholarships.")
        db.session.add(donation)
    db.session.commit()

    stories = []
    for i in range(3):
        story = ImpactStory(title=f"Gorilla Success Story {i+1}", body=fake.paragraph(nb_sentences=5), photo_url="https://www.pittstate.edu/_resources/images/psu-logo.png")
        stories.append(story)
    db.session.add_all(stories)
    db.session.commit()

    # ---------------------------------------------
    # Opportunities
    # ---------------------------------------------
    for i in range(5):
        opp = Opportunity(
            title=f"Internship Opportunity {i+1}",
            category=random.choice(["Internship", "Research", "Volunteer"]),
            description=fake.paragraph(nb_sentences=3),
            location="Pittsburg, KS",
            deadline=date.today() + timedelta(days=random.randint(30, 90)),
        )
        db.session.add(opp)
    db.session.commit()

    # ---------------------------------------------
    # Feed / Announcements
    # ---------------------------------------------
    for u in demo_users[:3]:
        fitem = FeedItem(user=u, content="Excited to announce I’ve been accepted into the Gorilla Scholars program!")
        db.session.add(fitem)
    db.session.commit()

    ann = Announcement(title="Welcome to PittState-Connect!", body="Explore scholarships, mentors, and alumni networks all in one place.", is_public=True)
    db.session.add(ann)
    db.session.commit()

    # ---------------------------------------------
    # Campus / Marketing / Emails
    # ---------------------------------------------
    locs = [
        CampusLocation(name="Overman Student Center", latitude=37.3912, longitude=-94.7025, category="building"),
        CampusLocation(name="Bicknell Family Center for the Arts", latitude=37.3921, longitude=-94.7041, category="building")
    ]
    db.session.add_all(locs)
    db.session.commit()

    for i in range(3):
        lead = MarketingLead(email=fake.email(), name=fake.name(), source="landing_page")
        db.session.add(lead)
    db.session.commit()

    print("✅ PSU demo seed complete.")


if __name__ == "__main__":
    from app_pro import create_app
    app = create_app()
    with app.app_context():
        seed_all()
