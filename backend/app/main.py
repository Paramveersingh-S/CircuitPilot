from fastapi import FastAPI, WebSocket
from .kicad_host.session_manager import SessionManager

app = FastAPI(title="CircuitPilot API")
session_manager = SessionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")
