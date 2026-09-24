"""
CircuitPilot Backend — FastAPI entry point.
All environment-sensitive paths are driven by env vars.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
import os
from dotenv import load_dotenv
import time

from app.agent.orchestrator import Orchestrator
from app.agent.session import SessionManager
from app.db import init_db, create_user, get_user_by_email, get_user_by_id
from app.auth import hash_password, verify_password, create_access_token, get_current_user_id

load_dotenv()

# ── Environment-driven config ─────────────────────────────────────────────────
WORKSPACES_DIR = os.environ.get("WORKSPACES_DIR", os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "workspaces"
))
WORKSPACES_DIR = os.path.abspath(WORKSPACES_DIR)

FRONTEND_ORIGIN = os.environ.get("FRONTEND_URL", "http://localhost:5173")
BASE_URL        = os.environ.get("BASE_URL", "http://localhost:8000")

APP_START_TIME  = time.time()

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="CircuitPilot API",
    description="AI-Powered PCB Design Backend",
    version="1.0.0",
)

@app.on_event("startup")
async def startup_event():
    """Initialize DB and workspace directory on startup."""
    os.makedirs(WORKSPACES_DIR, exist_ok=True)
    init_db()
    print(f"[CircuitPilot] Started. Workspaces: {WORKSPACES_DIR}")

# ── CORS — explicit origin list in production ─────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://localhost:5173", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files ──────────────────────────────────────────────────────────────
os.makedirs(WORKSPACES_DIR, exist_ok=True)
app.mount("/workspaces", StaticFiles(directory=WORKSPACES_DIR), name="workspaces")

# ── Global managers ───────────────────────────────────────────────────────────
session_manager = SessionManager()
orchestrator    = Orchestrator()

# ── Schemas ───────────────────────────────────────────────────────────────────
class AuthRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str

# ── Routes ────────────────────────────────────────────────────────────────────
@app.post("/auth/register", response_model=AuthResponse)
def register(req: AuthRequest):
    if get_user_by_email(req.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = create_user(req.email, hash_password(req.password))
    token = create_access_token({"sub": user_id})
    return AuthResponse(access_token=token, user_id=user_id)

@app.post("/auth/login", response_model=AuthResponse)
def login(req: AuthRequest):
    user_row = get_user_by_email(req.email)
    if not user_row or not verify_password(req.password, user_row["pwd_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    user_id = user_row["id"]
    token = create_access_token({"sub": user_id})
    return AuthResponse(access_token=token, user_id=user_id)

@app.get("/auth/me")
def get_me(user_id: str = Depends(get_current_user_id)):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user["id"], "email": user["email"]}

@app.get("/")
def read_root():
    return {"message": "CircuitPilot API is running", "version": "1.0.0"}

@app.get("/health")
def health_check():
    """Health check endpoint for Railway / Render / uptime monitors."""
    return JSONResponse({
        "status": "ok",
        "uptime_seconds": round(time.time() - APP_START_TIME, 1),
        "workspaces_dir": WORKSPACES_DIR,
    })

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = session_manager.create_session()

    try:
        while True:
            data    = await websocket.receive_text()
            payload = json.loads(data)

            if payload.get("type") == "user_command":
                user_text = payload.get("text", "")
                await orchestrator.handle_command(
                    session_manager, session_id, user_text, websocket
                )

    except WebSocketDisconnect:
        print(f"[CircuitPilot] WebSocket disconnected: session={session_id}")
    except Exception as e:
        import traceback
        print(f"[CircuitPilot] WebSocket error: {e}\n{traceback.format_exc()}")

