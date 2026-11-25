from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1)
    message: str = Field(min_length=1, max_length=2000)
    language: str = Field(default="en-IN", max_length=20)


class BookRequest(BaseModel):
    slot_id: str = Field(min_length=1, max_length=64)


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=600)
    language: str = Field(default="en-IN", max_length=20)
