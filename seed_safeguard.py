# ==============================================================
# seed_safeguard.py — Safe automatic seeder for Render
# ==============================================================

from extensions import db
from models import Department, Faculty, Alumni
from seed_departments_faculty import run_seed as seed_dept
from seed_alumni import app as alumni_app  # ensures context loading

def ensure_minimum_seed(app):
    """Check if essential tables are populated; seed if empty."""
    with app.app_context():
        dept_count = db.session.query(Department).count()
        alum_count = db.session.query(Alumni).count()

        if dept_count == 0:
            print("⚙️  No departments found — running seed_departments_faculty.py")
            try:
                seed_dept()
                print("✅ Departments and faculty seeded.")
            except Exception as e:
                print("❌ Failed to seed departments:", e)

        if alum_count == 0:
            print("⚙️  No alumni found — running seed_alumni.py")
            try:
                import seed_alumni
            except Exception as e:
                print("❌ Failed to seed alumni:", e)

        print("🟢 Database verified and ready.")
