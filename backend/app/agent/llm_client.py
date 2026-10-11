"""
CircuitPilot LLM Client — LiteLLM powered, provider-agnostic.
Supports OpenAI, Gemini, Anthropic, Ollama, vLLM, Groq.
Supports Multimodal input (text + circuit images).
"""
import os
import json
from typing import List, Dict, Any, Optional
from litellm import acompletion

class LLMClient:
    def __init__(self):
        # Provider-agnostic: driven entirely by environment variables
        self.model = os.environ.get("LLM_MODEL", "gemini/gemini-3.8-flash")
        self.api_base = os.environ.get("OPENAI_API_BASE")
        self.api_key = os.environ.get("OPENAI_API_KEY", "not-set")
        self.gemini_key = os.environ.get("GEMINI_API_KEY")
        self.temperature = float(os.environ.get("LLM_TEMPERATURE", "0.0"))

    def _prepare_messages(
        self,
        messages: List[Dict[str, Any]],
        images: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Formats messages for LiteLLM. If images are provided, injects them
        into the last user message as multimodal content parts.
        """
        if not images:
            return messages

        formatted = []
        last_user_idx = -1
        for i, m in enumerate(messages):
            if m.get("role") == "user":
                last_user_idx = i

        for i, m in enumerate(messages):
            if i == last_user_idx:
                content = m.get("content", "")
                parts: List[Dict[str, Any]] = []
                if isinstance(content, str):
                    parts.append({"type": "text", "text": content})
                elif isinstance(content, list):
                    parts.extend(content)

                for img in images:
                    parts.append({
                        "type": "image_url",
                        "image_url": {"url": img}
                    })

                formatted.append({**m, "content": parts})
            else:
                formatted.append(m)

        return formatted

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 4096,
        images: Optional[List[str]] = None
    ) -> Any:
        """
        Calls the configured LLM via LiteLLM with multimodal image support.
        """
        final_messages = self._prepare_messages(messages, images)
        target_model = self.model
        api_key = self.api_key
        api_base = self.api_base

        # If model is gemini, use gemini_key and do NOT pass openai/groq api_base
        if "gemini" in target_model.lower():
            if self.gemini_key:
                api_key = self.gemini_key
            api_base = None
        elif images and self.gemini_key:
            target_model = "gemini/gemini-3.8-flash"
            api_key = self.gemini_key
            api_base = None

        kwargs: Dict[str, Any] = dict(
            model=target_model,
            messages=final_messages,
            max_tokens=max_tokens,
            timeout=45,
            num_retries=1,
        )
        if "gemini-3" not in target_model.lower():
            kwargs["temperature"] = self.temperature
        if api_base:
            kwargs["api_base"] = api_base
        if api_key and api_key != "not-set":
            kwargs["api_key"] = api_key
        if tools:
            kwargs["tools"] = tools

        try:
            response = await acompletion(**kwargs)
            return response
        except Exception as primary_err:
            import traceback
            print(f"[LLMClient] Primary call failed with {target_model}: {primary_err}")

            # Fallback strategy: if primary was Gemini and failed, try Groq; or vice versa
            if "gemini" in target_model.lower() and self.api_key and self.api_key != "not-set" and not images:
                print("[LLMClient] Attempting fallback to configured OpenAI/Groq endpoint...")
                kwargs["model"] = os.environ.get("FALLBACK_MODEL", "openai/openai/gpt-oss-120b")
                kwargs["api_key"] = self.api_key
                kwargs["api_base"] = self.api_base
                return await acompletion(**kwargs)
            elif target_model != "gemini/gemini-3.8-flash" and self.gemini_key:
                print("[LLMClient] Attempting fallback to Gemini 3.8 Flash...")
                kwargs["model"] = "gemini/gemini-3.8-flash"
                kwargs["api_key"] = self.gemini_key
                kwargs.pop("api_base", None)
                return await acompletion(**kwargs)

            print(f"[LLMClient] Unrecoverable error: {traceback.format_exc()}")
            raise
