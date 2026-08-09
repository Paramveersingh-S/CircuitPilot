from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI(title="CircuitPilot Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "CircuitPilot Backend is running"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for testing in Phase 0
            await websocket.send_text(json.dumps({
                "type": "chat",
                "role": "assistant",
                "text": f"Echo: {json.loads(data).get('text', '')}"
            }))
    except Exception as e:
        print(f"WebSocket Error: {e}")
