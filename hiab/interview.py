"""Interview kits: instant template kit, optional LLM probing questions."""


def template_kit(res: dict, job: dict) -> dict:
    qs = []
    for s in res["matched_must"][:3]:
        qs.append(f"Tell me about a real project where you used {s}. What did you decide, and what went wrong?")
    for s in res["missing_must"][:2]:
        qs.append(f"{s} is required here but isn't on your CV. What's the closest thing you've done, and how would you ramp up?")
    if res["years"] < float(job.get("min_years", 0)):
        qs.append("You have less experience than we asked for. Which project shows you can work independently?")
    qs.append("Describe a technical disagreement with a teammate. How was it resolved?")
    rubric = [
        {"Competency": s, "Strong answer looks like": f"Concrete, recent examples of {s} in real work", "Score (1-5)": ""}
        for s in job["must_have"]
    ]
    return {"questions": qs, "rubric": rubric}


def ai_questions(llm, res: dict, job: dict, text: str) -> str:
    system = "You are a hiring manager's assistant. Be brief and specific."
    user = (
        f"Role: {job['title']}\nCandidate CV (excerpt):\n{text[:1200]}\n\n"
        "Write 3 short interview questions that probe specific claims in this CV. One per line, no numbering."
    )
    return llm.chat(system, user, max_tokens=120)


def kit_markdown(res: dict, job: dict, kit: dict, ai_text: str = "") -> str:
    out = [f"# Interview kit: {res['name']} ({job['title']})", f"Score: {res['score']} | {res['reason']}", "", "## Questions"]
    out += [f"{i}. {q}" for i, q in enumerate(kit["questions"], 1)]
    if ai_text:
        out += ["", "## AI probing questions", ai_text]
    out += ["", "## Rubric", "| Competency | Strong answer looks like | Score |", "|---|---|---|"]
    out += [f"| {r['Competency']} | {r['Strong answer looks like']} |  |" for r in kit["rubric"]]
    return "\n".join(out)
