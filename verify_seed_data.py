"""
verify_seed_data.py
----------------------------------------------------
Utility script to verify seeded demo data for PittState-Connect.

Checks all core tables created by Alembic migrations up to 0025.
Run this inside Render or locally after `flask db upgrade`.

Usage:
    $ python verify_seed_data.py
----------------------------------------------------
"""

import os
from datetime import datetime
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

def check_table(model, label):
    """Count rows in a given table safely."""
    try:
        count = db.session.query(model).count()
        console.print(f"✅ [bold green]{label}[/bold green]: {count} records found")
        return count
    except Exception as e:
        console.print(f"❌ [bold red]{label}[/bold red]: Error -> {e}")
        return 0


def main():
    console.print("\n[bold cyan]🔍 Verifying PittState-Connect Demo Data[/bold cyan]")
    console.print(f"🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n")

    with app.app_context():
        table = Table(title="PittState-Connect Seed Data Verification")
        table.add_column("Table", justify="left", style="bold yellow")
        table.add_column("Count", justify="center")
        table.add_column("Status", justify="left")

        # Check all relevant tables
        tables_to_check = [
            (User, "Users"),
            (Connection, "Connections"),
            (Job, "Jobs"),
            (Event, "Events"),
            (DigestArchive, "Digest Archives"),
            (EmailDigestLog, "Email Digest Logs"),
        ]

        for model, label in tables_to_check:
            try:
                count = db.session.query(model).count()
                status = "[green]OK[/green]" if count > 0 else "[red]Empty[/red]"
                table.add_row(label, str(count), status)
            except Exception as e:
                table.add_row(label, "Error", f"[red]{e}[/red]")

        console.print(table)

        # Show quick validation summary
        console.print("\n[bold white on blue] Summary [/bold white on blue]")
        console.print("✅ If all tables show non-zero counts, your demo data is loaded correctly.")
        console.print("⚠️ If any table is empty, run `flask db upgrade` again or check seed migration logs.\n")

        # Optional detailed view of top jobs and events
        try:
            jobs = Job.query.limit(3).all()
            if jobs:
                console.print("\n💼 [bold cyan]Top Demo Jobs:[/bold cyan]")
                for j in jobs:
                    console.print(f"  • {j.title} at {j.company} ({j.location})")

            events = Event.query.limit(3).all()
            if events:
                console.print("\n🎟️ [bold cyan]Upcoming Demo Events:[/bold cyan]")
                for e in events:
                    console.print(f"  • {e.title} — {e.location} on {e.event_date.strftime('%Y-%m-%d') if e.event_date else 'TBA'}")
        except Exception as e:
            console.print(f"\n⚠️ Error fetching sample records: {e}")

    console.print("\n[green]Verification complete.[/green]\n")


if __name__ == "__main__":
    main()
