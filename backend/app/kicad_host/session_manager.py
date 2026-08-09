class SessionManager:
    def __init__(self):
        self.sessions = {}

    def get_session(self, session_id):
        if session_id not in self.sessions:
            self.sessions[session_id] = self._create_session(session_id)
        return self.sessions[session_id]
        
    def _create_session(self, session_id):
        return {"id": session_id, "status": "active"}
