# utils/audit.py
from __future__ import annotations
from datetime import datetime
from typing import Optional, Mapping, Any
from flask import request, g
from loguru import logger

def audit(action: str, entity: str, entity_id: Optional[str] = None, meta: Optional[Mapping[str, Any]] = None):
    user = getattr(g, "current_user_email", None) or getattr(getattr(g, "user", None), "email", None)
    payload = {
        "ts": datetime.utcnow().isoformat(),
        "ip": request.headers.get("X-Forwarded-For", request.remote_addr),
        "user": user,
        "action": action,
        "entity": entity,
        "entity_id": entity_id,
        "meta": dict(meta or {}),
        "ua": request.headers.get("User-Agent"),
    }
    logger.bind(channel="audit").info(payload)
