# ==============================================================
# seed_alumni.py — Safe, idempotent alumni + company demo data
# ==============================================================
from datetime import date
from app_pro import create_app
from extensions import db
from models import Alumni, Company, Department, AlumniEmployment

app = create_app()
with app.app_context():
    # Ensure some departments exist
    needed = ["Business Management", "Engineering", "Computer Science", "Education"]
    depts = {d.name: d for d in Department.query.filter(Department.name.in_(needed)).all()}

    # Companies (upsert by name)
    companies = [
        {"name": "Acme Corp", "industry": "Technology", "city": "Kansas City", "state": "KS", "website": "https://acme.example"},
        {"name": "Heartland Health", "industry": "Healthcare", "city": "Wichita", "state": "KS", "website": "https://heartland.example"},
        {"name": "Jayhawk Education", "industry": "Education", "city": "Lawrence", "state": "KS", "website": "https://jayhawk.example"},
    ]
    company_map = {}
    for c in companies:
        obj = Company.query.filter_by(name=c["name"]).first()
        if not obj:
            obj = Company(**c)
            db.session.add(obj)
        company_map[c["name"]] = obj
    db.session.commit()

    # Alumni (upsert by email)
    demo_alumni = [
        {
            "name": "Alex Johnson",
            "email": "alex.johnson@alumni.pittstate.edu",
            "grad_year": 2022,
            "dept": "Computer Science",
            "current_title": "Software Engineer",
            "current_company": "Acme Corp",
            "city": "Pittsburg",
            "state": "KS",
            "linkedin_url": "https://linkedin.com/in/alexjohnson",
            "skills": ["Python", "Flask", "SQL", "Docker"],
            "achievements": ["Dean’s List", "Hackathon Winner"],
            "employments": [
                {"company": "Acme Corp", "title": "Software Engineer", "start": date(2023, 6, 1), "end": None, "current": True}
            ],
        },
        {
            "name": "Maria Lopez",
            "email": "maria.lopez@alumni.pittstate.edu",
            "grad_year": 2021,
            "dept": "Business Management",
            "current_title": "Operations Analyst",
            "current_company": "Acme Corp",
            "city": "Kansas City",
            "state": "MO",
            "linkedin_url": "",
            "skills": ["Excel", "Analytics", "Leadership"],
            "achievements": ["Beta Gamma Sigma"],
            "employments": [
                {"company": "Acme Corp", "title": "Operations Analyst", "start": date(2022, 1, 1), "end": None, "current": True}
            ],
        },
        {
            "name": "Nathan Carter",
            "email": "nathan.carter@alumni.pittstate.edu",
            "grad_year": 2020,
            "dept": "Education",
            "current_title": "Instructor",
            "current_company": "Jayhawk Education",
            "city": "Lawrence",
            "state": "KS",
            "linkedin_url": "",
            "skills": ["Curriculum", "K-12"],
            "achievements": [],
            "employments": [
                {"company": "Jayhawk Education", "title": "Instructor", "start": date(2020, 8, 1), "end": None, "current": True}
            ],
        },
    ]

    for a in demo_alumni:
        dept = depts.get(a["dept"]) or Department.query.filter_by(name=a["dept"]).first()
        alum = Alumni.query.filter_by(email=a["email"]).first()
        if not alum:
            alum = Alumni(
                name=a["name"],
                email=a["email"],
                grad_year=a["grad_year"],
                department_id=dept.id if dept else None,
                current_title=a["current_title"],
                current_company=a["current_company"],
                city=a["city"],
                state=a["state"],
                linkedin_url=a["linkedin_url"],
                skills=a["skills"],
                achievements=a["achievements"],
            )
            db.session.add(alum)
            db.session.flush()  # get alum.id

            # Employment rows (avoid duplicates by (alum_id, company_id, title, start))
            for emp in a["employments"]:
                comp = company_map[emp["company"]]
                exists = AlumniEmployment.query.filter_by(
                    alumni_id=alum.id, company_id=comp.id, title=emp["title"], start_date=emp["start"]
                ).first()
                if not exists:
                    db.session.add(AlumniEmployment(
                        alumni_id=alum.id,
                        company_id=comp.id,
                        title=emp["title"],
                        start_date=emp["start"],
                        end_date=emp["end"],
                        is_current=emp["current"],
                    ))

    db.session.commit()
    print("✅ Alumni + Companies seeded successfully (no duplicates).")
