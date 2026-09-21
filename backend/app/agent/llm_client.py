"""
CircuitPilot LLM Client — LiteLLM powered, provider-agnostic.
Supports OpenAI, Gemini, Anthropic, Ollama, vLLM, LM Studio.
Set LLM_MODEL, OPENAI_API_KEY, OPENAI_API_BASE in .env to configure.
"""
import os
import json
from typing import List, Dict, Any, Optional
from litellm import acompletion

class LLMClient:
    def __init__(self):
        # Provider-agnostic: driven entirely by environment variables
        self.model = os.environ.get("LLM_MODEL", "openai/local-model")
        self.api_base = os.environ.get("OPENAI_API_BASE")
        self.api_key = os.environ.get("OPENAI_API_KEY", "not-set")
        self.temperature = float(os.environ.get("LLM_TEMPERATURE", "0.0"))

    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 4096
    ) -> Any:
        """
        Calls the configured LLM via LiteLLM.
        Provider is fully determined by the LLM_MODEL env var:
          - "openai/gpt-4o"          → OpenAI
          - "gemini/gemini-2.0-flash" → Google Gemini
          - "anthropic/claude-3-5-sonnet" → Anthropic
          - "ollama/llama3"           → Local Ollama
          - "openai/local-model"      → LM Studio / vLLM
        """
        try:
            kwargs = dict(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=max_tokens,
            )
            if self.api_base:
                kwargs["api_base"] = self.api_base
            if self.api_key:
                kwargs["api_key"] = self.api_key
            if tools:
                kwargs["tools"] = tools

            response = await acompletion(**kwargs)
            return response

        except Exception as e:
            import traceback
            print(f"LLM Error [{self.model}]: {e}\n{traceback.format_exc()}")
            raise
