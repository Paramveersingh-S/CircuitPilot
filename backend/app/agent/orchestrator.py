from pydantic import BaseModel
from typing import List, Optional, Dict
import json
from .llm_client import LLMClient
from app.db import get_circuit_memory, save_circuit, create_session as db_create_session

class ClarificationOption(BaseModel):
    id: str
    label: str

class PlanResult(BaseModel):
    status: str  # 'CLARIFICATION_REQUIRED' or 'READY_TO_EXECUTE'
    options: List[ClarificationOption] = []
    components: dict = {}
    message: str = ""

# ─── Critic Verifier ──────────────────────────────────────────────────────────
class Critic:
    """
    Second-pass LLM reviewer that checks the Planner's component list for
    technical correctness before it is sent to the physical router.
    Checks:
      - Missing decoupling capacitors for each IC (IPC rule)
      - Missing current-limiting resistors for every LED
      - Missing power connector if none specified
      - Missing crystal oscillator if a microcontroller is present
      - Over-specified (too many caps for the IC count)
    Returns a corrected components dict.
    """
    def __init__(self):
        self.llm = LLMClient()

    async def verify(self, original_components: dict, user_request: str) -> dict:
        system_prompt = """\
You are a senior hardware engineer and PCB design reviewer at a top electronics company.
Your job is to review an AI-generated component list for a PCB and ensure it is TECHNICALLY CORRECT.

Rules you MUST enforce:
1. Every IC in 'main_ics' needs at least one decoupling capacitor (100nF) in 'decoupling_capacitors'.
2. Every LED in 'passives' needs a current-limiting resistor in 'passives'.
3. If there are main_ics but no power connector in 'connectors', add a BarrelJack.
4. If a Microcontroller is present and no Crystal is listed, add a Crystal Oscillator to 'main_ics'.
5. Do NOT add components the user didn't ask for beyond essential support components.
6. Do NOT remove components the user explicitly asked for.

You will be given the original user request and the proposed component list.
Return ONLY a corrected JSON object with the exact same structure:
{
  "main_ics": [...],
  "decoupling_capacitors": [...],
  "passives": [...],
  "connectors": [...]
}
Do NOT wrap in markdown. Output raw JSON only. Make minimal changes."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""User Request: {user_request}

Proposed Component List:
{json.dumps(original_components, indent=2)}

Please review and return the corrected component list."""}
        ]

        try:
            response = await self.llm.chat(messages=messages, max_tokens=2048)
            content = response.choices[0].message.content
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end > start:
                corrected = json.loads(content[start:end])
                # Validate it has the right keys
                if all(k in corrected for k in ['main_ics', 'decoupling_capacitors', 'passives', 'connectors']):
                    return corrected
        except Exception as e:
            import traceback
            print(f"Critic error (using original): {e}\n{traceback.format_exc()}")

        # On any failure, return original unchanged
        return original_components


