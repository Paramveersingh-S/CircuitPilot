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
    ato_code: str = ""
    message: str = ""

class Planner:
    def __init__(self):
        self.llm = LLMClient()
        
    async def process(self, user_text: str, context: str) -> PlanResult:
        system_prompt = f"""
You are the CircuitPilot Planner, an expert PCB designer and Atopile programmer.
Context: {context}

If the user's request is ambiguous or underspecified, you MUST ask a clarifying question and provide 2-4 concrete options for them to choose from.
If the request is fully specified, you MUST output valid Atopile (.ato) code to build the circuit. 
Assume standard generics are available (e.g., `import Resistor from "generics/resistors.ato"`).

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
  "message": "Writing Atopile code...",
  "ato_code": "component Resistor:\\n    pin p1\\n    pin p2\\n\\nmodule Blinky:\\n    res1 = new Resistor\\n    res1.p1 ~ res1.p2"
}}

IMPORTANT: Do not wrap `ato_code` in markdown. It must be a raw string safely escaped for JSON.

CRITICAL Atopile Syntax Rules:
1. DO NOT use `import` statements. You must define all components inline using `component <Name>:`.
   Example:
   component LED:
       pin anode
       pin cathode
       footprint = "LED_SMD:LED_0805_2012Metric"
2. DO NOT use the `property` keyword. Just define variables directly.
   ILLEGAL: `property pin_count`
   CORRECT: `pin_count = 40`
3. DO NOT use array syntax like `pins[6]` or `icsp.pins[1]`. Define explicit pins: `pin p1`, `pin p2`.
4. You CANNOT pass arguments to `new`. 
   ILLEGAL: `new DIPSocket(pin_count=40)`
   CORRECT: `sock = new DIPSocket` then `sock.pin_count = 40`
5. Values use exact units: `330ohm`, `10uF` (No underscores).
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text}
        ]
        
        try:
            response = await self.llm.chat(messages=messages)
            content = response.choices[0].message.content
            
            # Simple JSON extraction
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
                        ato_code=data.get("ato_code", "")
                    )
        except Exception as e:
            import traceback
            err = traceback.format_exc()
            print(f"Planner error: {err}")
            return PlanResult(status="READY_TO_EXECUTE", message=f"Error generating plan: {str(e)}", subtasks=[])

class Orchestrator:
    def __init__(self):
        self.planner = Planner()
        
    async def handle_command(self, session_manager, session_id: str, user_text: str, websocket):
        session = session_manager.get_session(session_id)
        if not session:
            session_id = session_manager.create_session()
            session = session_manager.get_session(session_id)
            
        context = session.get("context", {})
        
        # 1. Process with LLM
        await websocket.send_json({"type": "chat", "role": "assistant", "text": "Thinking..."})
        plan = await self.planner.process(user_text, context=str(context))
        
        await websocket.send_json({"type": "chat", "role": "assistant", "text": plan.message})
        
        if plan.status == "CLARIFICATION_REQUIRED":
            await websocket.send_json({
                "type": "clarification_options",
                "options": [o.dict() for o in plan.options]
            })
            
            # Save history and return, waiting for user response
            history = session.get("history", [])
            history.append({"role": "user", "content": user_text})
            history.append({"role": "assistant", "content": plan.message})
            session_manager.update_session(session_id, context, history)
            return
            
        # 2. Execute
        from app.projects.store import project_store
        from app.agent.tools.ato_tools import run_ato_build
        import os

        # Ensure project exists
        project_store.init_project(session_id)
        project_path = project_store.get_project_path(session_id)
        
        # Write .ato file
        ato_path = os.path.join(project_path, f"{session_id}.ato")
        with open(ato_path, "w", encoding="utf-8") as f:
            f.write(plan.ato_code)
            
        await websocket.send_json({"type": "chat", "role": "assistant", "text": "Compiling Atopile code natively..."})

        # Build project natively via Docker!
        success, logs = run_ato_build(ato_path, project_path)
        if not success:
            await websocket.send_json({"type": "chat", "role": "assistant", "text": f"Build failed:\\n```\\n{logs}\\n```"})
            return

        await websocket.send_json({"type": "chat", "role": "assistant", "text": "Finished executing tasks."})
        
        # Serve the dynamically generated board
        import time
        board_url = f"http://localhost:8000/workspaces/{session_id}/build/{session_id}.kicad_pcb?t={int(time.time())}"
        await websocket.send_json({
            "type": "file_changed", 
            "path": board_url
        })
        
        # 3. Update session history
        history = session.get("history", [])
        history.append({"role": "user", "content": user_text})
        history.append({"role": "assistant", "content": f"Wrote Atopile code and compiled."})
        session_manager.update_session(session_id, context, history)
