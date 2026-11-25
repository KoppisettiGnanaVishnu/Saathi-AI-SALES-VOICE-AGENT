"""Saathi neural voice service (Kokoro-82M, Apache-2.0).

A tiny local HTTP service that turns text into natural-sounding speech. It is
deliberately separate from the sales backend:

* the 82M-parameter model and PyTorch live in their own Python 3.12 environment
* synthesis is CPU-bound, so it can be scaled or moved to a GPU node on its own
* the sales API keeps working (with a browser-voice fallback) if this is down

Run it with::

    cd backend
    .tts-venv/bin/uvicorn voice_service.app:app --port 8100

Endpoints
---------
GET  /health  -> engine, model, sample rate, available voices, loaded pipelines
POST /tts     -> {"text": "...", "language": "en-IN"} -> audio/wav
"""

from __future__ import annotations

import io
import logging
import os
import re
import threading
from collections import OrderedDict
from contextlib import asynccontextmanager
from typing import Any

import numpy as np
import soundfile as sf
import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("saathi.voice")

SAMPLE_RATE = 24_000
MODEL_ID = os.getenv("KOKORO_MODEL", "hexgrad/Kokoro-82M")
DEFAULT_SPEED = float(os.getenv("TTS_SPEED", "1.03"))
MAX_CHARS = 600
CACHE_SIZE = 256

# language -> (kokoro lang_code, voice). af_heart is Kokoro's warmest English
# voice; hf_alpha is the Hindi female voice.
VOICES: dict[str, tuple[str, str]] = {
    "en-IN": ("a", os.getenv("TTS_VOICE_EN", "af_heart")),
    "en-US": ("a", os.getenv("TTS_VOICE_EN", "af_heart")),
    "en-GB": ("b", os.getenv("TTS_VOICE_EN_GB", "bf_emma")),
    "hi-IN": ("h", os.getenv("TTS_VOICE_HI", "hf_alpha")),
}


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_CHARS)
    language: str = Field(default="en-IN", max_length=20)
    speed: float | None = Field(default=None, ge=0.7, le=1.4)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Load the English pipeline in the background so the first reply is fast."""
    def _warm() -> None:
        try:
            _pipeline("a")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Warmup failed: %s", exc)

    threading.Thread(target=_warm, name="kokoro-warmup", daemon=True).start()
    yield


app = FastAPI(title="Saathi neural voice", version="1.0.0", lifespan=lifespan)

_lock = threading.RLock()
_pipelines: dict[str, Any] = {}
_cache: "OrderedDict[tuple[str, str, float], bytes]" = OrderedDict()


def _resolve(language: str) -> tuple[str, str]:
    key = (language or "en-IN").lower()
    if key in VOICES:
        return VOICES[key]
    root = key.split("-")[0]
    for candidate, value in VOICES.items():
        if candidate.startswith(root):
            return value
    return VOICES["en-IN"]


def _pipeline(lang_code: str):
    """Load (once) and return the Kokoro pipeline for a language code."""
    with _lock:
        if lang_code not in _pipelines:
            from kokoro import KPipeline

            logger.info("Loading Kokoro pipeline lang_code=%s", lang_code)
            _pipelines[lang_code] = KPipeline(
                lang_code=lang_code, repo_id=MODEL_ID, device="cpu"
            )
            logger.info("Kokoro pipeline ready lang_code=%s", lang_code)
        return _pipelines[lang_code]


def _to_numpy(audio: Any) -> np.ndarray:
    if hasattr(audio, "detach"):
        audio = audio.detach().cpu().numpy()
    return np.asarray(audio, dtype=np.float32)


def _synth_chunk(text: str, voice: str, speed: float) -> np.ndarray:
    pipeline = _pipeline(VOICES_BY_VOICE.get(voice, "a"))
    with torch.inference_mode():
        pieces = [
            _to_numpy(audio)
            for _, _, audio in pipeline(text, voice=voice, speed=speed)
        ]
    if not pieces:
        return np.zeros(0, dtype=np.float32)
    return np.concatenate(pieces)


VOICES_BY_VOICE = {voice: code for code, voice in VOICES.values()}


def _speakable_pieces(text: str, limit: int = 320) -> list[str]:
    """Keep each synthesis request short so time-to-first-audio stays low."""
    pieces: list[str] = []
    for sentence in [part.strip() for part in re.split(r"(?<=[.!?।])\s+", text) if part.strip()]:
        piece = sentence if sentence.endswith((".", "!", "?", "।")) else f"{sentence}."
        while len(piece) > limit:
            cut = max(piece.rfind(",", 0, limit), piece.rfind(" ", 0, limit))
            at = cut + 1 if cut > 40 else limit
            pieces.append(piece[:at].strip())
            piece = piece[at:].strip()
        if piece:
            pieces.append(piece)
    return pieces or [text]


def synthesise(text: str, language: str, speed: float | None = None) -> bytes:
    voice_lang, voice = _resolve(language)
    pace = round(speed or DEFAULT_SPEED, 2)
    key = (text, voice, pace)
    with _lock:
        cached = _cache.get(key)
        if cached is not None:
            _cache.move_to_end(key)
            return cached

    audio = np.concatenate([_synth_chunk(piece, voice, pace) for piece in _speakable_pieces(text)])
    buffer = io.BytesIO()
    sf.write(buffer, audio, SAMPLE_RATE, format="WAV", subtype="PCM_16")
    payload = buffer.getvalue()

    with _lock:
        _cache[key] = payload
        while len(_cache) > CACHE_SIZE:
            _cache.popitem(last=False)
    logger.info("synthesised %.1fs audio in %s (%s)", len(audio) / SAMPLE_RATE, language, voice)
    return payload


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "engine": "kokoro",
        "model": MODEL_ID,
        "sample_rate": SAMPLE_RATE,
        "speed": DEFAULT_SPEED,
        "voices": {language: voice for language, (_, voice) in VOICES.items()},
        "loaded": sorted(_pipelines),
        "cached_clips": len(_cache),
    }


@app.post("/tts")
def tts(payload: TTSRequest) -> Response:
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    try:
        audio = synthesise(text, payload.language, payload.speed)
    except Exception as exc:  # noqa: BLE001 - surface a clean 500 to the caller
        logger.exception("Synthesis failed")
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {exc}") from exc
    return Response(
        content=audio,
        media_type="audio/wav",
        headers={"Cache-Control": "no-store", "X-Voice-Engine": "kokoro"},
    )
