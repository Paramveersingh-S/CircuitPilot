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

import asyncio

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            if payload.get("type") == "user_command":
                cmd = payload.get("text", "").lower()
                
                # Acknowledge
                await websocket.send_text(json.dumps({
                    "type": "chat", "role": "assistant", "ts": "0.0s",
                    "text": f"Acknowledged: '{cmd}'. Decomposing task..."
                }))
                await asyncio.sleep(1)
                
                # Simulate tool call
                await websocket.send_text(json.dumps({
                    "type": "tool_call_started", "id": "tc_001", "tool": "ato_search_package",
                    "args": {"query": cmd}, "ts": "1.0s"
                }))
                await asyncio.sleep(1.5)
                await websocket.send_text(json.dumps({
                    "type": "tool_call_completed", "id": "tc_001", 
                    "result": {"matches": [{"name": "esp32_wroom_32e", "version": "1.0.0"}]}, "ts": "2.5s"
                }))
                
                # Simulate placing component
                await websocket.send_text(json.dumps({
                    "type": "chat", "role": "assistant", "ts": "2.6s",
                    "text": "Found a vetted component for the ESP32. Adding it to the schematic..."
                }))
                await asyncio.sleep(1)
                await websocket.send_text(json.dumps({
                    "type": "tool_call_started", "id": "tc_002", "tool": "ato_add_module",
                    "args": {"module_name": "MCU", "package_ref": "esp32_wroom_32e"}, "ts": "3.6s"
                }))
                await asyncio.sleep(1)
                await websocket.send_text(json.dumps({
                    "type": "tool_call_completed", "id": "tc_002", "result": {"id": "MCU"}, "ts": "4.6s"
                }))
                
                # Simulate file change (which would reload the board viewer in real life)
                await websocket.send_text(json.dumps({
                    "type": "file_changed", "path": "elec/layout/board.kicad_pcb", "ts": "4.7s"
                }))
                
                # Final completion message
                await websocket.send_text(json.dumps({
                    "type": "chat", "role": "assistant", "ts": "5.0s",
                    "text": "Task completed successfully. The schematic and board files have been updated."
                }))
                
    except Exception as e:
        print(f"WebSocket Error: {e}")
