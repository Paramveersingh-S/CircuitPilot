from pydantic import BaseModel
from typing import List, Optional
import json
from .llm_client import LLMClient

class Subtask(BaseModel):
    agent: str
    action: str
    args: dict
    is_destructive: bool = False

class ClarificationOption(BaseModel):
    id: str
    label: str

class PlanResult(BaseModel):
    status: str # 'CLARIFICATION_REQUIRED' or 'READY_TO_EXECUTE'
    options: List[ClarificationOption] = []
    components: dict = {}
    message: str = ""

class Planner:
    def __init__(self):
        self.llm = LLMClient()
        
    async def process(self, user_text: str, context: str) -> PlanResult:
        system_prompt = f"""
You are the CircuitPilot Planner, an expert PCB designer.
Context: {context}

If the user's request is ambiguous or underspecified, you MUST ask a clarifying question and provide 2-4 concrete options for them to choose from.
If the request is fully specified, you MUST extract all the hardware components they want to place on the circuit board into a categorized JSON object. You must classify them into: 'main_ics', 'decoupling_capacitors', 'passives', and 'connectors'. This is critical for PCB design rules.

Respond strictly in JSON format matching one of these two structures:

Structure 1 (Clarification):
{{
  "status": "CLARIFICATION_REQUIRED",
  "message": "What input and output voltage do you need?",
  "options": [
    {{"id": "5v_to_3v3", "label": "5V to 3.3V"}},
    {{"id": "12v_to_5v", "label": "12V to 5V"}}
  ]
}}

Structure 2 (Execution):
{{
  "status": "READY_TO_EXECUTE",
  "message": "Generating hardware layout...",
  "components": {{
    "main_ics": ["Microcontroller", "VoltageRegulator"],
    "decoupling_capacitors": ["100nF Cap", "10uF Cap"],
    "passives": ["LED", "Resistor"],
    "connectors": ["BarrelJack", "Header"]
  }}
}}
IMPORTANT: Do not wrap the JSON in markdown blocks. Output raw JSON.
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text}
        ]
        
        try:
            response = await self.llm.chat(messages=messages)
            content = response.choices[0].message.content
            
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = content[start:end]
                data = json.loads(json_str)
                
                if data.get("status") == "CLARIFICATION_REQUIRED":
                    return PlanResult(
                        status="CLARIFICATION_REQUIRED",
                        message=data.get("message", "Please clarify:"),
                        options=[ClarificationOption(**o) for o in data.get("options", [])]
                    )
                else:
                    return PlanResult(
                        status="READY_TO_EXECUTE",
                        message=data.get("message", "Executing..."),
                        components=data.get("components", {})
                    )
        except Exception as e:
            import traceback
            err = traceback.format_exc()
            print(f"Planner error: {err}")
            return PlanResult(status="READY_TO_EXECUTE", message=f"Error generating plan: {str(e)}")

class Orchestrator:
    def __init__(self):
        self.planner = Planner()
        
    async def handle_command(self, session_manager, session_id: str, user_text: str, websocket):
        session = session_manager.get_session(session_id)
        if not session:
            session_id = session_manager.create_session()
            session = session_manager.get_session(session_id)
            
        context = session.get("context", {})
        
        await websocket.send_json({"type": "chat", "role": "assistant", "text": "Thinking..."})
        plan = await self.planner.process(user_text, context=str(context))
        
        await websocket.send_json({"type": "chat", "role": "assistant", "text": plan.message})
        
        if plan.status == "CLARIFICATION_REQUIRED":
            await websocket.send_json({
                "type": "clarification_options",
                "options": [o.dict() for o in plan.options]
            })
            
            history = session.get("history", [])
            history.append({"role": "user", "content": user_text})
            history.append({"role": "assistant", "content": plan.message})
            session_manager.update_session(session_id, context, history)
            return
            
        from app.projects.store import project_store
        from app.agent.tools.native_generator import generate_kicad_pcb
        import os

        project_store.init_project(session_id)
        project_path = project_store.get_project_path(session_id)
        
        await websocket.send_json({"type": "chat", "role": "assistant", "text": "Routing PCB natively with 45-degree multi-layer algorithm..."})

        pcb_path = os.path.join(project_path, f"{session_id}.kicad_pcb")
        success = generate_kicad_pcb(pcb_path, plan.components)
        
        if not success:
            await websocket.send_json({"type": "chat", "role": "assistant", "text": f"Build failed: Native Generation Error"})
            return

        await websocket.send_json({"type": "chat", "role": "assistant", "text": "Finished executing tasks."})
        
        import time
        board_url = f"http://localhost:8000/workspaces/{session_id}/{session_id}.kicad_pcb?t={int(time.time())}"
        await websocket.send_json({
            "type": "file_changed", 
            "path": board_url
        })
        
        history = session.get("history", [])
        history.append({"role": "user", "content": user_text})
        history.append({"role": "assistant", "content": f"Generated native layout."})
        session_manager.update_session(session_id, context, history)
