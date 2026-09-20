import json
import os
from typing import List, Dict, Any, Optional
try:
    from litellm import acompletion
except ImportError:
    acompletion = None

class LLMClient:
    def __init__(self, model_name: str = "openai/local-model"):
        # Default to an OpenAI compatible endpoint (e.g. LM Studio, Ollama, vLLM)
        self.model_name = os.environ.get("LLM_MODEL", model_name)
    
    async def chat(self, messages: List[Dict[str, str]], tools: Optional[List[Dict]] = None) -> Any:
        api_base = os.environ.get("OPENAI_API_BASE")
        api_key = os.environ.get("OPENAI_API_KEY")

        try:
            response = await acompletion(
                model=self.model_name,
                messages=messages,
                api_base=api_base,
                api_key=api_key,
                temperature=0.0,
                max_tokens=8192
            )
            return response
        except Exception as e:
            print(f"LLM API Error: {e}")
            raise e
