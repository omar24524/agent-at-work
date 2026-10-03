"""Rule-based CV parsing: instant and deterministic, no LLM needed."""
import io
import re
from datetime import date
from pathlib import Path

SKILL_ALIASES = {
    "Python": ["python"], "SQL": ["sql"], "PostgreSQL": ["postgresql", "postgres"],
    "MySQL": ["mysql"], "Docker": ["docker"], "Kubernetes": ["kubernetes", "k8s"],
    "Git": ["git", "github", "gitlab"], "AWS": ["aws", "amazon web services"],
    "Azure": ["azure"], "GCP": ["gcp", "google cloud"], "Linux": ["linux"],
    "FastAPI": ["fastapi"], "Django": ["django"], "Flask": ["flask"],
    "REST API": ["rest api", "rest apis", "restful api", "restful apis"],
    "CI/CD": ["ci/cd", "github actions", "jenkins", "gitlab ci"],
    "JavaScript": ["javascript"], "TypeScript": ["typescript"], "React": ["react"],
    "Node.js": ["node.js", "nodejs"], "Java": ["java"], "C#": ["c#"],
    "PyTorch": ["pytorch"], "TensorFlow": ["tensorflow"], "Pandas": ["pandas"],
    "Scikit-learn": ["scikit-learn", "sklearn"], "Spark": ["spark", "pyspark"],
    "Kafka": ["kafka"], "Airflow": ["airflow"], "MLflow": ["mlflow"],
    "Testing": ["pytest", "unit test", "unit testing"],
}

RANGE = re.compile(
    r"((?:19|20)\d{2})\s*(?:-|–|—|to)\s*((?:19|20)\d{2}|present|current|now|today)", re.I
)
EDU = re.compile(
    r"\b(b\.?sc|bachelor|m\.?sc|master|ph\.?d|diploma|degree|university|faculty|college)\b", re.I
)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def _pat(alias: str):
    return re.compile(r"(?<![A-Za-z0-9+#])" + re.escape(alias) + r"(?![A-Za-z0-9+#])", re.I)


def aliases_for(skill: str):
    return SKILL_ALIASES.get(skill, [skill.lower()])


def find_skills(text: str, extra=()):
    vocab = dict(SKILL_ALIASES)
    for s in extra:
        vocab.setdefault(s, [s.lower()])
    found = [c for c, al in vocab.items() if any(_pat(a).search(text) for a in al)]
    if ("PostgreSQL" in found or "MySQL" in found) and "SQL" not in found:
        found.append("SQL")  # engines imply SQL
    return found


def years_experience(text: str, today: date = None) -> float:
    """Sum of work date ranges (merged if overlapping). Education lines are ignored."""
    this_year = (today or date.today()).year
    spans = []
    for line in text.splitlines():
        if EDU.search(line):
            continue
        for m in RANGE.finditer(line):
            a = int(m.group(1))
            end = m.group(2).lower()
            b = int(end) if end.isdigit() else this_year
            if b >= a:
                spans.append((a, b))
    spans.sort()
    total, cs, ce = 0, None, None
    for s, e in spans:
        if ce is None or s > ce:
            if ce is not None:
                total += ce - cs
            cs, ce = s, e
        else:
            ce = max(ce, e)
    if ce is not None:
        total += ce - cs
    return float(total)


def education_level(text: str) -> str:
    t = text.lower()
    if re.search(r"ph\.?d", t):
        return "PhD"
    if re.search(r"\bm\.?sc|master", t):
        return "Master"
    if re.search(r"\bb\.?sc|bachelor", t):
        return "Bachelor"
    return "Unknown"


def read_bytes(name: str, data: bytes) -> str:
    if name.lower().endswith(".pdf"):
        import pdfplumber

        with pdfplumber.open(io.BytesIO(data)) as pdf:
            return "\n".join((p.extract_text() or "") for p in pdf.pages)
    return data.decode("utf-8", errors="ignore")


def parse_cv(text: str, filename: str = "", extra_skills=(), idx: int = 0) -> dict:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    head = lines[0] if lines else Path(filename).stem
    parts = re.split(r"\s+[-–—|]\s+", head, maxsplit=1)
    email = EMAIL.search(text)
    return {
        "id": Path(filename).stem or f"cv_{idx}",
        "idx": idx,
        "name": parts[0].strip(),
        "title": parts[1].strip() if len(parts) > 1 else "",
        "email": email.group(0) if email else "",
        "years": years_experience(text),
        "skills": find_skills(text, extra_skills),
        "education": education_level(text),
        "text": text,
    }
