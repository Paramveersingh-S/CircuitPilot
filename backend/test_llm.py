import asyncio
import os
import traceback
from dotenv import load_dotenv
load_dotenv()
from app.agent.llm_client import LLMClient

async def main():
    try:
        client = LLMClient()
        print('Model:', client.model_name)
        print('API Base:', os.environ.get("OPENAI_API_BASE"))
        resp = await client.chat([{'role': 'user', 'content': 'hello'}])
        print(resp.choices[0].message.content)
    except Exception as e:
        print("ERROR CAUGHT:")
        traceback.print_exc()

asyncio.run(main())
