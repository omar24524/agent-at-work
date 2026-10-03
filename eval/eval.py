"""Ranking accuracy vs ground truth.  python eval/eval.py"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import yaml

from hiab import parse, rank

S = ROOT / "sample_data"
job = yaml.safe_load((S / "job.yaml").read_text(encoding="utf-8"))
truth = json.loads((S / "ground_truth.json").read_text(encoding="utf-8"))["expected_top3"]
extra = job["must_have"] + job["nice_to_have"]
profiles = [parse.parse_cv(p.read_text(encoding="utf-8"), p.name, extra, i) for i, p in enumerate(sorted((S / "cvs").glob("*.txt")), 1)]
res = rank.rank_all(profiles, job)
for i, r in enumerate(res, 1):
    print(f"{i:>2}. {r['name']:<14} {r['score']:>5}  {r['rec']:<9} {r['reason']}")
top3 = [r["name"] for r in res[:3]]
hits = len(set(top3) & set(truth))
print(f"\nTop-3 overlap with ground truth: {hits}/3   exact order: {top3 == truth}")
