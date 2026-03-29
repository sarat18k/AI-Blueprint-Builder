"""SQLite-based run history storage."""

from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "history.db"


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                task TEXT NOT NULL,
                results TEXT NOT NULL,
                timings TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()


def save_run(task: str, results: dict, timings: dict) -> str:
    run_id = uuid.uuid4().hex[:16]
    now = datetime.now(timezone.utc).isoformat()
    try:
        results_json = json.dumps(results, default=str)
        timings_json = json.dumps(timings, default=str)
    except (TypeError, ValueError) as exc:
        logger.error("Failed to serialize run data: %s", exc)
        raise

    with _conn() as conn:
        conn.execute(
            "INSERT INTO runs (id, task, results, timings, created_at) VALUES (?, ?, ?, ?, ?)",
            (run_id, task, results_json, timings_json, now),
        )
        conn.commit()
    return run_id


def list_runs(limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT id, task, created_at FROM runs ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return [{"id": r["id"], "task": r["task"], "created_at": r["created_at"]} for r in rows]


def get_run(run_id: str) -> dict[str, Any] | None:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    if not row:
        return None
    try:
        results = json.loads(row["results"])
    except (json.JSONDecodeError, TypeError):
        results = {}
    try:
        timings = json.loads(row["timings"]) if row["timings"] else {}
    except (json.JSONDecodeError, TypeError):
        timings = {}
    return {
        "id": row["id"],
        "task": row["task"],
        "results": results,
        "timings": timings,
        "created_at": row["created_at"],
    }


def delete_run(run_id: str) -> bool:
    with _conn() as conn:
        cursor = conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))
        conn.commit()
        return cursor.rowcount > 0
