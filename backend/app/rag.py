from __future__ import annotations

import logging
import math
import re
from pathlib import Path
from typing import Any

import numpy as np

from .llm import OllamaClient

logger = logging.getLogger(__name__)

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "your", "you", "are",
    "our", "can", "will", "have", "has", "how", "what", "why", "when", "where",
    "who", "does", "did", "was", "were", "about", "into", "over", "under", "they",
    "them", "their", "there", "here", "but", "not", "all", "any", "may", "might",
    "would", "could", "should", "please", "tell", "want", "need", "like", "just",
    "very", "much", "more", "most", "some", "such", "also", "than", "then", "now",
    "get", "got", "make", "made", "use", "using", "used", "one", "two", "new",
}

# Small query-expansion map so keyword retrieval still works for Hindi questions.
HINDI_HINTS = {
    "कीमत": "pricing price cost plan",
    "मूल्य": "pricing price cost",
    "लागत": "cost pricing price",
    "सुरक्षा": "security data privacy",
    "डेमो": "demo booking appointment",
    "बुक": "book booking appointment demo",
    "अपॉइंटमेंट": "appointment booking demo",
    "इंटीग्रेशन": "integration crm calendar",
    "भाषा": "language multilingual hindi",
    "समर्थन": "support onboarding",
    "कॉल": "call voice phone",
    "सेल्स": "sales lead qualification",
    "ग्राहक": "customer lead",
    "कंपनी": "company",
    "समय": "timeline setup time",
    "कितना": "pricing cost",
    "कैसे": "how integration security",
    "क्या": "what",
    "बजट": "budget pricing cost",
    "हफ्तों": "weeks timeline",
    "हफ्ते": "weeks timeline",
    "महीना": "month pricing",
    "महीने": "months timeline",
    "सुरक्षित": "security privacy",
    "गोपनीयता": "privacy security",
    "शुरू": "launch start timeline",
}

# English query expansion improves retrieval for short, natural sales questions.
SYNONYMS = {
    "cost": "pricing price plan",
    "costs": "pricing price plan",
    "price": "pricing cost plan",
    "pricing": "cost price plan",
    "plan": "pricing plan",
    "plans": "pricing plan",
    "quote": "pricing cost",
    "budget": "pricing cost",
    "secure": "security privacy compliance",
    "security": "secure privacy compliance",
    "privacy": "security compliance",
    "compliance": "security gdpr dpdp",
    "gdpr": "security compliance",
    "hipaa": "security compliance",
    "demo": "booking appointment schedule",
    "book": "booking appointment schedule",
    "booking": "appointment schedule demo",
    "appointment": "booking schedule demo",
    "integration": "crm calendar api",
    "integrations": "crm calendar api",
    "integrate": "integration crm calendar",
    "connects": "integration crm calendar",
    "connect": "integration crm calendar",
    "crm": "integration salesforce hubspot",
    "hubspot": "crm integration salesforce",
    "salesforce": "crm integration hubspot",
    "calendar": "booking integration",
    "language": "multilingual hindi",
    "languages": "multilingual hindi",
    "support": "onboarding help",
    "setup": "onboarding implementation",
    "latency": "performance response",
    "accuracy": "performance intent",
    "trial": "pilot pricing",
    "telephony": "phone call twilio",
}


def _tokenize(text: str) -> list[str]:
    raw = re.findall(r"[a-zA-Z0-9\u0900-\u097F]+", (text or "").lower())
    tokens: list[str] = []
    for token in raw:
        if token in HINDI_HINTS:
            tokens.extend(HINDI_HINTS[token].split())
        if token in SYNONYMS:
            tokens.extend(SYNONYMS[token].split())
        if len(token) > 2 and token not in STOPWORDS:
            tokens.append(token)
    return tokens


def _expand_query(text: str) -> str:
    """Append English hints so a Hindi query can reach English documents."""
    hints: list[str] = []
    for token, hint in HINDI_HINTS.items():
        if token in text:
            hints.extend(hint.split())
    if not hints:
        return text
    unique = list(dict.fromkeys(hints))
    return f"{text} {' '.join(unique)}"


def _chunk_markdown(text: str, source: str) -> list[dict[str, str]]:
    chunks: list[dict[str, str]] = []
    sections = re.split(r"\n(?=#{1,3} )", text)

    for section in sections:
        section = section.strip()
        if not section:
            continue
        heading = section.splitlines()[0].lstrip("#").strip() or source

        if len(section) <= 900:
            chunks.append({"source": source, "heading": heading, "text": section})
            continue

        buffer = ""
        for paragraph in section.split("\n\n"):
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            if buffer and len(buffer) + len(paragraph) > 800:
                chunks.append(
                    {"source": source, "heading": heading, "text": buffer.strip()}
                )
                buffer = paragraph
            else:
                buffer = f"{buffer}\n\n{paragraph}".strip()
        if buffer:
            chunks.append({"source": source, "heading": heading, "text": buffer})

    return chunks


