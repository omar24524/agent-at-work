# Hire-in-a-Box

A local agent for small businesses that turns a pile of CVs into a ranked shortlist, interview kits and booked interviews. Nothing leaves your machine.

## Run it
```bash
pip install -r requirements.txt
python scripts/make_sample_data.py     # 12 synthetic CVs + ground truth
streamlit run app.py
```
Press **Run screening**. Screening and scheduling need no model. The optional local LLM (llama-cpp, GGUF path in `config.yaml`) adds extra interview questions.

## How it works
1. **Parse**: rule-based extraction of skills and years of experience (instant, deterministic).
2. **Rank**: transparent score = 55% must-haves, 15% nice-to-haves, 30% experience. Every match cites a CV line. A missing must-have caps the recommendation at "Maybe".
3. **Interview kit**: tailored questions and a scoring rubric, optionally extended by the local LLM.
4. **Schedule**: matches slots, writes `.ics` invites and email drafts from a mock inbox.
5. **ROI**: measured agent time vs editable manual-effort assumptions.

## Accuracy
`python eval/eval.py` compares the top 3 with ground truth (currently 3/3).

## Responsible use
The agent recommends, a human approves the shortlist. Blind mode hides names and emails.
