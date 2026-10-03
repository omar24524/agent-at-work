"""Generate 12 synthetic CVs + job + availability + ground truth.  python scripts/make_sample_data.py"""
import json
from pathlib import Path

import yaml

OUT = Path(__file__).resolve().parent.parent / "sample_data"
(OUT / "cvs").mkdir(parents=True, exist_ok=True)

JOB = {
    "title": "Backend Developer (Python)",
    "must_have": ["Python", "SQL", "Docker", "Git", "REST API"],
    "nice_to_have": ["FastAPI", "Kubernetes", "AWS", "CI/CD", "PostgreSQL"],
    "min_years": 3,
}

# (name, title, [(role, company, start, end, [bullets])], education, skills line)
C = [
 ("Sara Ahmed", "Backend Developer", [
   ("Backend Developer", "Nile Software", "2021", "2025", ["Built REST APIs in Python (FastAPI) serving 2M requests/day", "Designed PostgreSQL schemas and tuned slow SQL queries", "Containerised services with Docker; CI/CD with GitHub Actions on AWS"]),
   ("Junior Developer", "Delta Apps", "2019", "2021", ["Django web apps and unit testing with pytest"])],
  "B.Sc. Computer Science, Cairo Univ., 2019", "Python, FastAPI, Django, PostgreSQL, Docker, AWS, Git"),
 ("Karim Hassan", "Senior Backend Engineer", [
   ("Senior Backend Engineer", "Pyramid Tech", "2018", "Present", ["Led migration to Kubernetes on AWS", "Python/Django services exposing REST APIs", "Optimised SQL and PostgreSQL workloads; Docker everywhere"]),
   ("Developer", "Sphinx Labs", "2016", "2018", ["Python scripts, Git workflows, MySQL"])],
  "B.Sc. Computer Engineering, Ain Shams Univ., 2016", "Python, Django, SQL, PostgreSQL, Docker, Kubernetes, AWS, Git"),
 ("Mona Ibrahim", "Software Engineer", [
   ("Software Engineer", "Cairo Commerce", "2020", "2025", ["Flask REST APIs for the order system", "MySQL reporting queries (SQL)", "Dockerised deployments, Git branching strategy"])],
  "B.Sc. Information Systems, Helwan Univ., 2020", "Python, Flask, MySQL, Docker, Git"),
 ("Mahmoud Reda", "Python Developer", [
   ("Python Developer", "Giza Systems", "2023", "2025", ["Django REST APIs, PostgreSQL, Docker", "Code reviews on Git pull requests"])],
  "B.Sc. Computer Science, Alexandria Univ., 2023", "Python, Django, PostgreSQL, Docker, Git"),
 ("Ali Samir", "Java Backend Developer", [
   ("Java Backend Developer", "Delta Bank IT", "2019", "2025", ["Spring Boot REST APIs, Oracle SQL", "Docker and Kubernetes deployments", "Git, Jenkins pipelines"])],
  "B.Sc. Computer Science, Mansoura Univ., 2019", "Java, Spring, SQL, Docker, Kubernetes, Git"),
 ("Salma Gamal", "Data Scientist", [
   ("Data Scientist", "Insight Analytics", "2021", "2025", ["Python, pandas, scikit-learn models", "SQL pipelines, Docker for model serving", "Git-based experiments"])],
  "M.Sc. Data Science, AUC, 2021", "Python, SQL, Pandas, Scikit-learn, Docker, Git"),
 ("Tarek Nabil", "DevOps Engineer", [
   ("DevOps Engineer", "Cloud Nine", "2018", "2025", ["Kubernetes and Docker platform on AWS", "CI/CD with Jenkins; Linux administration", "Python automation scripts, Git"])],
  "B.Sc. Computer Science, Cairo Univ., 2018", "Docker, Kubernetes, AWS, Linux, Jenkins, Python, Git"),
 ("Dina Fathy", "Junior Backend Developer (fresh graduate)", [
   ("Backend Intern", "Orange Digital", "2025", "2025", ["FastAPI REST API for a booking app", "SQL database design; Docker; Git"])],
  "B.Sc. Computer Science, Capital Univ., 2025", "Python, FastAPI, SQL, Docker, Git"),
 ("Youssef Adel", "Junior Developer", [
   ("Junior Developer", "Web Studio", "2024", "2025", ["Python scripts and SQL reports", "Git for version control"])],
  "B.Sc. Computer Science, Benha Univ., 2024", "Python, SQL, Git"),
 ("Nour El-Din", "Data Analyst", [
   ("Data Analyst", "Retail Co", "2020", "2025", ["SQL dashboards and Python (pandas) analysis"])],
  "B.Com., Cairo Univ., 2020", "Python, SQL, Pandas"),
 ("Hana Mostafa", "Frontend Developer", [
   ("Frontend Developer", "Pixel House", "2020", "2025", ["React and TypeScript single-page apps", "Git workflow, design systems"])],
  "B.Sc. Computer Science, GUC, 2020", "JavaScript, TypeScript, React, Git"),
 ("Laila Hossam", "Marketing Manager", [
   ("Marketing Manager", "BrandWorks", "2018", "2025", ["Campaign planning and budget management", "Team leadership"])],
  "B.A. Business, AUC, 2018", "SEO, Copywriting, Analytics"),
]


def render(i, c):
    name, title, jobs, edu, skills = c
    ln = [f"{name} - {title}", f"Cairo, Egypt | {name.split()[0].lower()}.{name.split()[-1].lower()}@example.com", "", "Experience"]
    for role, co, s, e, bl in jobs:
        ln.append(f"{role}, {co} ({s}-{e})")
        ln += [f"- {b}" for b in bl]
    ln += ["", "Education", edu, "", f"Skills: {skills}"]
    return "\n".join(ln)


for i, c in enumerate(C, 1):
    (OUT / "cvs" / f"cv_{i:02d}_{c[0].split()[0].lower()}.txt").write_text(render(i, c), encoding="utf-8")

(OUT / "job.yaml").write_text(yaml.safe_dump(JOB, sort_keys=False), encoding="utf-8")
(OUT / "availability.json").write_text(json.dumps({
    "Sara Ahmed": ["Sun 10:00", "Mon 14:00"], "Karim Hassan": ["Sun 10:00", "Tue 11:00"],
    "Mona Ibrahim": ["Mon 10:00", "Wed 15:00"], "Mahmoud Reda": ["Thu 10:00"], "Ali Samir": ["Wed 11:00"],
}, indent=2), encoding="utf-8")
(OUT / "ground_truth.json").write_text(json.dumps({"expected_top3": ["Sara Ahmed", "Karim Hassan", "Mona Ibrahim"]}, indent=2), encoding="utf-8")
print(f"Wrote {len(C)} CVs to {OUT}")
