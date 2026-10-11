import asyncio
import os
import ast
from dotenv import load_dotenv
load_dotenv()

from app.agent.orchestrator import Orchestrator
from app.agent.session import SessionManager

class MockWebSocket:
    def __init__(self):
        self.sent_messages = []

    async def send_json(self, data):
        self.sent_messages.append(data)
        m_type = data.get("type")
        if m_type == "chat":
            print(f"[WS Chat] {data.get('text')}")
        elif m_type == "board_ready":
            print(f"[WS BoardReady] kicad_url={data.get('kicad_url')}")
            print(f"[WS BoardReady] python_url={data.get('python_url')}")
            print(f"[WS BoardReady] python_code_len={len(data.get('python_code', ''))}")
            print(f"[WS BoardReady] BOM count={len(data.get('bom', []))}")
        else:
            print(f"[WS {m_type}]")

async def test_generation():
    session_mgr = SessionManager()
    session_id = session_mgr.create_session()
    ws = MockWebSocket()
    orchestrator = Orchestrator()

    # Test circuit prompt
    prompt = "ESP32 weather station with BME280 sensor and power LED"
    print(f"\n--- Testing Orchestrator with prompt: '{prompt}' ---")

    await orchestrator.handle_command(
        session_mgr,
        session_id,
        prompt,
        ws,
        images=None
    )

    # Check files in workspace
    from app.projects.store import project_store
    proj_path = project_store.get_project_path(session_id)
    py_file = os.path.join(proj_path, "circuit_generator.py")
    pcb_file = os.path.join(proj_path, f"{session_id}.kicad_pcb")

    print(f"\nChecking generated files:")
    print(f"Python script exists: {os.path.exists(py_file)} ({py_file})")
    print(f"KiCad PCB exists: {os.path.exists(pcb_file)} ({pcb_file})")

    assert os.path.exists(py_file), "circuit_generator.py was not created!"
    assert os.path.exists(pcb_file), "kicad_pcb file was not created!"

    with open(py_file, "r", encoding="utf-8") as f:
        py_code = f.read()

    # Validate Python syntax
    ast.parse(py_code)
    print("Python script syntax: VALID")

    with open(pcb_file, "r", encoding="utf-8") as f:
        pcb_content = f.read()

    assert "(kicad_pcb" in pcb_content, "Invalid PCB file header"
    assert "(segment" in pcb_content, "Missing copper trace segments"
    assert "(zone" in pcb_content, "Missing ground copper zone"
    print("KiCad PCB contents: VALID with copper segments and ground zone!")

    print("\n--- ALL TESTS PASSED SUCCESSFULLY! ---")

if __name__ == "__main__":
    asyncio.run(test_generation())
