from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from . import config

LEAD_COLUMNS = [
    "name",
    "company",
    "email",
    "phone",
    "need",
    "budget",
    "timeline",
    "decision_role",
    "interest_level",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    Path(config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS leads (
                session_id TEXT PRIMARY KEY,
                name TEXT,
                company TEXT,
                email TEXT,
                phone TEXT,
                need TEXT,
                budget TEXT,
                timeline TEXT,
                decision_role TEXT,
                interest_level TEXT,
                score INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'cold',
                sentiment TEXT NOT NULL DEFAULT 'neutral',
                sentiment_score REAL NOT NULL DEFAULT 0,
                stage TEXT NOT NULL DEFAULT 'greeting',
                crm_synced_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                slot_id TEXT NOT NULL,
                slot_iso TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'booked',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS calls (
                session_id TEXT PRIMARY KEY,
                summary_json TEXT NOT NULL,
                duration_seconds INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
            CREATE INDEX IF NOT EXISTS idx_appointments_session ON appointments(session_id);
            """
        )


def get_lead(session_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM leads WHERE session_id = ?", (session_id,)
        ).fetchone()
    return dict(row) if row else None


def upsert_lead(
    session_id: str,
    profile: dict[str, Any],
    score: int,
    status: str,
    sentiment: str,
    sentiment_score: float,
    stage: str,
) -> dict[str, Any]:
    """Merge new lead information into the CRM record and stamp the sync time."""
    existing = get_lead(session_id) or {}
    now = utc_now()

    values = {column: existing.get(column) for column in LEAD_COLUMNS}
    for key, value in (profile or {}).items():
        if key in LEAD_COLUMNS and value not in (None, ""):
            values[key] = str(value)[:500]

    created_at = existing.get("created_at") or now

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO leads (
                session_id, name, company, email, phone, need, budget, timeline,
                decision_role, interest_level, score, status, sentiment,
                sentiment_score, stage, crm_synced_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                name = excluded.name,
                company = excluded.company,
                email = excluded.email,
                phone = excluded.phone,
                need = excluded.need,
                budget = excluded.budget,
                timeline = excluded.timeline,
                decision_role = excluded.decision_role,
                interest_level = excluded.interest_level,
                score = excluded.score,
                status = excluded.status,
                sentiment = excluded.sentiment,
                sentiment_score = excluded.sentiment_score,
                stage = excluded.stage,
                crm_synced_at = excluded.crm_synced_at,
                updated_at = excluded.updated_at
            """,
            (
                session_id,
                values["name"],
                values["company"],
                values["email"],
                values["phone"],
                values["need"],
                values["budget"],
                values["timeline"],
                values["decision_role"],
                values["interest_level"],
                int(score),
                status,
                sentiment,
                float(sentiment_score),
                stage,
                now,
                created_at,
                now,
            ),
        )
    return get_lead(session_id) or {}


def list_leads(limit: int = 20) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM leads ORDER BY updated_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(row) for row in rows]


def book_appointment(session_id: str, slot_id: str, slot_iso: str) -> bool:
    """Reserve a slot. Returns False if another call already booked it."""
    try:
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO appointments (session_id, slot_id, slot_iso, status, created_at)
                VALUES (?, ?, ?, 'booked', ?)
                """,
                (session_id, slot_id, slot_iso, utc_now()),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def list_booked_slot_isos() -> set[str]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT slot_iso FROM appointments WHERE status = 'booked'"
        ).fetchall()
    return {row["slot_iso"] for row in rows}


def list_appointments(limit: int = 20) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT a.*, l.name AS lead_name, l.company AS lead_company
            FROM appointments a
            LEFT JOIN leads l ON l.session_id = a.session_id
            ORDER BY a.created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def save_call(session_id: str, summary: dict[str, Any], duration_seconds: int) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO calls (session_id, summary_json, duration_seconds, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                summary_json = excluded.summary_json,
                duration_seconds = excluded.duration_seconds,
                created_at = excluded.created_at
            """,
            (
                session_id,
                json.dumps(summary, ensure_ascii=False),
                int(duration_seconds),
                utc_now(),
            ),
        )


def get_call(session_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM calls WHERE session_id = ?", (session_id,)
        ).fetchone()
    if not row:
        return None
    data = dict(row)
    data["summary"] = json.loads(data.pop("summary_json"))
    return data


def insights() -> dict[str, Any]:
    with _connect() as conn:
        lead_row = conn.execute(
            """
            SELECT
                COUNT(*) AS total_leads,
                COALESCE(SUM(CASE WHEN status = 'hot' THEN 1 ELSE 0 END), 0) AS hot_leads,
                COALESCE(SUM(CASE WHEN status = 'warm' THEN 1 ELSE 0 END), 0) AS warm_leads,
                COALESCE(AVG(score), 0) AS avg_score,
                COALESCE(SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END), 0)
                    AS positive_leads
            FROM leads
            """
        ).fetchone()
        meetings = conn.execute(
            "SELECT COUNT(*) FROM appointments WHERE status = 'booked'"
        ).fetchone()[0]
        calls = conn.execute("SELECT COUNT(*) FROM calls").fetchone()[0]

    total = int(lead_row["total_leads"] or 0)
    positive = int(lead_row["positive_leads"] or 0)
    return {
        "total_leads": total,
        "hot_leads": int(lead_row["hot_leads"] or 0),
        "warm_leads": int(lead_row["warm_leads"] or 0),
        "meetings_booked": int(meetings or 0),
        "calls_completed": int(calls or 0),
        "avg_score": round(float(lead_row["avg_score"] or 0), 1),
        "positive_sentiment_pct": round((positive / total) * 100, 1) if total else 0.0,
    }


def reset_demo_data() -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM calls")
        conn.execute("DELETE FROM appointments")
        conn.execute("DELETE FROM leads")
