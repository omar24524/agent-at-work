"""ROI model. All assumptions are editable in the UI; outputs are estimates, not guarantees."""

DEFAULTS = dict(
    hourly_rate=15.0,       # cost of the owner's/HR time, per hour
    min_per_cv=4.0,         # manual minutes to read and judge one CV
    min_per_kit=20.0,       # manual minutes to prepare an interview kit
    min_per_schedule=12.0,  # manual minutes of email back-and-forth per interview
    vacancy_day_value=100.0,  # value of one day with the role filled
    days_saved=3.0,         # days earlier the shortlist is ready
)


def compute(n_cvs: int, n_kits: int, n_scheduled: int, agent_seconds: float, assumptions: dict = None) -> dict:
    a = {**DEFAULTS, **(assumptions or {})}
    manual_min = n_cvs * a["min_per_cv"] + n_kits * a["min_per_kit"] + n_scheduled * a["min_per_schedule"]
    agent_min = agent_seconds / 60
    hours_saved = max(manual_min - agent_min, 0) / 60
    return {
        "manual_minutes": round(manual_min, 1),
        "agent_minutes": round(agent_min, 2),
        "hours_saved": round(hours_saved, 2),
        "cost_saved": round(hours_saved * a["hourly_rate"], 2),
        "revenue_value": round(a["days_saved"] * a["vacancy_day_value"], 2) if n_cvs else 0.0,
    }
