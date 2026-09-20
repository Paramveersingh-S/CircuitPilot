import asyncio
import os
import json
import traceback
from dotenv import load_dotenv
load_dotenv()
from app.agent.llm_client import LLMClient

async def main():
    try:
        client = LLMClient()
        system_prompt = """
You are the CircuitPilot Planner, an expert PCB designer.
Context: {}

If the user's request is ambiguous or underspecified (e.g. they ask for a "buck converter" but don't specify the input/output voltages or current), you MUST ask a clarifying question and provide 2-4 concrete options for them to choose from.
If the request is fully specified (or they just selected an option), you MUST output a plan to execute the design using the tools: 'ato_search', 'ato_add_module', 'kicad_place_component'.

Respond strictly in JSON format matching one of these two structures:

Structure 1 (Clarification):
{
  "status": "CLARIFICATION_REQUIRED",
  "message": "What input and output voltage do you need?",
  "options": [
    {"id": "5v_to_3v3", "label": "5V to 3.3V"},
    {"id": "12v_to_5v", "label": "12V to 5V"}
  ]
}

Structure 2 (Execution):
{
  "status": "READY_TO_EXECUTE",
  "message": "Designing the circuit...",
  "subtasks": [
    {"agent": "schematic", "action": "ato_search", "args": {"query": "buck converter"}, "is_destructive": false},
    {"agent": "schematic", "action": "ato_add_module", "args": {"module": "buck", "instance_name": "psu"}, "is_destructive": true}
  ]
}
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Create a 5V buck converter"}
        ]
        
        print("Sending request to:", client.model_name)
        response = await client.chat(messages=messages)
        content = response.choices[0].message.content
        print("Raw Content:", content)
        
        start = content.find('{')
        end = content.rfind('}') + 1
        if start != -1 and end != 0:
            json_str = content[start:end]
            data = json.loads(json_str)
            print("Parsed JSON:", data)
        else:
            print("No JSON found")
            
    except Exception as e:
        print("ERROR CAUGHT:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
