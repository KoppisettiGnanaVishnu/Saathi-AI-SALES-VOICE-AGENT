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
    """Thin, dependency-light client for a local Ollama server."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        embed_model: str | None = None,
    ) -> None:
        self.base_url = (base_url or config.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or config.OLLAMA_MODEL
        self.embed_model = embed_model or config.OLLAMA_EMBED_MODEL
        self._client = httpx.Client(
            timeout=httpx.Timeout(180.0, connect=5.0),
            headers={"Content-Type": "application/json"},
        )

    def status(self) -> dict[str, Any]:
        try:
            response = self._client.get(f"{self.base_url}/api/tags", timeout=3.0)
            response.raise_for_status()
            models = [item.get("name", "") for item in response.json().get("models", [])]
            installed = any(
                name == self.model or name.startswith(f"{self.model}:")
                for name in models
            )
            return {
                "reachable": True,
                "model": self.model,
                "model_installed": installed,
                "available_models": models,
            }
        except Exception as exc:  # noqa: BLE001 - health endpoint should never crash
            return {
                "reachable": False,
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
        """Ask the local model for a JSON object, with one repair attempt."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "format": "json",
            # Keep the model resident between turns and give the prompt enough
            # room that retrieval context is never silently truncated.
            "keep_alive": "30m",
            "options": {
                "temperature": temperature,
                "num_predict": num_predict,
                "num_ctx": 4096,
                "top_p": 0.9,
            },
        }

        last_error: Exception | None = None
        working_messages = list(messages)

        for attempt in range(2):
            try:
                response = self._client.post(
                    f"{self.base_url}/api/chat", json=payload
                )
                response.raise_for_status()
                content = response.json().get("message", {}).get("content", "")
                return extract_json(content)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.warning("Ollama chat attempt %s failed: %s", attempt + 1, exc)
                if attempt == 0:
                    working_messages = list(messages) + [
                        {
                            "role": "system",
                            "content": (
                                "Your previous answer was not valid JSON. "
                                "Return ONLY one valid JSON object with no markdown."
                            ),
                        }
                    ]
                    payload["messages"] = working_messages
                    payload["options"]["temperature"] = 0.1

        raise LLMError(f"Local model failed to return usable JSON: {last_error}")

    def chat_json_deltas(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.25,
        num_predict: int = 420,
    ):
        """Yield content deltas from Ollama so the caller can speak early.

        Ollama still emits one JSON object (``format: json``); we stream its
        tokens and let the agent pull the ``reply`` string out as it forms.
        """
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

        try:
            with self._client.stream(
                "POST", f"{self.base_url}/api/chat", json=payload
            ) as response:
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
            raise LLMError(f"Streaming chat failed: {exc}") from exc

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Create embeddings with Ollama, supporting both embed API shapes."""
        if not texts:
            return []

        try:
            response = self._client.post(
                f"{self.base_url}/api/embed",
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
            response = self._client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.embed_model, "prompt": text},
                timeout=120.0,
            )
            response.raise_for_status()
            embeddings.append(response.json()["embedding"])
        return embeddings
