
# Deployment Guide (Render + Google OAuth + Gmail)

- Build: `pip install -r requirements.txt`
- Start: `gunicorn app_pro:app`
- Env vars: see `.env.example` from previous bundle or README

Google OAuth:
- Redirect URI: https://<your-domain>/auth/callback
- Allowed domain: gus.pittstate.edu

Hosted images:
- Update links in `data/image_links.json` to point to your CDN or Render Static Assets.
