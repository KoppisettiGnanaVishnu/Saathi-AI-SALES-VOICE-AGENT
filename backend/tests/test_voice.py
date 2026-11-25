"""Tests for the speech layer: text normalisation, chunking and fallbacks."""

from app.tts import VoiceClient
from app.tts_text import normalise_for_speech, split_sentences


def test_english_price_and_time_are_spoken_naturally():
    spoken = normalise_for_speech(
        "The Growth plan is $499 per month. A demo is booked for Thu, 26 Nov · 11:00 AM.",
        "en-IN",
    )
    assert "four hundred and ninety-nine dollars" in spoken
    assert "Thursday" in spoken
    assert "eleven AM" in spoken
    assert "$" not in spoken
    assert ":" not in spoken


def test_hindi_currency_and_numbers_use_hindi_words():
    spoken = normalise_for_speech(
        "बजट $2,000 प्रति महीना है और हम 3 हफ्तों में शुरू करना चाहते हैं।", "hi-IN"
    )
    assert "दो हज़ार डॉलर" in spoken
    assert "तीन हफ्तों" in spoken
    assert "$" not in spoken


def test_markdown_and_percent_are_cleaned():
    spoken = normalise_for_speech("**Great** — 40% cheaper than hiring reps.", "en-IN")
    assert "forty percent" in spoken
    assert "*" not in spoken
    assert "—" not in spoken


def test_split_sentences_keeps_chunks_speakable():
    chunks = split_sentences(
        "Sure. I've booked Thursday at 11 AM. Anything else you'd like in the invite?"
    )
    assert len(chunks) == 2
    assert chunks[0].startswith("Sure. I've booked")
    assert chunks[-1].endswith("?")


def test_split_sentences_handles_long_text():
    chunks = split_sentences("word, " * 120, max_chars=190)
    assert chunks
    assert all(len(chunk) <= 190 for chunk in chunks)


def test_voice_client_degrades_when_disabled():
    client = VoiceClient()
    client.enabled = False
    assert client.synthesize("Hello there.", "en-IN") is None
    assert client.status()["engine"] == "browser"
