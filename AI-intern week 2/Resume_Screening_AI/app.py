import csv
import io
import re
import secrets
import time
from pathlib import Path
import pdfplumber
from flask import Flask, abort, make_response, render_template, request 
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from werkzeug.utils import secure_filename


MAX_FILE_BYTES = 10 * 1024 * 1024  #10MB
MAX_RESUMES = 20
RESULT_TTL_SECONDS = 30 * 60

SKILLS = {
    "python": ["python"],
    "sql": ["sql"],
    "machine learning" : ["machine learning", "ml"],
    "deep learning": ["deep learning"],
    "natural language processing": ["nlp", "natural language processing"],
    "data science": ["data science", "ds"],
    "data analysis": ["data analysis", "data analytics"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "tensorflow": ["tensorflow"],
    "keras": ["keras"],
    "pytorch": ["pytorch"],
    "jupyter": ["jupyter"],
    "git": ["git"],
    "docker": ["docker"],
    "aws": ["aws", "amazon web services"],
    "google cloud": ["google cloud", "gcp"],
    "linux": ["linux"],
    "html": ["html"],
    "css": ["css"],
    "javascript": ["javascript"],
    "generative ai": ["generative ai", "gpt", "gpt-3", "gpt-4", "chatgpt", "openai", "genai"],
    "llm": ["llm", "large language model"],
    "ai": ["ai", "artificial intelligence"],
    "statistics": ["statistics", "statistical"],
    "data visualization": ["data visualization", "data visualisation", "data viz"],
    "azure": ["azure"],
    "java": ["java"],
    "c++": ["c++"],
    "c#": ["c#"],
    "ruby": ["ruby"],
    "php": ["php"],
    "r": ["r"],
    "saas": ["saas"],
    "google cloud": ["google cloud", "gcp"],
    "mongodb": ["mongodb"],
    "postgresql": ["postgresql"],
    "redis": ["redis"],
    "rabbitmq": ["rabbitmq"],
    "kafka": ["kafka"],
    "elasticsearch": ["elasticsearch"],
    "flask": ["flask"],
    "django": ["django"],
    "fastapi": ["fastapi"],
    "react": ["react"],
    "excel": ["excel"],
    "communication": ["communication", "communication skills", "stakeholder management"],
}

SECTION_HEADINGS = {
    "skills":{
        "skills",
        "technical skills",
        "core competencies",
        "competencies",
    },
    "education": {
        "education",
        "education and training",
        "education and certifications",
        "academic background",
        "educational background",
        "qualifications",
    },
    "experience": {
        "experience",
        "work experience",
        "employment history",
        "professional experience",
        "employment",
        "work history",
        "job history",
        "professional background",
        "career history",
        "work",
        "employment record",
    },
}

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config["MAX_CONTENT_LENGTH"] = (
    MAX_FILE_BYTES * MAX_RESUMES + 128_000
)

RESULTS = {}

def parse_resume(filename, file_bytes):
    safe_name = secure_filename(filename or "") or "resume"
    extension = Path(safe_name).suffix.lower()
    
    if extension not in {".pdf", ".txt"}:
        raise ValueError(f"{safe_name} is not a PDF or TXT file.")
    
    if len(file_bytes) > MAX_FILE_BYTES:
        raise ValueError(f"{safe_name} is larger than the 10 MB file limit.")
    
    if extension == "pdf":
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                text = "\n".join(
                    page.extract_text() or "" for page in pdf.pages
                    )
        except Exception as error:
            raise ValueError(
                f"Could not read {safe_name}. Check that it is a valid PDF."
                ) from error
    else:
        text = file_bytes.decode("utf-8-sig", errors="replace")
        
    text = re.sub(r"[ \t]+", " ", text).strip()
    
    if len(text) < 30:
        raise ValueError(
            f"{safe_name} has too little readable text. "
            "Scanned PDFs need OCR before upload."
        )
        
    sections = extract_sections(text)
    
    return {
        "filename": safe_name,
        "name": find_candidate_name(text, safe_name),
        "text": text[:100_000],
        "skills_section" : sections["skills"],
        "education": sections["education"] or "No education section detected",
        "experience": (
            sections["experience"] or "No experience section detected"
        ),
    }
    

def extract_sections(text):
    sections = {
        "skills": [],
        "education": [],
        "experience": [],
    }
    active_section = None
    
    for line in text.splitlines():
        cleaned = line.strip()
        
        if not cleaned:
            continue
        
        heading = re.sub(r"[^a-z]", "", cleaned.lower()).strip()
        matched_section = None
        
        for section_name, headings in SECTION_HEADINGS.items():
            if heading in headings:
                matched_section = section_name
                break

        if matched_section:
            active_section = matched_section
        elif active_section and len(cleaned) < 500:
            sections[active_section].append(cleaned)
            
    return {
        name: "\n".join(lines)
        for name, lines in sections.items()
    }
    
    
def find_candidate_name(text, filename):
    for line in text.splitlines()[:8]:
        candidate = re.sub(r"\s+", " ", line).strip(" |•-\t")
        
        is_name = re.fullmatch(r"[A-Za-z][A-Za-z .'-]+", candidate)
        looks_like_contact = any(
            word in candidate.lower()
            for word in ("resume", "curriculum vitae", "email", "phone")
        )
        
        if is_name and 2 <= len(candidate) <= 70 and not looks_like_contact:
            return candidate

    return Path(filename).stem.replace("_", " ").replace("-"," ").title()

def find_skills(text):
    found = []
    text = text.lower()
    
    for skill, aliases in SKILLS.items():
        for alias in aliases:
            pattern = r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])"
        
            if re.search(pattern, text):
                found.append(skill)
                break

    return found


