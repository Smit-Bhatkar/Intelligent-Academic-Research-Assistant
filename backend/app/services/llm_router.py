"""
LLM Router service — Phase 3 multi-provider failover chain.
Implements: Gemini -> Groq -> Local Ollama -> Offline Extractive Fallback.
"""

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    text: str
    model: str
    provider: str
    is_fallback: bool


class LLMRouter:
    """
    Intelligent LLM gateway that routes prompts to the highest priority
    available model provider, cascading automatically on failure or rate-limits:
    1. Google Gemini (Gemini 2.5 Flash / 1.5 Flash)
    2. Groq Cloud (Llama 3.3 70B / 3.1 8B)
    3. Local Ollama (e.g. llama3, mistral)
    4. Extractive Semantic Fallback (offline)
    """

    def __init__(self):
        self.gemini_model = "gemini-2.5-flash"
        self.groq_model = "llama-3.3-70b-versatile"
        self.ollama_model = "llama3"
        self.ollama_base_url = "http://localhost:11434"

    async def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        api_key: str | None = None,
    ) -> LLMResponse:
        """
        Attempts to generate content through the failover chain.
        Returns LLMResponse with generated text, model, provider, and fallback status.
        """
        # 1. Try Gemini
        gemini_key = api_key or settings.GEMINI_API_KEY
        if gemini_key:
            try:
                resp = await self._call_gemini(prompt, system_instruction, gemini_key)
                if resp and resp.strip():
                    return LLMResponse(
                        text=resp,
                        model=self.gemini_model,
                        provider="gemini",
                        is_fallback=False,
                    )
            except Exception as e:
                logger.warning(f"Gemini generation failed: {e}. Trying Groq fallback...")

        # 2. Try Groq
        groq_key = settings.GROQ_API_KEY
        if groq_key:
            try:
                resp = await self._call_groq(prompt, system_instruction, groq_key)
                if resp and resp.strip():
                    return LLMResponse(
                        text=resp,
                        model=self.groq_model,
                        provider="groq",
                        is_fallback=False,
                    )
            except Exception as e:
                logger.warning(f"Groq generation failed: {e}. Trying Ollama fallback...")

        # 3. Try Local Ollama
        try:
            resp = await self._call_ollama(prompt, system_instruction)
            if resp and resp.strip():
                return LLMResponse(
                    text=resp,
                    model=self.ollama_model,
                    provider="ollama",
                    is_fallback=False,
                )
        except Exception as e:
            logger.debug(f"Ollama local service unavailable: {e}")

        # 4. If all generative providers failed or are unconfigured, return None to trigger extractive fallback
        return LLMResponse(
            text="",
            model="none",
            provider="extractive-semantic-ranker",
            is_fallback=True,
        )

    async def _call_gemini(
        self, prompt: str, system_instruction: str, api_key: str
    ) -> str:
        """Calls Google Gemini API via official google-genai SDK."""
        from google import genai

        client = genai.Client(api_key=api_key)
        full_content = prompt
        if system_instruction:
            full_content = f"System Instruction:\n{system_instruction}\n\n{prompt}"

        # Using generate_content
        resp = client.models.generate_content(
            model=self.gemini_model,
            contents=full_content,
        )
        return resp.text or ""

    async def _call_groq(
        self, prompt: str, system_instruction: str, api_key: str
    ) -> str:
        """Calls Groq Cloud API using OpenAI-compatible endpoint."""
        messages: list[dict[str, str]] = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.groq_model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 2048,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def _call_ollama(self, prompt: str, system_instruction: str) -> str:
        """Calls local Ollama server if running."""
        full_prompt = prompt
        if system_instruction:
            full_prompt = f"{system_instruction}\n\n{prompt}"

        payload = {
            "model": self.ollama_model,
            "prompt": full_prompt,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "")


# Global singleton router
llm_router = LLMRouter()
