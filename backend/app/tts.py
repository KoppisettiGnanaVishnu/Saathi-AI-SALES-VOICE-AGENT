"""Client for the local neural voice service.

The sales API owns the public ``/api/tts`` route; this module normalises the
reply for speech and forwards it to the Kokoro service. If the service is not
running the call returns ``None`` and the browser voice takes over, so the demo
never breaks because of a missing optional dependency.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from . import config
from .tts_text import normalise_for_speech

logger = logging.getLogger(__name__)


class VoiceClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or config.TTS_URL).rstrip("/")
        self.enabled = config.TTS_ENABLED
        self._client = httpx.Client(timeout=httpx.Timeout(60.0, connect=1.0))
        self._status_cache: tuple[float, dict[str, Any]] | None = None

    def status(self, ttl: float = 5.0) -> dict[str, Any]:
        if not self.enabled:
            return {"engine": "browser", "reachable": False, "reason": "disabled"}
        now = time.monotonic()
        if self._status_cache and now - self._status_cache[0] < ttl:
            return self._status_cache[1]
        try:
            response = self._client.get(f"{self.base_url}/health", timeout=1.5)
            response.raise_for_status()
            data = response.json()
            data["reachable"] = True
        except Exception as exc:  # noqa: BLE001 - health must never raise
            data = {
                "engine": "browser",
                "reachable": False,
                "error": str(exc)[:140],
            }
        self._status_cache = (now, data)
        return data

    def synthesize(self, text: str, language: str) -> tuple[bytes, str] | None:
        """Return ``(wav_bytes, engine)`` or ``None`` when neural TTS is down."""
        if not self.enabled:
            return None
        spoken = normalise_for_speech(text, language)
        if not spoken:
            return None
        try:
            response = self._client.post(
                f"{self.base_url}/tts",
                json={"text": spoken[:600], "language": language},
            )
            response.raise_for_status()
            return response.content, "kokoro"
        except Exception as exc:  # noqa: BLE001 - fall back to browser voice
            logger.info("Neural voice unavailable, falling back: %s", exc)
            self._status_cache = None
            return None