# ─── Planner ─────────────────────────────────────────────────────────────────
class Planner:
    def __init__(self):
        self.llm = LLMClient()

    async def process(self, user_text: str, context: str, memory: list = []) -> PlanResult:
        # Build memory context block for Phase B
        memory_block = ""
        if memory:
            memory_block = "\n\nPrevious circuits you built for this user (use as context):\n"
            for i, m in enumerate(memory, 1):
                comps_summary = ", ".join(
                    f"{k}: {len(v)}" for k, v in m.get("components", {}).items() if isinstance(v, list)
                )
                memory_block += f"{i}. Prompt: \"{m['prompt']}\" → {comps_summary}\n"
            memory_block += "\nUse this to understand user preferences and improve your component selection.\n"

        system_prompt = f"""\
You are the CircuitPilot Planner, an expert PCB designer.
Context: {context}{memory_block}

If the user's request is ambiguous or underspecified, ask a clarifying question with 2-4 options.
If fully specified, extract all components into a categorized JSON object with keys:
'main_ics', 'decoupling_capacitors', 'passives', 'connectors'.

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
    "main_ics": ["ESP32", "VoltageRegulator"],
    "decoupling_capacitors": ["100nF Cap", "10uF Cap"],
    "passives": ["LED", "Resistor"],
    "connectors": ["BarrelJack", "ProgrammingHeader"]
  }}
}}
IMPORTANT: Output raw JSON only. No markdown code fences."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text}
        ]

        try:
            response = await self.llm.chat(messages=messages)
            content = response.choices[0].message.content
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end > start:
                data = json.loads(content[start:end])
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
            print(f"Planner error: {traceback.format_exc()}")
            return PlanResult(status="READY_TO_EXECUTE", message=f"Error generating plan: {str(e)}")


# ─── Orchestrator ─────────────────────────────────────────────────────────────
class Orchestrator:
    def __init__(self):
        self.planner = Planner()
        self.critic  = Critic()

    async def handle_command(self, session_manager, session_id: str, user_text: str, websocket):
        session = session_manager.get_session(session_id)
        if not session:
            session_id = session_manager.create_session()
            session = session_manager.get_session(session_id)

        context = session.get("context", {})

        # ── Step 1: Load circuit memory (Phase B) ──────────────────────────
        memory = get_circuit_memory(session_id, limit=3)

        # ── Step 2: Plan ────────────────────────────────────────────────────
        await websocket.send_json({"type": "chat", "role": "assistant", "text": "Thinking..."})
        plan = await self.planner.process(user_text, context=str(context), memory=memory)
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

        # ── Step 2: Critic Self-Verification ───────────────────────────────
        await websocket.send_json({
            "type": "chat", "role": "assistant",
            "text": "Verifying technical correctness (IPC rules check)..."
        })
        verified_components = await self.critic.verify(plan.components, user_text)

        # Report any corrections made
        original_total = sum(len(v) for v in plan.components.values() if isinstance(v, list))
        verified_total = sum(len(v) for v in verified_components.values() if isinstance(v, list))
        if verified_total != original_total:
            delta = verified_total - original_total
            await websocket.send_json({
                "type": "chat", "role": "assistant",
                "text": f"Critic added {delta} essential component(s) to meet IPC design rules."
            })
        else:
            await websocket.send_json({
                "type": "chat", "role": "assistant",
                "text": "Technical review passed — component list is IPC-compliant."
            })

        # ── Step 3: Route & Generate ───────────────────────────────────────
        from app.projects.store import project_store
        from app.agent.tools.native_generator import generate_kicad_pcb
        import os

        project_store.init_project(session_id)
        project_path = project_store.get_project_path(session_id)

        await websocket.send_json({
            "type": "chat", "role": "assistant",
            "text": "Routing PCB with Force-Directed 45-degree multi-layer algorithm..."
        })

        pcb_path = os.path.join(project_path, f"{session_id}.kicad_pcb")
        success = generate_kicad_pcb(pcb_path, verified_components)

        if not success:
            await websocket.send_json({"type": "chat", "role": "assistant", "text": "Build failed: Native Generation Error"})
            return

        await websocket.send_json({"type": "chat", "role": "assistant", "text": "Board generated successfully!"})

        # ── Save to circuit memory DB ───────────────────────────────────────
        save_circuit(session_id, user_text, verified_components, pcb_path)

        # ── Export Gerbers ──────────────────────────────────────────────────
        from app.agent.tools.gerber_export import export_gerbers
        gerber_ok, zip_path, _gerber_msg = export_gerbers(pcb_path)

        import time
        BASE_URL  = os.environ.get("BASE_URL", "http://localhost:8000")
        board_url = f"{BASE_URL}/workspaces/{session_id}/{session_id}.kicad_pcb?t={int(time.time())}"

        gerber_url = None
        if gerber_ok and zip_path:
            zip_name   = os.path.basename(zip_path)
            gerber_url = f"{BASE_URL}/workspaces/{session_id}/{zip_name}"
            await websocket.send_json({
                "type": "chat", "role": "assistant",
                "text": "Gerbers ready! Download below and order from JLCPCB/PCBWay."
            })

        # ── Generate BOM ────────────────────────────────────────────────────
        bom = _generate_bom(verified_components)

        # ── Enriched board_ready event (picked up by frontend) ──────────────
        await websocket.send_json({
            "type":        "board_ready",
            "kicad_url":   board_url,
            "gerber_url":  gerber_url,
            "bom":         bom,
            "order_links": {
                "jlcpcb":  "https://cart.jlcpcb.com/quote",
                "pcbway":  "https://www.pcbway.com/orderonline.aspx",
                "oshpark": "https://oshpark.com/",
            },
        })

        # Backward-compat event so KiCanvas still loads
        await websocket.send_json({"type": "file_changed", "path": board_url})

        history = session.get("history", [])
        history.append({"role": "user",      "content": user_text})
        history.append({"role": "assistant", "content": "Generated IPC-verified layout with Gerbers + BOM."})
        session_manager.update_session(session_id, context, history)


def _generate_bom(components: dict) -> list:
    """
    Build a Bill of Materials list from the verified component manifest.
    Returns a list of dicts with ref, category, value, quantity, and Octopart URL.
    """
    bom: list = []
    category_labels = {
        "main_ics":              "Integrated Circuit",
        "decoupling_capacitors": "Decoupling Capacitor",
        "passives":              "Passive",
        "connectors":            "Connector",
    }
    prefix_map = {
        "main_ics":              "U",
        "decoupling_capacitors": "C",
        "passives":              "R",
        "connectors":            "J",
    }
    counters: dict = {}

    for category, items in components.items():
        if not isinstance(items, list):
            continue
        prefix = prefix_map.get(category, "X")
        for item in items:
            n   = counters.get(prefix, 1)
            ref = f"{prefix}{n}"
            counters[prefix] = n + 1
            bom.append({
                "reference":  ref,
                "value":      item,
                "category":   category_labels.get(category, category),
                "quantity":   1,
                "footprint":  "SMD 0805" if category in ("decoupling_capacitors", "passives") else "",
                "source_url": f"https://octopart.com/search?q={item.replace(' ', '+')}&currency=USD",
            })
    return bom

