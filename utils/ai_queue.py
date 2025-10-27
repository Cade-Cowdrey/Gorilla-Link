"""
AI queue helpers for PittState-Connect.

Enhancements:
- Simple, typed enqueue helpers for common AI jobs
- Generic enqueue for custom tasks
- Redis fallback creation if extensions.redis_client is missing
- Defensive logging + input validation
"""

import os
import json
from typing import Optional, Dict, Any

from loguru import logger

# --- Redis helper -------------------------------------------------------------
def _get_redis():
    try:
        from extensions import redis_client as shared_client  # type: ignore
        if shared_client:
            return shared_client
    except Exception:
        pass
    REDIS_URL = os.getenv("REDIS_URL") or os.getenv("REDIS_TLS_URL")
    if not REDIS_URL:
        return None
    try:
        import redis  # type: ignore
        return redis.from_url(REDIS_URL, decode_responses=True, retry_on_timeout=True)
    except Exception as e:
        logger.error("ai_queue: Redis unavailable: {}", e)
        return None


redis_client = _get_redis()
AI_QUEUE_KEY = os.getenv("AI_QUEUE_KEY", "queue:ai")


def _push(payload: Dict[str, Any]) -> bool:
    if not redis_client:
        logger.warning("ai_queue: Redis not configured; cannot enqueue payload: {}", payload)
        return False
    try:
        redis_client.lpush(AI_QUEUE_KEY, json.dumps(payload))
        logger.info("ai_queue: enqueued -> {}", payload.get("type", "unknown"))
        return True
    except Exception as e:
        logger.error("ai_queue: enqueue failed: {}", e)
        return False


def enqueue_essay_feedback(student_id: int, text: str, model: str = "gpt-4o-mini") -> bool:
    if not isinstance(student_id, int) or not text or not text.strip():
        logger.warning("enqueue_essay_feedback: invalid inputs")
        return False
    return _push({
        "type": "essay_feedback",
        "student_id": student_id,
        "text": text,
        "model": model
    })


def enqueue_smartmatch_training(dataset: str = "internal") -> bool:
    return _push({
        "type": "smart_match_train",
        "dataset": dataset,
    })


def enqueue_generic(task_type: str, **kwargs) -> bool:
    if not task_type:
        logger.warning("enqueue_generic: missing task_type")
        return False
    payload = {"type": task_type}
    payload.update(kwargs)
    return _push(payload)