def _keyword_score(query_tokens: set[str], chunk: dict[str, str]) -> float:
    if not query_tokens:
        return 0.0
    chunk_tokens = set(_tokenize(chunk["text"] + " " + chunk["heading"]))
    heading_tokens = set(_tokenize(chunk["heading"]))
    overlap = len(query_tokens & chunk_tokens)
    heading_overlap = len(query_tokens & heading_tokens)
    return (overlap / math.sqrt(len(query_tokens))) + (0.5 * heading_overlap)


def _source_boost(query_tokens: set[str], source: str) -> float:
    """Prefer the most authoritative document for common sales intents."""
    source_lower = source.lower()
    boost = 0.0

    if query_tokens & {"pricing", "price", "cost", "costs", "plan", "plans", "quote"}:
        if "pricing" in source_lower:
            boost += 1.5
    if query_tokens & {
        "security",
        "secure",
        "privacy",
        "compliance",
        "gdpr",
        "dpdp",
        "hipaa",
    }:
        if "security" in source_lower:
            boost += 1.5
    if query_tokens & {"demo", "book", "booking", "appointment", "schedule", "meeting"}:
        if "faq" in source_lower or "product" in source_lower:
            boost += 0.5
    if query_tokens & {"integration", "integrations", "crm", "calendar", "telephony"}:
        if "product" in source_lower or "faq" in source_lower:
            boost += 0.5
    return boost


class KnowledgeBase:
    """Local markdown knowledge base with embeddings + keyword fallback."""

    def __init__(self, directory: Path | str, llm: OllamaClient | None = None) -> None:
        self.directory = Path(directory)
        self.llm = llm
        self.chunks: list[dict[str, str]] = []
        self.vectors: np.ndarray | None = None
        self.mode = "keyword"
        self.loaded = False

    def load(self) -> None:
        if self.loaded:
            return
        self.chunks = []
        if self.directory.exists():
            for path in sorted(self.directory.glob("*.md")):
                text = path.read_text(encoding="utf-8", errors="ignore")
                self.chunks.extend(_chunk_markdown(text, path.name))
        if not self.chunks:
            logger.warning("No knowledge documents found in %s", self.directory)
        self.loaded = True

    def build_index(self, use_embeddings: bool = True) -> None:
        self.load()
        self.vectors = None
        self.mode = "keyword"

        if not use_embeddings or not self.llm or not self.chunks:
            return

        try:
            vectors = self.llm.embed([chunk["text"] for chunk in self.chunks])
            matrix = np.asarray(vectors, dtype=np.float32)
            norms = np.linalg.norm(matrix, axis=1, keepdims=True)
            self.vectors = matrix / np.clip(norms, 1e-8, None)
            self.mode = "embeddings"
            logger.info("RAG index ready: %s chunks (embeddings)", len(self.chunks))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Embedding index unavailable; using keyword search: %s", exc)
            self.vectors = None
            self.mode = "keyword"

    def _keyword_search(self, query: str, k: int) -> list[dict[str, Any]]:
        query_tokens = set(_tokenize(query))
        if not query_tokens:
            return []
        scored = [
            (
                _keyword_score(query_tokens, chunk)
                + _source_boost(query_tokens, chunk["source"]),
                chunk,
            )
            for chunk in self.chunks
        ]
        scored = [item for item in scored if item[0] > 0]
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            {**chunk, "score": round(score, 3)} for score, chunk in scored[:k]
        ]

    def search(self, query: str, k: int = 3) -> list[dict[str, Any]]:
        if not query or not query.strip():
            return []
        self.load()

        if self.mode == "embeddings" and self.vectors is not None and self.llm:
            try:
                query_vector = np.asarray(
                    self.llm.embed([_expand_query(query)])[0], dtype=np.float32
                )
                norm = float(np.linalg.norm(query_vector))
                if norm > 0:
                    query_vector = query_vector / norm
                    scores = self.vectors @ query_vector
                    order = np.argsort(scores)[::-1][:k]
                    query_tokens = set(_tokenize(query))
                    results = [
                        {
                            **self.chunks[index],
                            "score": round(
                                float(scores[index])
                                + (
                                    _source_boost(
                                        query_tokens, self.chunks[index]["source"]
                                    )
                                    * 0.08
                                ),
                                3,
                            ),
                        }
                        for index in order
                    ]
                    results.sort(key=lambda item: item["score"], reverse=True)
                    if results and results[0]["score"] >= 0.2:
                        return results
            except Exception as exc:  # noqa: BLE001
                logger.warning("Embedding search failed; using keyword search: %s", exc)

        return self._keyword_search(query, k)

    @staticmethod
    def format_context(results: list[dict[str, Any]]) -> str:
        if not results:
            return "No relevant knowledge found."
        blocks = []
        for index, result in enumerate(results, start=1):
            blocks.append(
                f"[{index}] Source: {result['source']} — {result['heading']}\n"
                f"{result['text']}"
            )
        return "\n\n".join(blocks)
