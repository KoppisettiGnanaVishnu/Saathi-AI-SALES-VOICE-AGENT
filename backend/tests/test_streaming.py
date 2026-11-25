"""Tests for incremental reply extraction used by the streaming endpoint."""

from app.agent import _ReplyExtractor


def _collect(raw: str, size: int) -> list[str]:
    extractor = _ReplyExtractor()
    sentences: list[str] = []
    for index in range(0, len(raw), size):
        sentences.extend(extractor.feed(raw[index : index + size]))
    sentences.extend(extractor.flush())
    return sentences


def test_extracts_sentences_before_json_finishes():
    raw = (
        '{"reply": "Hi Priya, great to meet you. Our Growth plan is $499 per month. '
        'Would you like a demo?", "sentiment": "positive", "lead_score": 88}'
    )
    assert _collect(raw, 400) == [
        "Hi Priya, great to meet you.",
        "Our Growth plan is $499 per month.",
        "Would you like a demo?",
    ]


def test_chunk_boundaries_do_not_change_output():
    raw = (
        '{"reply": "One short sentence. Another one follows here! '
        'Is that clear?", "stage": "discovery"}'
    )
    assert _collect(raw, 1) == _collect(raw, 5) == _collect(raw, 1000)


def test_decodes_escaped_unicode_and_quotes():
    raw = (
        '{"reply": "\\u0928\\u092e\\u0938\\u094d\\u0924\\u0947! '
        '\\"Great\\" plan. Done.", "x": 1}'
    )
    assert _collect(raw, 4) == ["नमस्ते!", '"Great" plan.', "Done."]


def test_decimal_points_are_not_sentence_breaks():
    raw = '{"reply": "It costs 3.5 dollars per call. Deal?", "x": 1}'
    assert _collect(raw, 2) == ["It costs 3.5 dollars per call.", "Deal?"]
