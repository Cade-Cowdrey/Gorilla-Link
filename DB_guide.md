# 🏛️ PittState-Connect | Database Management Developer Guide

---

## 📦 Purpose
This guide explains how to manage your **PostgreSQL database** and **Alembic migrations** for PittState-Connect using the unified CLI tooling system (`db_tools.sh` + seed scripts).

Everything below works both **locally** and in **Render Shell**.

---

## 🚀 Quick Commands

Run all commands from your project root:

```bash
./db_tools.sh migrate "add_new_model"
# → Auto-generates and applies a new migration file.

./db_tools.sh check
# → Verifies your DB and models.py are fully synchronized.

flask db upgrade
# → Manually apply all unapplied migrations.

flask db downgrade
# → Roll back the last migration (use cautiously).

flask db current
# → Show current migration revision applied to DB.
