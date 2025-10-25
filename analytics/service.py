# analytics/service.py
from __future__ import annotations
import io
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from loguru import logger

try:
    from openai import OpenAI
    _openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception:
    _openai = None

@dataclass
class KPI:
    label: str
    value: float
    delta: float = 0.0
    unit: str = ""

class AnalyticsService:
    """
    Provides analytics utilities:
      - KPI aggregation
      - Simple anomaly detection
      - AI weekly insight summaries
      - Chart generation (static PNG)
    """

    def __init__(self, db_session):
        self.db = db_session

    # ---------------------- KPI Aggregation ----------------------
    def compute_core_kpis(self) -> List[KPI]:
        # Replace with real SQL queries; here we stub with predictable structure.
        # Example:
        # users_count = self.db.session.execute(text("select count(*) from users")).scalar()
        # For now, return mock values if DB not wired.
        try:
            users = self._count("users")
            scholarships = self._count("scholarships")
            applications = self._count("applications")
            postings = self._count("job_postings")
        except Exception:
            users, scholarships, applications, postings = (1287, 52, 231, 88)

        return [
            KPI("Active Users", users, delta=+4.3, unit=""),
            KPI("Scholarships", scholarships, delta=+1.0, unit=""),
            KPI("Applications", applications, delta=+7.8, unit=""),
            KPI("Job Postings", postings, delta=-2.1, unit=""),
        ]

    def _count(self, table: str) -> int:
        # Placeholder for real SQLAlchemy models
        raise NotImplementedError

    # ---------------------- Anomaly Detection ----------------------
    @staticmethod
    def detect_anomalies(series: List[float], z_threshold: float = 2.5) -> Tuple[bool, float]:
        """
        Very simple z-score anomaly detector.
        """
        if len(series) < 6:
            return False, 0.0
        arr = np.array(series, dtype=float)
        mean = arr.mean()
        std = arr.std() or 1.0
        z_last = (arr[-1] - mean) / std
        return abs(z_last) >= z_threshold, float(z_last)

    # ---------------------- AI Insight Summaries ----------------------
    def ai_weekly_brief(self, kpis: List[KPI], anomalies: Dict[str, float]) -> str:
        """
        Returns HTML summary (safe to embed in emails). Falls back to a plain brief if OpenAI not configured.
        """
        plain = self._plain_brief(kpis, anomalies)
        if not _openai:
            return plain

        try:
            prompt = (
                "You are an analytics assistant for a university platform. Summarize the weekly performance.\n\n"
                f"KPIs: {[(k.label, k.value, k.delta, k.unit) for k in kpis]}\n"
                f"Anomalies (z-scores): {anomalies}\n"
                "Be concise, actionable, and optimistic. Use <ul> and <li> bullets."
            )
            resp = _openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=300,
            )
            content = resp.choices[0].message.content
            if not content:
                return plain
            return f"<div>{content}</div>"
        except Exception as e:
            logger.warning(f"[AI] Weekly brief fallback due to error: {e}")
            return plain

    def _plain_brief(self, kpis: List[KPI], anomalies: Dict[str, float]) -> str:
        lis = "".join(
            f"<li><strong>{k.label}:</strong> {k.value} ({'+' if k.delta>=0 else ''}{k.delta} {k.unit})</li>"
            for k in kpis
        )
        anom = "".join(
            f"<li><strong>{name}:</strong> z-score {score:.2f} — investigate drivers.</li>"
            for name, score in anomalies.items()
        ) or "<li>No anomalies detected.</li>"
        return f"""
        <h3>PSU Impact Brief</h3>
        <ul>{lis}</ul>
        <h4>Attention Items</h4>
        <ul>{anom}</ul>
        """

    # ---------------------- Chart Generation ----------------------
    def generate_timeseries_chart(self, title: str, series: List[float], output_path: str) -> str:
        """
        Saves a simple line chart to output_path and returns the path.
        """
        x = list(range(len(series)))
        plt.figure(figsize=(8, 3))
        plt.plot(x, series, linewidth=2)
        plt.title(title)
        plt.tight_layout()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=144)
        plt.close()
        return output_path
