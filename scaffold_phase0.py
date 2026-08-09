import os

dirs = [
    "backend/app/agent/tools",
    "backend/app/kicad_host",
    "backend/app/projects",
    "backend/app/ws",
    "backend/tests/golden_circuits",
    "frontend/src/components",
    "frontend/src/ws",
    "atopile_packages",
    "docs"
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

with open("docker-compose.yml", "w") as f:
    f.write("""version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    environment:
      - KICAD_HOST_URL=http://kicad-host:5000

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app

  kicad-host:
    image: kicad/kicad:9.0
    ports:
      - "5000:5000"
    command: kicad-cli server --headless
""")

with open("backend/pyproject.toml", "w") as f:
    f.write("""[project]
name = "circuitpilot-backend"
version = "0.1.0"
dependencies = [
    "fastapi",
    "uvicorn[standard]",
    "websockets",
    "kicad-python",
    "atopile"
]
""")

with open("backend/app/main.py", "w") as f:
    f.write("""from fastapi import FastAPI, WebSocket
from .kicad_host.session_manager import SessionManager

app = FastAPI(title="CircuitPilot API")
session_manager = SessionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")
""")

with open("backend/app/kicad_host/session_manager.py", "w") as f:
    f.write("""class SessionManager:
    def __init__(self):
        self.sessions = {}

    def get_session(self, session_id):
        if session_id not in self.sessions:
            self.sessions[session_id] = self._create_session(session_id)
        return self.sessions[session_id]
        
    def _create_session(self, session_id):
        return {"id": session_id, "status": "active"}
""")

with open("frontend/package.json", "w") as f:
    f.write("""{
  "name": "circuitpilot-frontend",
  "version": "0.1.0",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@theacodes/kicanvas": "^1.0.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.0.0",
    "typescript": "^5.0.0",
    "vite": "^4.0.0"
  }
}
""")

with open("frontend/src/components/BoardCanvas.tsx", "w") as f:
    f.write("""import React, { useEffect, useRef } from 'react';

export const BoardCanvas: React.FC<{ fileUrl: string }> = ({ fileUrl }) => {
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // KiCanvas initialization logic
        if (containerRef.current) {
            containerRef.current.innerHTML = `<kicanvas-embed src="${fileUrl}"></kicanvas-embed>`;
        }
    }, [fileUrl]);

    return <div ref={containerRef} style={{ width: '100%', height: '100%' }} />;
};
""")

with open(".gitignore", "w") as f:
    f.write("""node_modules/
__pycache__/
*.pyc
.env
dist/
build/
""")
