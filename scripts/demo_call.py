"""Run a complete scripted sales call against a running backend.

Usage:
    python scripts/demo_call.py
    python scripts/demo_call.py --language hi-IN
"""

from __future__ import annotations

import argparse
import json

import httpx

BASE_URL = "http://localhost:8000"

ENGLISH_TURNS = [
    "Hi, I'm Priya from Acme Retail. We need an AI agent to handle inbound sales calls.",
    "What does it cost?",
    "We have a budget of around $2,000 per month and want to launch in 3 weeks. I'm the head of sales.",
    "Yes, book the first slot.",
]

HINDI_TURNS = [
    "नमस्ते, मैं प्रिया हूँ। हमें इनबाउंड सेल्स कॉल्स के लिए AI एजेंट चाहिए।",
    "आपकी कीमत क्या है?",
    "हमारा बजट लगभग $2,000 प्रति महीना है और हम 3 हफ्तों में शुरू करना चाहते हैं।",
    "हाँ, पहला स्लॉट बुक कर दीजिए।",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", default="en-IN", choices=["en-IN", "hi-IN"])
    args = parser.parse_args()
    turns = HINDI_TURNS if args.language == "hi-IN" else ENGLISH_TURNS

    with httpx.Client(base_url=BASE_URL, timeout=180.0) as client:
        health = client.get("/api/health")
        health.raise_for_status()
        print("HEALTH")
        print(json.dumps(health.json(), indent=2)[:800])
        print()

        session = client.post("/api/session")
        session.raise_for_status()
        data = session.json()
        session_id = data["session_id"]

        print(f"SESSION {session_id}")
        print(f"Mira: {data['greeting']}\n")

        for message in turns:
            print(f"Customer: {message}")
            response = client.post(
                "/api/chat",
                json={
                    "session_id": session_id,
                    "message": message,
                    "language": args.language,
                },
            )
            response.raise_for_status()
            result = response.json()
            print(f"Mira: {result['reply']}")
            print(
                f"  score={result['lead_score']} status={result['lead_status']} "
                f"stage={result['stage']} sentiment={result['sentiment']} "
                f"sources={result.get('knowledge_used')}"
            )
            if result.get("booking"):
                print(f"  BOOKED: {result['booking']['label']}")
            print()

        summary = client.post(f"/api/session/{session_id}/end")
        summary.raise_for_status()
        payload = summary.json()
        print("SUMMARY")
        print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))
        print(f"\nDuration: {payload['duration_seconds']}s")
        print(f"Lead score: {payload['lead_score']} ({payload['lead_status']})")
        if payload.get("booking"):
            print(f"Booking: {payload['booking']['label']}")


if __name__ == "__main__":
    main()
