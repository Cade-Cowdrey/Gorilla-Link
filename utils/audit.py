# utils/audit.py
from __future__ import annotations
from datetime import datetime
from typing import Optional, Mapping, Any
from flask import request, g, current_app
from loguru import logger

def audit(action: str, entity: str, entity_id: Optional[str] = None, meta: Optional[Mapping[str, Any]] = None):
    """
    Lightweight audit log to stdout (Render log drain) with optional DB hook.
    Integrate later with a dedicated Audit table if needed.
    """
    user = getattr(g, "current_user_email", None) or getattr(getattr(g, "user", None), "email", None)
    payload = {
        "ts": datetime.utcnow().isoformat(),
        "ip": request.headers.get("X-Forwarded-For", request.remote_addr),
        "user": user,
        "action": action,
        "entity": entity,
        "entity_id": entity_id,
        "meta": dict(meta or {}),
        "ua": request.headers.get("User-Agent")
    }
    logger.bind(channel="audit").info(payload)
    # OPTIONAL: persist to DB if configured
    if current_app.config.get("AUDIT_TO_DB"):
        db = current_app.extensions.get("sqlalchemy").db
        Audit = current_app.audit_model  # set this in app_pro when model defined
        db.session.add(Audit(**payload))
        db.session.commit()
