from __future__ import annotations

from datetime import date, datetime, time, timedelta

from . import db

SLOT_TIMES = [(11, 0), (15, 0), (17, 0)]
BUSINESS_DAYS = 3


def _all_slots() -> list[dict[str, str]]:
    """Generate demo slots for the next few business days (local time)."""
    slots: list[dict[str, str]] = []
    cursor = date.today()
    generated_days = 0

    while generated_days < BUSINESS_DAYS:
        cursor += timedelta(days=1)
        if cursor.weekday() >= 5:  # skip Saturday/Sunday
            continue
        generated_days += 1
        for hour, minute in SLOT_TIMES:
            slot_dt = datetime.combine(cursor, time(hour, minute))
            slots.append(
                {
                    "id": slot_dt.strftime("%Y%m%d-%H%M"),
                    "iso": slot_dt.isoformat(),
                    "label": slot_dt.strftime("%a, %d %b · %I:%M %p"),
                }
            )
    return slots


def get_available_slots(limit: int = 6) -> list[dict[str, str]]:
    booked = db.list_booked_slot_isos()
    available = [slot for slot in _all_slots() if slot["iso"] not in booked]
    return available[:limit]


def find_available_slot(slot_id: str) -> dict[str, str] | None:
    for slot in get_available_slots(limit=100):
        if slot["id"] == slot_id:
            return slot
    return None
