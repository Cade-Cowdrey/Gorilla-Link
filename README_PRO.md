
# Pitt State Connect — Pro v2

Adds:
- Hosted real building photos (via `data/image_links.json`)
- Custom OG banner for social sharing
- Admin CSV export endpoints
- Department hero partial include
- Everything from Pro v1 (OAuth, Gmail, dashboards, internships, feedback, search, highlights)

## Run
pip install -r requirements.txt
export SECRET_KEY=dev ADMIN_SECRET=changeme DATABASE_URL=sqlite:///pittstate_connect.db
export OAUTH_CLIENT_ID=xxx OAUTH_CLIENT_SECRET=yyy OAUTH_ALLOWED_DOMAIN=gus.pittstate.edu
export MAIL_USERNAME=connorvandenberg06@gmail.com MAIL_PASSWORD=<app_pw> MAIL_DEFAULT_SENDER=connorvandenberg06@gmail.com
python app_pro.py

## CSV Export
/admin/export/<students|alumni|opportunities|feedback>?token=ADMIN_SECRET
