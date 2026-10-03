"""Hire-in-a-Box dashboard.  Run:  streamlit run app.py"""
import json
import time
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

from hiab import interview, parse, rank, roi, schedule

ROOT = Path(__file__).parent
SAMPLE = ROOT / "sample_data"

st.set_page_config(page_title="Hire-in-a-Box", page_icon="🧰", layout="wide")


@st.cache_resource(show_spinner="Loading local model (first time only, can take a minute)...")
def get_llm():
    from hiab.llm import LLM

    llm = LLM()
    llm._load()
    return llm


def split(text):
    return [s.strip() for s in text.replace("\n", ",").split(",") if s.strip()]


ss = st.session_state
for k, v in dict(results=None, run_id=0, agent_seconds=0.0, schedule=None, ai_text={}, n_cvs=0).items():
    ss.setdefault(k, v)

# ---------------- sidebar ----------------
base = yaml.safe_load((SAMPLE / "job.yaml").read_text(encoding="utf-8"))
with st.sidebar:
    st.header("Role")
    title = st.text_input("Job title", base["title"])
    must = split(st.text_area("Must-have skills (comma separated)", ", ".join(base["must_have"])))
    nice = split(st.text_area("Nice-to-have skills", ", ".join(base["nice_to_have"])))
    min_years = st.number_input("Minimum years of experience", 0, 20, int(base["min_years"]))
    st.header("Options")
    use_ai = st.checkbox("Use local LLM for extra interview questions", value=False,
                         help="Optional and slow on CPU. Screening and scheduling work without it.")
    st.checkbox("Blind mode (hide names and emails)", key="blind")
    with st.expander("ROI assumptions"):
        a = dict(
            hourly_rate=st.number_input("Hourly cost of HR/owner time", 1.0, 500.0, roi.DEFAULTS["hourly_rate"]),
            min_per_cv=st.number_input("Manual minutes per CV", 0.5, 30.0, roi.DEFAULTS["min_per_cv"]),
            min_per_kit=st.number_input("Manual minutes per interview kit", 1.0, 120.0, roi.DEFAULTS["min_per_kit"]),
            min_per_schedule=st.number_input("Manual minutes per scheduling", 1.0, 60.0, roi.DEFAULTS["min_per_schedule"]),
            vacancy_day_value=st.number_input("Value of one day with role filled", 0.0, 5000.0, roi.DEFAULTS["vacancy_day_value"]),
            days_saved=st.number_input("Days earlier the shortlist is ready", 0.0, 30.0, roi.DEFAULTS["days_saved"]),
        )

job = {"title": title, "must_have": must, "nice_to_have": nice, "min_years": min_years}


def label(r):
    return f"Candidate #{r['idx']:02d}" if ss.get("blind") else r["name"]


# ---------------- header + intake ----------------
st.title("🧰 Hire-in-a-Box")
st.caption("Local hiring agent: screens CVs, prepares interview kits, books interviews. Everything runs on this machine. You decide, the agent recommends.")

c1, c2 = st.columns([2, 1])
uploads = c1.file_uploader("Add your own CVs (PDF or TXT)", type=["pdf", "txt"], accept_multiple_files=True)
use_sample = c2.checkbox("Include the 12 sample CVs", value=True)

if st.button("Run screening", type="primary"):
    t0 = time.perf_counter()
    cvs = [(p.name, p.read_bytes()) for p in sorted((SAMPLE / "cvs").glob("*.txt"))] if use_sample else []
    cvs += [(f.name, f.getvalue()) for f in (uploads or [])]
    if not cvs or not must:
        st.warning("Add at least one CV and one must-have skill.")
    else:
        profiles = [parse.parse_cv(parse.read_bytes(n, b), n, must + nice, i) for i, (n, b) in enumerate(cvs, 1)]
        ss.results = rank.rank_all(profiles, job)
        ss.job = job
        ss.n_cvs = len(profiles)
        ss.run_id += 1
        ss.schedule = None
        ss.ai_text = {}
        ss.agent_seconds = time.perf_counter() - t0

if not ss.results:
    st.info("Add CVs (or keep the samples) and press **Run screening**.")
    st.stop()

results, job = ss.results, ss.job
by_id = {r["id"]: r for r in results}
st.success(f"Screened {ss.n_cvs} CVs in {ss.agent_seconds:.2f}s.")
tab_rank, tab_kit, tab_sched, tab_roi = st.tabs(["1. Ranking", "2. Interview kits", "3. Scheduling", "4. ROI"])

