# ==============================================================
# Gorilla-Link / Pitt State Connect
# seed_departments_faculty.py — Demo Seeder (Idempotent)
# ==============================================================
from app_pro import create_app
from extensions import db
from models import Department, Faculty
from slugify import slugify

app = create_app()

with app.app_context():
    demo_departments = [
        ("Business Management", 243, 120, 51, 91),
        ("Engineering", 201, 90, 36, 88),
        ("Education", 177, 110, 14, 79),
        ("Nursing", 163, 140, 27, 84),
        ("Computer Science", 192, 70, 42, 86),
        ("Psychology", 145, 150, 18, 74),
    ]

    for name, students, alumni, jobs, engagement in demo_departments:
        dept = Department.query.filter_by(name=name).first()
        if not dept:
            dept = Department(
                name=name,
                slug=slugify(name),
                students=students,
                alumni=alumni,
                jobs=jobs,
                engagement=engagement,
                contact_email=f"{name.split()[0].lower()}@pittstate.edu",
                phone="(620) 235-4000"
            )
            db.session.add(dept)
    db.session.commit()

    # 🧑‍🏫 Demo Faculty (Safe insert)
    sample_faculty = [
        {
            "name": "Dr. Robert King",
            "title": "Lecturer, Computer Science",
            "email": "rking@pittstate.edu",
            "dept_name": "Computer Science",
            "research_interests": "AI Ethics and Data Privacy",
            "courses": [
                {"code": "ICS 101", "name": "Intro to Programming", "semester": "Fall 2024"},
                {"code": "ICS 302", "name": "AI & Society", "semester": "Spring 2025"},
            ],
            "publications": [
                {"title": "AI Ethics in Academia", "journal": "TechEd Journal", "year": 2023}
            ],
        },
        {
            "name": "Dr. Emily Carter",
            "title": "Professor of Business",
            "email": "ecarter@pittstate.edu",
            "dept_name": "Business Management",
            "research_interests": "Entrepreneurship and Digital Innovation",
            "courses": [
                {"code": "BUS 210", "name": "Principles of Management", "semester": "Fall 2024"},
                {"code": "BUS 450", "name": "Strategic Leadership", "semester": "Spring 2025"},
            ],
            "publications": [
                {"title": "Digital Leadership in Startups", "journal": "Business Review", "year": 2022}
            ],
        },
    ]

    for fac in sample_faculty:
        if not Faculty.query.filter_by(email=fac["email"]).first():
            dept = Department.query.filter_by(name=fac["dept_name"]).first()
            faculty = Faculty(
                name=fac["name"],
                title=fac["title"],
                email=fac["email"],
                department_id=dept.id if dept else None,
                research_interests=fac["research_interests"],
                courses=fac["courses"],
                publications=fac["publications"],
            )
            db.session.add(faculty)

    db.session.commit()
    print("✅ Departments & Faculty seeded successfully — no duplicates created.")
