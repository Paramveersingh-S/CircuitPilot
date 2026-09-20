import json
import uuid

# In-memory store for immediate demo
_SESSIONS = {}

class SessionManager:
    def __init__(self):
        pass

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        _SESSIONS[session_id] = {"context": {}, "history": []}
        return session_id

    def get_session(self, session_id: str):
        if session_id in _SESSIONS:
            s = _SESSIONS[session_id]
            return {
                "session_id": session_id,
                "context": s["context"],
                "history": s["history"]
            }
        return None

    def update_session(self, session_id: str, context: dict, history: list):
        if session_id in _SESSIONS:
            _SESSIONS[session_id]["context"] = context
            _SESSIONS[session_id]["history"] = history
