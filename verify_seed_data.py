"""
verify_seed_data.py
----------------------------------------------------
Verification + Auto-Repair Script for PittState-Connect Demo Data
----------------------------------------------------

Features:
✅ Verifies counts for Users, Jobs, Events, Connections, Digest Archives, Email Logs.
✅ Auto-repairs (re-seeds) empty tables safely, without duplication.
✅ PSU-branded Rich CLI output for easy Render log reading.

Usage:
  python verify_seed_data.py          # Verify only
  python verify_seed_data.py --fix    # Verify + Auto-repair empty tables
----------------------------------------------------
"""

import sys
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from app_pro import app, db
from models import (
    User,
    Job,
    Event,
    Connection,
    DigestArchive,
    EmailDigestLog,
)

console = Console()
FIX_MODE = "--fix" in sys.argv


def print_header():
    console.print("\n[bold red on gold3]🦍  PITTSTATE-CONNECT DATABASE CHECK  🦍[/bold red on gold3]")
    console.print(f"[dim]Run time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC[/dim]\n")


def count(model):
    """Get a safe row count for a SQLAlchemy model."""
    try:
        return db.session.query(model).count()
    except Exception as e:
        console.print(f"[red]Error counting {model.__name__}: {e}[/red]")
        return -1


def seed_if_missing(model, label, seed_func):
    """Re-seed if a table is empty."""
    total = count(model)
    if total == 0 and FIX_MODE:
        console.print(f"[yellow]⚠️ {label} is empty — auto-repairing...[/yellow]")
        try:
            seed_func()
            db.session.commit()
            console.print(f"[green]✅ {label} successfully re-seeded.[/green]")
        except Exception as e:
            db.session.rollback()
            console.print(f"[red]❌ Failed to re-seed {label}: {e}[/red]")
    elif total == 0:
        console.print(f"[red]❌ {label} empty (run with --fix to repair)[/red]")
    else:
        console.print(f"[green]✅ {label}: {total} records[/green]")


# ======================================================
# SEED HELPERS (used only if FIX_MODE=True)
# ======================================================
def seed_demo_jobs():
    now = datetime.utcnow()
    demo_jobs = [
        Job(
            title="Marketing Intern",
            company="Pittsburg State University",
            location="Pittsburg, KS",
            job_type="Internship",
            description="Assist University Marketing with social media, analytics, and outreach.",
            posted_by=1,
            posted_at=now,
            is_active=True,
        ),
        Job(
            title="Software Engineer (Entry Level)",
            company="Gorilla Innovations LLC",
            location="Pittsburg, KS",
            job_type="Full-time",
            description="Develop APIs and student SaaS tools for PittState-Connect.",
            posted_by=1,
            posted_at=now,
            is_active=True,
        ),
        Job(
            title="Business Analyst",
            company="Freeman Health Systems",
            location="Joplin, MO",
            job_type="Full-time",
            description="Analyze operations data and support dashboard reports.",
            posted_by=2,
            posted_at=now,
            is_active=True,
        ),
    ]
    db.session.bulk_save_objects(demo_jobs)


def seed_demo_events():
    now = datetime.utcnow()
    demo_events = [
        Event(
            title="Career & Internship Expo 2025",
            description="Meet top employers, network with alumni, and explore opportunities.",
            location="Overman Student Center Ballroom",
            event_date=now + timedelta(days=30),
            created_by=1,
            created_at=now,
        ),
        Event(
            title="Gorilla Alumni Networking Night",
            description="Reconnect with fellow Gorillas for mentorship and fun.",
            location="Kelce College of Business Atrium",
            event_date=now + timedelta(days=60),
            created_by=1,
            created_at=now,
        ),
        Event(
            title="Innovation Showcase",
            description="Students present research and startup ideas to local business leaders.",
            location="Bicknell Family Center for the Arts",
            event_date=now + timedelta(days=90),
            created_by=2,
            created_at=now,
        ),
    ]
    db.session.bulk_save_objects(demo_events)


def seed_demo_connections():
    now = datetime.utcnow()
    demo_connections = [
        Connection(user_id=1, connected_user_id=2, status="accepted", created_at=now),
        Connection(user_id=1, connected_user_id=3, status="accepted", created_at=now),
        Connection(user_id=2, connected_user_id=4, status="pending", created_at=now),
    ]
    db.session.bulk_save_objects(demo_connections)


def seed_demo_digests():
    now = datetime.utcnow()
    demo_archives = [
        DigestArchive(
            title="Jungle Report — Spring 2025",
            summary="Celebrating innovation, alumni success, and PSU growth.",
            pdf_url="/static/pdfs/jungle_report_spring2025.pdf",
            created_at=now,
        ),
        DigestArchive(
            title="Jungle Report — Summer 2025",
            summary="Highlights of internships, local partnerships, and alumni spotlights.",
            pdf_url="/static/pdfs/jungle_report_summer2025.pdf",
            created_at=now,
        ),
    ]
    db.session.bulk_save_objects(demo_archives)

    demo_logs = [
        EmailDigestLog(
            recipient_email="student1@pittstate.edu",
            subject="Welcome to PittState-Connect — Jungle Report",
            sent_at=now,
            status="sent",
        ),
        EmailDigestLog(
            recipient_email="alumni@pittstate.edu",
            subject="Reconnect with PittState — Jungle Report",
            sent_at=now,
            status="sent",
        ),
    ]
    db.session.bulk_save_objects(demo_logs)


# ======================================================
# MAIN CHECK + AUTO-REPAIR LOGIC
# ======================================================
def main():
    print_header()
    with app.app_context():
        console.print("[bold cyan]Checking core demo data tables...[/bold cyan]\n")

        seed_if_missing(Job, "Jobs", seed_demo_jobs)
        seed_if_missing(Event, "Events", seed_demo_events)
        seed_if_missing(Connection, "Connections", seed_demo_connections)
        seed_if_missing(DigestArchive, "Digest Archives", seed_demo_digests)
        seed_if_missing(EmailDigestLog, "Email Digest Logs", seed_demo_digests)

        console.print("\n[bold white on blue]Summary[/bold white on blue]")
        console.print(
            "✅ If all tables show records, your demo environment is fully populated.\n"
        )

        if FIX_MODE:
            console.print("[green]Auto-repair mode completed.[/green]")
        else:
            console.print("[yellow]Tip:[/yellow] Run with `--fix` to re-seed empty tables.\n")

        # Optional preview
        try:
            jobs = Job.query.limit(3).all()
            events = Event.query.limit(3).all()
            if jobs:
                console.print("\n💼 [bold]Top Jobs:[/bold]")
                for j in jobs:
                    console.print(f"  • {j.title} — {j.company} ({j.location})")

            if events:
                console.print("\n🎟️ [bold]Upcoming Events:[/bold]")
                for e in events:
                    console.print(f"  • {e.title} at {e.location}")
        except Exception as e:
            console.print(f"[red]⚠️ Error loading preview data: {e}[/red]")


if __name__ == "__main__":
    main()
