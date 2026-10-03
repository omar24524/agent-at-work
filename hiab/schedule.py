"""Offline scheduling: slot matching, .ics invites, email drafts. No real calendar needed."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4


def interviewer_slots(days: int = 5, hours=(10, 11, 14, 15), now: datetime = None) -> list:
    d = (now or datetime.now()).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    slots = []
    while len(slots) < days * len(hours):
        if d.weekday() not in (4, 5):  # skip Fri/Sat
            slots += [d.replace(hour=h) for h in hours]
        d += timedelta(days=1)
    return slots


def label(dt: datetime) -> str:
    return dt.strftime("%a %H:%M")


def schedule_all(candidates: list, availability: dict, slots: list) -> list:
    """candidates: list of dicts with name/email. Never double-books a slot."""
    taken, out = set(), []
    for c in candidates:
        free = [s for s in slots if s not in taken]
        avail = availability.get(c["name"])
        if avail is None:
            out.append({**c, "status": "proposed", "slot": None, "options": free[:3]})
            continue
        match = next((s for s in free if label(s) in avail), None)
        if match:
            taken.add(match)
            out.append({**c, "status": "booked", "slot": match, "options": []})
        else:
            out.append({**c, "status": "no_overlap", "slot": None, "options": free[:3]})
    return out


def make_ics(summary: str, start: datetime, minutes: int = 45, email: str = "") -> str:
    fmt = "%Y%m%dT%H%M%S"
    lines = [
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//agent-at-work//EN", "BEGIN:VEVENT",
        f"UID:{uuid4()}@agent-at-work",
        f"DTSTAMP:{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}",
        f"DTSTART:{start.strftime(fmt)}",
        f"DTEND:{(start + timedelta(minutes=minutes)).strftime(fmt)}",
        f"SUMMARY:{summary}",
    ]
    if email:
        lines.append(f"ATTENDEE:mailto:{email}")
    lines += ["END:VEVENT", "END:VCALENDAR"]
    return "\r\n".join(lines)


def email_draft(item: dict, role: str, company: str = "our team") -> str:
    first = item["name"].split()[0]
    if item["status"] == "booked":
        when = item["slot"].strftime("%A %d %B at %H:%M")
        body = f"We'd like to invite you to a 45-minute interview for the {role} role on {when}. A calendar invite is attached."
    else:
        opts = "\n".join(f"  - {s.strftime('%A %d %B at %H:%M')}" for s in item["options"])
        body = f"We'd like to invite you to a 45-minute interview for the {role} role. Which of these times suits you?\n{opts}"
    return f"Subject: Interview invitation - {role}\n\nHi {first},\n\nThanks for applying. {body}\n\nBest regards,\n{company}"