# ---------------- ranking ----------------
with tab_rank:
    rows = [{
        "Rank": i, "Candidate": label(r), "Score": r["score"], "Years": r["years"],
        "Must-haves": f"{len(r['matched_must'])}/{len(job['must_have'])}",
        "Missing": ", ".join(r["missing_must"]) or "-", "Recommendation": r["rec"], "Why": r["reason"],
    } for i, r in enumerate(results, 1)]
    st.dataframe(pd.DataFrame(rows), hide_index=True,
                 column_config={"Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f")})
    default = [r["id"] for r in results if r["rec"] == "Interview"][:5]
    shortlist = st.multiselect("Approve the shortlist (you decide, not the agent)", [r["id"] for r in results],
                               default=default, format_func=lambda i: label(by_id[i]), key=f"sl_{ss.run_id}")

# ---------------- interview kits ----------------
with tab_kit:
    if not shortlist:
        st.info("Approve at least one candidate in the Ranking tab.")
    else:
        sel = st.selectbox("Candidate", shortlist, format_func=lambda i: label(by_id[i]))
        res = by_id[sel]
        st.write(f"**Score {res['score']}** · {res['reason']}")
        with st.expander("Evidence from the CV"):
            for s, line in res["evidence"].items():
                st.markdown(f"- **{s}**: {line}")
        kit = interview.template_kit(res, job)
        st.subheader("Questions")
        for i, q in enumerate(kit["questions"], 1):
            st.markdown(f"{i}. {q}")
        if use_ai:
            if st.button("Generate AI probing questions", key=f"ai_{ss.run_id}_{sel}"):
                with st.spinner("Local model is thinking (can take a minute on CPU)..."):
                    t0 = time.perf_counter()
                    ss.ai_text[sel] = interview.ai_questions(get_llm(), res, job, res["text"])
                    ss.agent_seconds += time.perf_counter() - t0
        if sel in ss.ai_text:
            st.subheader("AI probing questions")
            st.markdown(ss.ai_text[sel])
        st.subheader("Scoring rubric")
        st.dataframe(pd.DataFrame(kit["rubric"]), hide_index=True)
        st.download_button("Download kit (.md)", interview.kit_markdown(res, job, kit, ss.ai_text.get(sel, "")),
                           file_name=f"kit_{res['id']}.md")

# ---------------- scheduling ----------------
with tab_sched:
    if not shortlist:
        st.info("Approve at least one candidate in the Ranking tab.")
    else:
        avail_path = SAMPLE / "availability.json"
        availability = json.loads(avail_path.read_text(encoding="utf-8")) if avail_path.exists() else {}
        st.caption("Candidate availability comes from a mock inbox (sample_data/availability.json). No real email or calendar is touched.")
        if st.button("Schedule shortlisted candidates"):
            t0 = time.perf_counter()
            ss.schedule = schedule.schedule_all([by_id[i] for i in shortlist], availability, schedule.interviewer_slots())
            ss.agent_seconds += time.perf_counter() - t0
        for it in ss.schedule or []:
            who = label(it)
            icon = {"booked": "✅", "proposed": "📨", "no_overlap": "⚠️"}[it["status"]]
            when = it["slot"].strftime("%a %d %b %H:%M") if it["slot"] else "options sent"
            with st.expander(f"{icon} {who}: {when}"):
                st.text_area("Email draft", schedule.email_draft(it, job["title"]), height=220, key=f"em_{ss.run_id}_{it['id']}")
                if it["slot"]:
                    st.download_button("Download .ics invite",
                                       schedule.make_ics(f"Interview: {job['title']} - {who}", it["slot"], email=it["email"]),
                                       file_name=f"{it['id']}.ics", key=f"ics_{ss.run_id}_{it['id']}")

# ---------------- ROI ----------------
with tab_roi:
    n_sched = len(ss.schedule or [])
    out = roi.compute(ss.n_cvs, len(shortlist), n_sched, ss.agent_seconds, a)
    m1, m2, m3 = st.columns(3)
    m1.metric("Time saved", f"{out['hours_saved']:.1f} h", help="Manual minutes minus measured agent time")
    m2.metric("Cost saved", f"${out['cost_saved']:,.0f}")
    m3.metric("Revenue (estimated)", f"${out['revenue_value']:,.0f}", help="Value of filling the role earlier")
    st.write(f"Manual effort: **{out['manual_minutes']} min** vs agent: **{out['agent_minutes']} min** "
             f"({ss.n_cvs} CVs, {len(shortlist)} kits, {n_sched} interviews scheduled).")
    st.caption("Estimates based on the editable assumptions in the sidebar. The agent time is measured, the manual time is assumed.")