def score_resumes(job_description, uploaded_files):
    if not job_description.strip():
        raise ValueError("Enter a job description.")
    
    if len(job_description) > 12_000:
        raise ValueError("The job description must be 12,000 characters or less.")
    
    uploaded_files = [
        file for file in uploaded_files
        if file and file.filename
    ]
    
    if not uploaded_files:
        raise ValueError("Choose at least one PDF or TXT resume.")
    
    if len(uploaded_files) > MAX_RESUMES:
        raise ValueError(f"Upload no more than {MAX_RESUMES} resumes.")
    
    candidates = []
    
    for uploaded_file in uploaded_files:
        file_bytes = uploaded_file.read(MAX_FILE_BYTES + 1)
        candidate = parse_resume(uploaded_file.filename, file_bytes)
        candidates.append(candidate)

    documents = [job_description] + [
        candidate["text"] for candidate in candidates
    ]
    
    try:
        vectors = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=20_000,
        ).fit_transform(documents)
        
        text_similarities = cosine_similarity(
            vectors[0:1],
            vectors[1:]
        ).flatten()
    except ValueError:
        text_similarities = [0.0] * len(candidates)
        
    job_skills = find_skills(job_description)
    ranked_candidates = []
    
    for candidate, similarity in zip(candidates, text_similarities):
        resume_skills = find_skills(candidate["text"])
            
        matched_skills = [
            skill for skill in job_skills
            if skill in resume_skills
        ]
        extra_skills = [
            skill for skill in resume_skills
            if skill not in job_skills
        ]
        not_found_skills = [
            skill for skill in job_skills
            if skill not in resume_skills
        ]
        
        if job_skills:
            skill_coverage = len(matched_skills) / len(job_skills)
        else:
            skill_coverage = 0.0
            
        
        final_score = round(
            100 * (
                0.65 * float(similarity)
                + 0.35 * skill_coverage
            )
        )
        
        candidate.update({
            "score": final_score,
            "similarity": round(float(similarity) * 100),
            "skill_coverage": round(skill_coverage * 100),
            "matched_skills": matched_skills,
            "extra_skills": extra_skills,
            "not_found_skills": not_found_skills,
        })
        ranked_candidates.append(candidate)

    return sorted(
        ranked_candidates,
        key=lambda candidate: candidate["score"],
        reverse=True,
    )
    
    
@app.errorhandler(413)
def upload_too_large(_error):
    return render_template(
        "index.html",
        error="The combined upload is too large.",
        candidates=None,
    ), 413
    

@app.get("/")
def index():
    return render_template(
        "index.html", candidates=None
    )
    

@app.post("/screen")
def screen():
    job_description = request.form.get("job_description", "")
    uploaded_files = request.files.getlist("resumes")
    
    try:
        candidates = score_resumes(job_description, uploaded_files)
    except ValueError as error:
        return render_template(
            "index.html",
            error=str(error),
            candidates=None,
        ), 400

    token = secrets.token_urlsafe(24)
    now = time.monotonic()
    
    for old_token, (created_at, _) in list(RESULTS.items()):
        if now - created_at > RESULT_TTL_SECONDS:
            RESULTS.pop(old_token, None)
            
    RESULTS[token] = (now, candidates)
    
    return render_template(
        "index.html",
        candidates=candidates,
        report_token=token,
    )
    
    
@app.get("/report/token>.csv")
def download_report(token):
    result = RESULTS.get(token)
    
    if not result or time.monotonic() - result[0] > RESULT_TTL_SECONDS:
        RESULTS.pop(token, None)
        abort(404)
        
    output = io.StringIO(newline="")
    columns = [
        "rank",
        "name",
        "filename",
        "score",
        "similarity",
        "skill_coverage",
        "matched_skills",
        "extra_skills",
        "not_found_skills",
    ]

    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()

    for rank, candidate in enumerate(result[1], start=1):
        writer.writerow({
            "rank": rank,
            "name": candidate["name"],
            "filename": candidate["filename"],
            "score": candidate["score"],
            "similarity": candidate["similarity"],
            "skill_coverage": candidate["skill_coverage"],
            "matched_skills": ", ".join(candidate["matched_skills"]),
            "extra_skills": ", ".join(candidate["extra_skills"]),
            "not_found_skills": ", ".join(
                candidate["not_found_skills"]
            ),
        })

    response = make_response("\ufeff" + output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = (
        "attachment; filename=resume-screening-report.csv"
    )
    return response


if __name__ == "__main__":
    app.run(debug=False)