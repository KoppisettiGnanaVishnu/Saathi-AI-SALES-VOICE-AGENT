from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse

from . import config, db
from .agent import SalesAgent
from .schemas import BookRequest, ChatRequest, TTSRequest
from .tts import VoiceClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

agent: SalesAgent | None = None
voice = VoiceClient()


@asynccontextmanager
async def lifespan(_: FastAPI):
    global agent
    db.init_db()
    logger.info("Loading knowledge base and local model client...")
    agent = SalesAgent()
    logger.info(
        "Agent ready | model=%s | rag=%s | chunks=%s",
        agent.llm.model,
        agent.kb.mode,
        len(agent.kb.chunks),
    )
    yield
    logger.info("Shutting down agent")


app = FastAPI(
    title="Saathi - Autonomous Sales Voice Agent",
    description=(
        "Open-source MVP: local LLM sales agent with a local neural voice, RAG, "
        "lead qualification, sentiment analysis, appointment booking, CRM sync "
        "and call insights."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_agent() -> SalesAgent:
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent is still starting")
    return agent


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "name": "Saathi - A companion for business conversations",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.get("/api/health")
def health() -> dict[str, Any]:
    data = get_agent().health()
    data["voice"] = voice.status()
    return data


@app.post("/api/tts")
def synthesize(payload: TTSRequest) -> Response:
    """Speak a reply with the local neural voice; 503 lets the UI fall back."""
    result = voice.synthesize(payload.text, payload.language)
    if result is None:
        raise HTTPException(status_code=503, detail="Neural voice unavailable")
    audio, engine = result
    return Response(
        content=audio,
        media_type="audio/wav",
        headers={"Cache-Control": "no-store", "X-Voice-Engine": engine},
    )


@app.post("/api/session")
def create_session() -> dict[str, Any]:
    return get_agent().create_session()


@app.get("/api/session/{session_id}")
def get_session(session_id: str) -> dict[str, Any]:
    try:
        return get_agent().public_state(get_agent()._get_session(session_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/chat")
def chat(payload: ChatRequest) -> dict[str, Any]:
    try:
        return get_agent().handle_message(
            payload.session_id, payload.message, payload.language
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Chat failed")
        raise HTTPException(status_code=500, detail="Agent error") from exc


@app.post("/api/chat/stream")
def chat_stream(payload: ChatRequest) -> StreamingResponse:
    """Newline-delimited JSON: ``sentence`` events first, then ``final``."""

    def events():
        try:
            for event in get_agent().handle_message_stream(
                payload.session_id, payload.message, payload.language
            ):
                yield json.dumps(event, ensure_ascii=False) + "\n"
        except KeyError as exc:
            yield json.dumps({"type": "error", "detail": str(exc)}) + "\n"
        except ValueError as exc:
            yield json.dumps({"type": "error", "detail": str(exc)}) + "\n"
        except Exception:  # noqa: BLE001
            logger.exception("Chat stream failed")
            yield json.dumps({"type": "error", "detail": "Agent error"}) + "\n"

    return StreamingResponse(
        events(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )


@app.post("/api/session/{session_id}/book")
def book_slot(session_id: str, payload: BookRequest) -> dict[str, Any]:
    try:
        return get_agent().book_slot(session_id, payload.slot_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/session/{session_id}/end")
def end_call(session_id: str) -> dict[str, Any]:
    try:
        return get_agent().end_call(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Call summary failed")
        raise HTTPException(status_code=500, detail="Summary error") from exc


@app.get("/api/leads")
def leads() -> dict[str, Any]:
    return {"leads": db.list_leads(limit=50)}


@app.get("/api/appointments")
def appointments() -> dict[str, Any]:
    return {"appointments": db.list_appointments(limit=50)}


@app.get("/api/calls")
def calls() -> dict[str, Any]:
    return {"calls": db.list_calls(limit=50)}


@app.get("/api/insights")
def insights() -> dict[str, Any]:
    return get_agent().insights()


@app.post("/api/demo/reset")
def reset_demo() -> dict[str, Any]:
    try:
        get_agent().reset_demo()
        return {"status": "reset", "message": "Demo data cleared"}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
