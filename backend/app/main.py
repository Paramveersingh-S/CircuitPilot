from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
import os
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles


from app.agent.orchestrator import Orchestrator
from app.agent.session import SessionManager

load_dotenv()

app = FastAPI(title="CircuitPilot Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize global managers
session_manager = SessionManager()
orchestrator = Orchestrator()

os.makedirs("d:/Projects/CircuitPilotv1/workspaces", exist_ok=True)
app.mount("/workspaces", StaticFiles(directory="d:/Projects/CircuitPilotv1/workspaces"), name="workspaces")

@app.get("/")
def read_root():
    return {"message": "CircuitPilot Backend is running"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = session_manager.create_session()
    
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            if payload.get("type") == "user_command":
                user_text = payload.get("text", "")
                await orchestrator.handle_command(session_manager, session_id, user_text, websocket)
                
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        print(f"WebSocket Error: {e}")
