"""
CircuitPilot — SQLite Session Database (Phase A + B)
-----------------------------------------------------
Replaces the ephemeral in-memory dict with a persistent SQLite store.
Survives server restarts. Stores full prompt/component history per session
for Phase B contextual memory.
"""
import sqlite3
import json
import uuid
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "circuitpilot.db")
DB_PATH = os.path.abspath(DB_PATH)


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist. Called once on startup."""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id   TEXT PRIMARY KEY,
                created_at   TEXT NOT NULL,
                updated_at   TEXT NOT NULL,
                context_json TEXT NOT NULL DEFAULT '{}'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS circuit_history (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id      TEXT NOT NULL,
                prompt          TEXT NOT NULL,
                components_json TEXT NOT NULL,
                board_path      TEXT,
                created_at      TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role       TEXT NOT NULL,
                content    TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        conn.commit()


# ─── Session CRUD ──────────────────────────────────────────────────────────────

def create_session(session_id: Optional[str] = None) -> str:
    sid = session_id or str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    with _get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO sessions (session_id, created_at, updated_at, context_json) VALUES (?,?,?,?)",
            (sid, now, now, "{}")
        )
        conn.commit()
    return sid


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        if not row:
            return None
        history = conn.execute(
            "SELECT role, content FROM chat_history WHERE session_id = ? ORDER BY id ASC",
            (session_id,)
        ).fetchall()
        return {
            "session_id": row["session_id"],
            "context": json.loads(row["context_json"]),
            "history": [{"role": r["role"], "content": r["content"]} for r in history]
        }


def update_session(session_id: str, context: dict, new_messages: List[Dict]):
    now = datetime.utcnow().isoformat()
    with _get_conn() as conn:
        conn.execute(
            "UPDATE sessions SET context_json = ?, updated_at = ? WHERE session_id = ?",
            (json.dumps(context), now, session_id)
        )
        for msg in new_messages:
            conn.execute(
                "INSERT INTO chat_history (session_id, role, content, created_at) VALUES (?,?,?,?)",
                (session_id, msg["role"], msg["content"], now)
            )
        conn.commit()


# ─── Circuit History (Phase B Memory) ─────────────────────────────────────────

def save_circuit(session_id: str, prompt: str, components: dict, board_path: str = ""):
    """Record every generated board for contextual memory."""
    now = datetime.utcnow().isoformat()
    with _get_conn() as conn:
        conn.execute(
            """INSERT INTO circuit_history
               (session_id, prompt, components_json, board_path, created_at)
               VALUES (?,?,?,?,?)""",
            (session_id, prompt, json.dumps(components), board_path, now)
        )
        conn.commit()


def get_circuit_memory(session_id: str, limit: int = 3) -> List[Dict]:
    """
    Return the last `limit` circuits built in this session.
    Used to inject memory context into the Planner prompt (Phase B).
    """
    with _get_conn() as conn:
        rows = conn.execute(
            """SELECT prompt, components_json FROM circuit_history
               WHERE session_id = ?
               ORDER BY id DESC LIMIT ?""",
            (session_id, limit)
        ).fetchall()
    results = []
    for r in reversed(rows):   # chronological order
        results.append({
            "prompt": r["prompt"],
            "components": json.loads(r["components_json"])
        })
    return results
