from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

from . import config

logger = logging.getLogger(__name__)


class LLMError(RuntimeError):
    """Raised when the local model cannot produce a usable response."""


def extract_json(raw: str) -> dict[str, Any]:
    """Parse JSON from a model response, tolerating code fences and prose."""
    text = (raw or "").strip()
    if not text:
        raise ValueError("Empty model response")

    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end <= start:
            raise ValueError("No JSON object found in model response")
        candidate = text[start : end + 1]
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            cleaned = re.sub(r",\s*([}\]])", r"\1", candidate)
            parsed = json.loads(cleaned)

    if not isinstance(parsed, dict):
        raise ValueError("Model response JSON is not an object")
    return parsed


class OllamaClient:
    """Chat via Ollama or any OpenAI-compatible API, embeddings via Ollama."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        embed_model: str | None = None,
    ) -> None:
        self.provider = (config.LLM_PROVIDER or "ollama").lower()
        self.api_key = config.LLM_API_KEY
        self.chat_base_url = (
            config.LLM_BASE_URL if self.provider == "openai_compatible" else (base_url or config.OLLAMA_BASE_URL)
        ).rstrip("/")
        self.model = config.LLM_MODEL if self.provider == "openai_compatible" else (model or config.OLLAMA_MODEL)
        self.embed_base_url = (base_url or config.OLLAMA_BASE_URL).rstrip("/")
        self.embed_model = embed_model or config.OLLAMA_EMBED_MODEL
        headers = {"Content-Type": "application/json"}
        if self.provider == "openai_compatible" and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        self._client = httpx.Client(timeout=httpx.Timeout(120.0, connect=10.0), headers=headers)
        self._embed_client = httpx.Client(
            timeout=httpx.Timeout(120.0, connect=5.0),
            headers={"Content-Type": "application/json"},
        )

    def status(self) -> dict[str, Any]:
        try:
            if self.provider == "openai_compatible":
                r = self._client.get(f"{self.chat_base_url}/models", timeout=8.0)
                r.raise_for_status()
                data = r.json()
                models = [m.get("id", "") for m in data.get("data", []) if isinstance(m, dict)]
                return {
                    "reachable": True,
                    "provider": self.provider,
                    "model": self.model,
                    "model_installed": True,
                    "available_models": models[:20],
                }
            response = self._embed_client.get(f"{self.embed_base_url}/api/tags", timeout=3.0)
            response.raise_for_status()
            models = [item.get("name", "") for item in response.json().get("models", [])]
            installed = any(name == self.model or name.startswith(f"{self.model}:") for name in models)
            return {
                "reachable": True,
                "provider": "ollama",
                "model": self.model,
                "model_installed": installed,
                "available_models": models,
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "reachable": False,
                "provider": self.provider,
                "model": self.model,
                "model_installed": False,
                "error": str(exc),
            }

    def chat_json(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.25,
        num_predict: int = 700,
    ) -> dict[str, Any]:
        """Ask the model for a JSON object, with one repair attempt."""
        last_error: Exception | None = None
        working_messages = list(messages)

        for attempt in range(2):
            try:
                if self.provider == "openai_compatible":
                    payload = {
                        "model": self.model,
                        "messages": working_messages,
                        "temperature": temperature,
                        "max_tokens": num_predict,
                    }
                    # response_format json_object can cause 400 on some models; request JSON in prompt instead
                    response = self._client.post(f"{self.chat_base_url}/chat/completions", json=payload)
                    if response.status_code in (400, 429):
                        raise httpx.HTTPStatusError(f"retryable {response.status_code}", request=response.request, response=response)
                    response.raise_for_status()
                    content = response.json()["choices"][0]["message"]["content"]
                    return extract_json(content)

                payload = {
                    "model": self.model,
                    "messages": working_messages,
                    "stream": False,
                    "format": "json",
                    "keep_alive": "30m",
                    "options": {
                        "temperature": temperature,
                        "num_predict": num_predict,
                        "num_ctx": 4096,
                        "top_p": 0.9,
                    },
                }
                response = self._embed_client.post(f"{self.embed_base_url}/api/chat", json=payload)
                response.raise_for_status()
                content = response.json().get("message", {}).get("content", "")
                return extract_json(content)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.warning("Chat attempt %s failed (%s/%s): %s", attempt + 1, self.provider, self.model, exc)
                if attempt == 0:
                    working_messages = list(messages) + [
                        {
                            "role": "system",
                            "content": "Your previous answer was not valid JSON. Return ONLY one valid JSON object with no markdown.",
                        }
                    ]

        if self.provider == "openai_compatible":
            # Fallback to local Ollama if available
            try:
                payload = {
                    "model": config.OLLAMA_MODEL,
                    "messages": working_messages,
                    "stream": False,
                    "format": "json",
                    "keep_alive": "30m",
                    "options": {"temperature": temperature, "num_predict": num_predict, "num_ctx": 4096, "top_p": 0.9},
                }
                response = self._embed_client.post(f"{self.embed_base_url}/api/chat", json=payload, timeout=120.0)
                response.raise_for_status()
                content = response.json().get("message", {}).get("content", "")
                logger.warning("Fell back to local Ollama after OpenAI-compatible failure")
                return extract_json(content)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
        raise LLMError(f"Model failed to return usable JSON: {last_error}")

    def chat_json_deltas(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.25,
        num_predict: int = 420,
    ):
        """Yield content deltas so the caller can speak early."""
        try:
            if self.provider == "openai_compatible":
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": num_predict,
                    "stream": True,
                }
                with self._client.stream("POST", f"{self.chat_base_url}/chat/completions", json=payload) as response:
                    if response.status_code in (400, 429):
                        raise httpx.HTTPStatusError(f"retryable {response.status_code}", request=response.request, response=response)
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if not line or not line.startswith("data:"):
                            continue
                        data = line[5:].strip()
                        if data == "[DONE]":
                            return
                        try:
                            chunk = json.loads(data)
                        except json.JSONDecodeError:
                            continue
                        delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content") or ""
                        if delta:
                            yield delta
                return

            payload = {
                "model": self.model,
                "messages": messages,
                "stream": True,
                "format": "json",
                "keep_alive": "30m",
                "options": {
                    "temperature": temperature,
                    "num_predict": num_predict,
                    "num_ctx": 4096,
                    "top_p": 0.9,
                },
            }
            with self._embed_client.stream("POST", f"{self.embed_base_url}/api/chat", json=payload) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if chunk.get("error"):
                        raise LLMError(str(chunk["error"]))
                    delta = chunk.get("message", {}).get("content") or ""
                    if delta:
                        yield delta
                    if chunk.get("done"):
                        return
        except httpx.HTTPError as exc:
            if self.provider == "openai_compatible":
                logger.warning("OpenAI-compatible stream failed, falling back to Ollama: %s", exc)
                try:
                    payload = {
                        "model": config.OLLAMA_MODEL,
                        "messages": messages,
                        "stream": True,
                        "format": "json",
                        "keep_alive": "30m",
                        "options": {"temperature": temperature, "num_predict": num_predict, "num_ctx": 4096, "top_p": 0.9},
                    }
                    with self._embed_client.stream("POST", f"{self.embed_base_url}/api/chat", json=payload) as response:
                        response.raise_for_status()
                        for line in response.iter_lines():
                            if not line:
                                continue
                            try:
                                chunk = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                            if chunk.get("error"):
                                raise LLMError(str(chunk["error"]))
                            delta = chunk.get("message", {}).get("content") or ""
                            if delta:
                                yield delta
                            if chunk.get("done"):
                                return
                    return
                except Exception as ollama_exc:  # noqa: BLE001
                    raise LLMError(f"Streaming chat failed: {exc}; ollama fallback: {ollama_exc}") from exc
            raise LLMError(f"Streaming chat failed: {exc}") from exc

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Create embeddings with Ollama, supporting both embed API shapes."""
        if not texts:
            return []

        try:
            response = self._embed_client.post(
                f"{self.embed_base_url}/api/embed",
                json={"model": self.embed_model, "input": texts},
                timeout=120.0,
            )
            if response.status_code == 200:
                embeddings = response.json().get("embeddings")
                if embeddings and len(embeddings) == len(texts):
                    return embeddings
        except Exception as exc:  # noqa: BLE001
            logger.info("Batch embed endpoint unavailable: %s", exc)

        embeddings: list[list[float]] = []
        for text in texts:
            response = self._embed_client.post(
                f"{self.embed_base_url}/api/embeddings",
                json={"model": self.embed_model, "prompt": text},
                timeout=120.0,
            )
            response.raise_for_status()
            embeddings.append(response.json()["embedding"])
        return embeddings
