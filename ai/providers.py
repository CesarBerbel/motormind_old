import json
import time
from dataclasses import dataclass
from typing import Any

from django.conf import settings


@dataclass(frozen=True)
class AIProviderResult:
    output_text: str
    model_name: str
    tokens_input: int = 0
    tokens_output: int = 0
    latency_ms: int = 0
    raw_response: dict | None = None


class AIProviderError(Exception):
    pass


class BaseAIProvider:
    def generate(self, *, system_prompt, user_prompt):
        raise NotImplementedError


class LocalEchoAIProvider(BaseAIProvider):
    """
    Provedor seguro para desenvolvimento quando não há chave externa configurada.
    Ele não tenta simular diagnóstico real; apenas devolve uma resposta marcada.
    """

    def generate(self, *, system_prompt, user_prompt):
        started = time.monotonic()
        output = (
            "[MODO LOCAL - IA NÃO ENVIADA A PROVEDOR EXTERNO]\n\n"
            "Revise o texto abaixo antes de usar com cliente ou em uma OS.\n\n"
            f"Entrada organizada:\n{user_prompt.strip()}"
        )
        return AIProviderResult(
            output_text=output,
            model_name="local-echo",
            latency_ms=int((time.monotonic() - started) * 1000),
            raw_response={"provider": "local_echo"},
        )


class GeminiAIProvider(BaseAIProvider):
    """
    Provider Gemini usando o SDK atual do Google: google-genai.

    Importante:
    - O pacote legado google-generativeai foi substituído por google-genai.
    - A API atual usa `from google import genai` e `client.models.generate_content`.
    """

    def __init__(self, *, api_key=None, model=None):
        self.api_key = api_key or getattr(settings, "GEMINI_API_KEY", "")
        self.model = model or getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")

    def generate(self, *, system_prompt, user_prompt):
        if not self.api_key:
            raise AIProviderError("GEMINI_API_KEY não configurada no arquivo .env.")

        started = time.monotonic()

        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise AIProviderError(
                "Pacote google-genai não instalado. Rode: pip install -U google-genai"
            ) from exc

        try:
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=getattr(settings, "AI_TEMPERATURE", 0.2),
                ),
            )
        except Exception as exc:
            raise AIProviderError(f"Erro ao chamar Gemini: {exc}") from exc

        output_text = (getattr(response, "text", "") or "").strip()
        if not output_text:
            raise AIProviderError("O Gemini retornou uma resposta vazia.")

        usage = getattr(response, "usage_metadata", None)
        raw_response = self._safe_response_to_dict(response)

        return AIProviderResult(
            output_text=output_text,
            model_name=self.model,
            tokens_input=(
                self._safe_int(getattr(usage, "prompt_token_count", 0)) if usage else 0
            ),
            tokens_output=(
                self._safe_int(getattr(usage, "candidates_token_count", 0))
                if usage
                else 0
            ),
            latency_ms=int((time.monotonic() - started) * 1000),
            raw_response=raw_response,
        )

    def _safe_response_to_dict(self, response: Any) -> dict:
        for method_name in ("model_dump", "to_dict"):
            method = getattr(response, method_name, None)
            if callable(method):
                try:
                    data = method()
                    if isinstance(data, dict):
                        return data
                except Exception:
                    pass

        return {
            "provider": "gemini",
            "model": self.model,
            "text": getattr(response, "text", ""),
        }

    def _safe_int(self, value: Any) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0


# Mantido apenas para compatibilidade com bancos/logs antigos ou troca futura.
class OpenAIChatProvider(BaseAIProvider):
    def __init__(self, *, api_key=None, model=None):
        self.api_key = api_key or getattr(settings, "OPENAI_API_KEY", "")
        self.model = model or getattr(settings, "OPENAI_MODEL", "gpt-4.1-mini")

    def generate(self, *, system_prompt, user_prompt):
        if not self.api_key:
            raise AIProviderError("OPENAI_API_KEY não configurada.")

        started = time.monotonic()
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=getattr(settings, "AI_TEMPERATURE", 0.2),
            )
        except Exception as exc:
            raise AIProviderError(str(exc)) from exc

        choice = response.choices[0]
        usage = getattr(response, "usage", None)
        raw_response = json.loads(response.model_dump_json())
        return AIProviderResult(
            output_text=(choice.message.content or "").strip(),
            model_name=self.model,
            tokens_input=getattr(usage, "prompt_tokens", 0) if usage else 0,
            tokens_output=getattr(usage, "completion_tokens", 0) if usage else 0,
            latency_ms=int((time.monotonic() - started) * 1000),
            raw_response=raw_response,
        )


def get_ai_provider():
    provider_name = getattr(settings, "AI_PROVIDER", "local").lower().strip()
    if provider_name == "gemini":
        return GeminiAIProvider()
    if provider_name == "openai":
        return OpenAIChatProvider()
    return LocalEchoAIProvider()
