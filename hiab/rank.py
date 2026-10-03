"""Transparent scoring: every point can be traced back to a line in the CV."""
from .parse import aliases_for, _pat

W_MUST, W_NICE, W_EXP = 0.55, 0.15, 0.30


def _evidence(text: str, skill: str) -> str:
    aliases = list(aliases_for(skill))
    if skill == "SQL":
        aliases += ["postgresql", "postgres", "mysql"]
    for line in text.splitlines():
        if any(_pat(a).search(line) for a in aliases):
            return line.strip()[:140]
    return ""


def score_candidate(p: dict, job: dict) -> dict:
    have = {s.lower() for s in p["skills"]}
    must, nice = job["must_have"], job.get("nice_to_have", [])
    m_hit = [s for s in must if s.lower() in have]
    m_miss = [s for s in must if s.lower() not in have]
    n_hit = [s for s in nice if s.lower() in have]
    min_y = float(job.get("min_years", 0))
    exp = 1.0 if min_y <= 0 else min(p["years"] / min_y, 1.0)
    must_r = len(m_hit) / len(must) if must else 1.0
    nice_r = len(n_hit) / len(nice) if nice else 0.0
    score = round(100 * (W_MUST * must_r + W_NICE * nice_r + W_EXP * exp), 1)
    rec = "Interview" if (score >= 75 and not m_miss) else "Maybe" if score >= 55 else "Hold"  # missing must-have caps at Maybe
    reason = f"Meets {len(m_hit)}/{len(must)} must-haves; {p['years']:.0f} yrs vs {min_y:.0f} required."
    if m_miss:
        reason += f" Missing: {', '.join(m_miss)}."
    if n_hit:
        reason += f" Bonus: {', '.join(n_hit)}."
    return {
        "id": p["id"], "idx": p["idx"], "name": p["name"], "email": p["email"],
        "title": p["title"], "years": p["years"], "score": score, "rec": rec,
        "matched_must": m_hit, "missing_must": m_miss, "matched_nice": n_hit,
        "reason": reason, "text": p["text"],
        "evidence": {s: _evidence(p["text"], s) for s in m_hit},
    }


def rank_all(profiles: list, job: dict) -> list:
    res = [score_candidate(p, job) for p in profiles]
    return sorted(res, key=lambda r: (-r["score"], -r["years"]))
