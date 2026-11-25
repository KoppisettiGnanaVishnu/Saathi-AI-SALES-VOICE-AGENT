from __future__ import annotations

from datetime import datetime

from app import config, db, slots
from app.agent import (
    _advance_stage,
    _clean_updates,
    _extract_lead_facts,
    _is_affirmative,
    _wants_booking,
    compute_score,
    lead_status,
)
from app.llm import extract_json
from app.rag import KnowledgeBase


def test_high_intent_lead_scores_hot():
    lead = {
        "name": "Priya",
        "company": "Acme Retail",
        "need": "inbound sales calls",
        "budget": "$2,000 per month",
        "timeline": "3 weeks",
        "decision_role": "Head of Sales",
        "email": "priya@acme.com",
    }
    score = compute_score(lead, 0.6)
    assert score == 100
    assert lead_status(score) == "hot"


def test_empty_lead_scores_cold():
    assert compute_score({}, 0.0) == 0
    assert compute_score({}, -0.5) == 0
    assert lead_status(0) == "cold"


def test_partial_lead_is_warm():
    lead = {"need": "customer support automation", "budget": "$500/month"}
    score = compute_score(lead, 0.1)
    assert 40 <= score < 70
    assert lead_status(score) == "warm"


def test_clean_updates_filters_placeholders_and_normalises():
    updates = _clean_updates(
        {
            "name": "  Priya  ",
            "budget": "unknown",
            "timeline": None,
            "need": "inbound   sales calls",
            "company": 123,
            "email": "not provided",
        }
    )
    assert updates["name"] == "Priya"
    assert updates["need"] == "inbound sales calls"
    assert updates["company"] == "123"
    assert "budget" not in updates
    assert "email" not in updates
    assert "timeline" not in updates


def test_affirmative_detection():
    assert _is_affirmative("Yes, book the first one")
    assert _is_affirmative("book it")
    assert _is_affirmative("हाँ")
    assert not _is_affirmative("not interested")
    assert not _is_affirmative("")


def test_booking_intent_detection_in_english_and_hindi():
    assert _wants_booking("book a demo this week")
    assert _wants_booking("पहला स्लॉट बुक कर दीजिए")
    assert _wants_booking("डेमो शेड्यूल करें")
    assert not _wants_booking("tell me about pricing")


def test_deterministic_lead_extraction():
    first = _extract_lead_facts(
        "Hi, I'm Priya from Acme Retail. We need an AI agent for inbound calls."
    )
    assert first["name"] == "Priya"
    assert first["company"] == "Acme Retail"
    assert first["need"] == "an AI agent for inbound calls"

    second = _extract_lead_facts(
        "Our budget is around $2,000 per month and we want to launch in 3 weeks. "
        "I'm the head of sales."
    )
    assert second["budget"] == "$2,000 per month"
    assert second["timeline"] == "in 3 weeks"
    assert second["decision_role"] == "Head of Sales"

    hindi = _extract_lead_facts(
        "हमें इनबाउंड सेल्स कॉल्स के लिए AI एजेंट चाहिए। "
        "बजट $2,000 प्रति महीना है और हम 3 हफ्तों में शुरू करना चाहते हैं।"
    )
    assert hindi["need"] == "इनबाउंड सेल्स कॉल्स के लिए AI एजेंट"
    assert hindi["budget"] == "$2,000 प्रति महीना"
    assert hindi["timeline"] == "3 हफ्तों"


def test_stage_advances_from_captured_fields():
    assert _advance_stage("greeting", "greeting", {"name": "Priya"}, False) == "discovery"
    qualified = {"need": "sales", "budget": "$2k", "timeline": "3 weeks"}
    assert _advance_stage("discovery", "discovery", qualified, False) == "qualification"
    assert _advance_stage("qualification", "booking", qualified, True) == "closing"


def test_extract_json_handles_code_fences_and_trailing_commas():
    assert extract_json('```json\n{"reply": "hi"}\n```') == {"reply": "hi"}
    assert extract_json('Sure, here it is: {"a": 1,}') == {"a": 1}


def test_keyword_rag_finds_pricing():
    kb = KnowledgeBase(config.KNOWLEDGE_DIR)
    kb.load()
    results = kb.search("how much does it cost per month", k=3)
    assert results
    assert any(
        "pricing" in item["source"].lower() or "price" in item["text"].lower()
        for item in results
    )


def test_keyword_rag_handles_hindi_pricing_query():
    kb = KnowledgeBase(config.KNOWLEDGE_DIR)
    kb.load()
    results = kb.search("आपकी कीमत क्या है?", k=3)
    assert results
    assert any(
        "pricing" in item["source"].lower() or "कीमत" in item["text"]
        for item in results
    )


def test_slots_are_unique_weekdays():
    all_slots = slots._all_slots()
    assert len(all_slots) == 9
    assert len({item["id"] for item in all_slots}) == 9
    for item in all_slots:
        assert datetime.fromisoformat(item["iso"]).weekday() < 5


def test_booking_prevents_double_booking(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "test.db")
    db.init_db()

    slot = slots.get_available_slots(limit=1)[0]
    assert db.book_appointment("session-1", slot["id"], slot["iso"]) is True
    assert db.book_appointment("session-2", slot["id"], slot["iso"]) is False
    assert slot["iso"] in db.list_booked_slot_isos()
