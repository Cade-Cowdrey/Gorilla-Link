"""
utils/ai_queue.py
-------------------------------------------------------------
PittState-Connect AI Queue Utility
-------------------------------------------------------------
• Enqueues essay feedback, Smart-Match, and analytics tasks
• Redis fallback creation if extensions missing
• Type-safe helpers
• Logging and safe validation
"""

import os
import json
from typing import Any, Dict
from loguru import logger


def get_redis():
    try:
        from extensions import redis_client as shared
        if shared:
            return shared
    except Exception:
        pass
    url = os.getenv("REDIS_URL") or os.getenv("REDIS_TLS_URL")
    if not url:
        return None
    try:
        import redis
        return redis.from_url(url, decode_responses=True, retry_on_timeout=True)
    except Exception as e:
        logger.error("AI Queue Redis unavailable: {}", e)
        return None


redis_client = get_redis()
AI_QUEUE_KEY = os.getenv("AI_QUEUE_KEY", "queue:ai")


def _push(payload: Dict[str, Any]) -> bool:
    if not redis_client:
        logger.warning("Redis not configured; cannot enqueue -> {}", payload)
        return False
    try:
        redis_client.lpush(AI_QUEUE_KEY, json.dumps(payload))
        logger.info("Enqueued AI task -> {}", payload.get("type", "unknown"))
        return True
    except Exception as e:
        logger.error("AI enqueue failed: {}", e)
        return False


def enqueue_essay_feedback(student_id: int, text: str, model: str = "gpt-4o-mini") -> bool:
    if not isinstance(student_id, int) or not text.strip():
        logger.warning("Invalid essay feedback inputs")
        return False
    return _push({
        "type": "essay_feedback",
        "student_id": student_id,
        "text": text.strip(),
        "model": model
    })


def enqueue_smartmatch_training(dataset: str = "internal") -> bool:
    return _push({
        "type": "smart_match_train",
        "dataset": dataset
    })


def enqueue_analytics_refresh() -> bool:
    return _push({
        "type": "analytics_refresh"
    })


def enqueue_generic(task_type: str, **kwargs) -> bool:
    if not task_type:
        logger.warning("Missing task_type")
        return False
    payload = {"type": task_type}
    payload.update(kwargs)
    return _push(payload)
