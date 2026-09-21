"""
CircuitPilot — DB-backed Session Manager
Replaces the ephemeral in-memory dict with SQLite persistence.
"""
import uuid
from typing import Optional
from app.db import (
    create_session as db_create,
    get_session as db_get,
    update_session as db_update,
)


class SessionManager:
    """
    Drop-in replacement for the old in-memory SessionManager.
    All state is persisted to SQLite so it survives server restarts.
    """

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        db_create(session_id)
        return session_id

    def get_session(self, session_id: str) -> Optional[dict]:
        """Returns session dict or None if not found."""
        return db_get(session_id)

    def update_session(self, session_id: str, context: dict, history: list):
        """
        Persist context and append new chat messages.
        `history` here is the FULL list; we diff and store only the tail.
        For simplicity we store the last 2 messages (user + assistant pair).
        """
        new_messages = history[-2:] if len(history) >= 2 else history
        db_update(session_id, context, new_messages)
