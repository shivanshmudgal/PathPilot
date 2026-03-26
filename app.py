from flask import Flask, render_template, request, jsonify
import PyPDF2
import io

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max

# ─────────────────────────────────────────
# SKILL KEYWORDS FOR RESUME PARSING
# ─────────────────────────────────────────

SKILL_KEYWORDS = [
    "python", "machine learning", "sql", "html", "css", "javascript",
    "react", "testing", "apis", "nlp", "java", "c++", "docker",
    "kubernetes", "aws", "azure", "gcp", "tensorflow", "pytorch",
    "pandas", "numpy", "git", "linux", "node.js", "flask", "django",
    "tableau", "power bi", "excel", "mongodb", "postgresql", "rest",
    "graphql", "ci/cd", "agile", "scrum", "data analysis", "statistics",
    "deep learning", "computer vision", "spark", "hadoop", "selenium",
    "typescript", "vue", "angular", "figma", "ux", "ui", "bash",
    "r programming", "scala", "airflow", "dbt", "redis", "kafka",
    "fastapi", "spring boot", "jest", "cypress", "terraform", "ansible",
    "communication", "leadership", "problem solving", "stakeholder management",
    "product management", "roadmap", "a/b testing", "data storytelling"
]

# ─────────────────────────────────────────
# REALISTIC ROLE → SKILLS MAP
# Each role has required skills with a weight (1=nice-to-have, 2=important, 3=must-have)
# ─────────────────────────────────────────

ROLE_SKILLS_MAP = {
    # Data roles
    "data analyst": {
        "SQL": 3, "Excel": 3, "Python": 2, "Tableau": 2, "Power BI": 2,
        "Statistics": 3, "Data Visualization": 3, "Data Cleaning": 3,
        "Business Communication": 2, "Git": 1
    },
    "data scientist": {
        "Python": 3, "Machine Learning": 3, "SQL": 3, "Statistics": 3,
        "Pandas": 3, "NumPy": 2, "Scikit-learn": 3, "Data Visualization": 2,
        "Deep Learning": 2, "Git": 2, "Feature Engineering": 3, "A/B Testing": 2
    },
    "machine learning engineer": {
        "Python": 3, "Machine Learning": 3, "Deep Learning": 3,
        "TensorFlow": 2, "PyTorch": 2, "MLOps": 3, "Docker": 2,
        "APIs": 2, "SQL": 2, "Cloud (AWS/GCP/Azure)": 2, "Git": 3,
        "Model Deployment": 3, "Statistics": 2
    },
    "data engineer": {
        "Python": 3, "SQL": 3, "Spark": 3, "Airflow": 2, "Kafka": 2,
        "AWS/Azure/GCP": 3, "Docker": 2, "PostgreSQL": 2, "MongoDB": 1,
        "ETL Pipelines": 3, "dbt": 2, "Git": 3, "Linux": 2
    },
    # Engineering roles
    "frontend developer": {
        "HTML": 3, "CSS": 3, "JavaScript": 3, "React": 3, "TypeScript": 2,
        "Git": 3, "REST APIs": 2, "Responsive Design": 3,
        "Testing (Jest/Cypress)": 2, "Figma/UI basics": 1
    },
    "backend developer": {
        "Python or Java or Node.js": 3, "REST APIs": 3, "SQL": 3,
        "PostgreSQL": 2, "MongoDB": 2, "Docker": 2, "Git": 3,
        "System Design": 2, "Authentication/Security": 2, "Linux": 2
    },
    "full stack developer": {
        "HTML": 3, "CSS": 3, "JavaScript": 3, "React": 2, "Node.js": 2,
        "SQL": 2, "REST APIs": 3, "Git": 3, "Docker": 2,
        "System Design": 2, "PostgreSQL": 2
    },
    "devops engineer": {
        "Linux": 3, "Docker": 3, "Kubernetes": 3, "CI/CD": 3,
        "Terraform": 2, "Ansible": 2, "AWS/Azure/GCP": 3,
        "Bash Scripting": 3, "Git": 3, "Monitoring (Grafana/Prometheus)": 2,
        "Networking basics": 2
    },
    "cloud engineer": {
        "AWS/Azure/GCP": 3, "Terraform": 3, "Docker": 2, "Kubernetes": 2,
        "Linux": 3, "Networking": 3, "Security basics": 2,
        "CI/CD": 2, "Python or Bash": 2, "Git": 2
    },
    # QA / Testing
    "qa engineer": {
        "Manual Testing": 3, "Test Case Design": 3, "Selenium": 2,
        "Python or Java": 2, "API Testing": 2, "SQL": 2,
        "Bug Reporting": 3, "Agile/Scrum": 2, "Git": 2, "Cypress": 1
    },
    "qa automation engineer": {
        "Selenium": 3, "Python or Java": 3, "Cypress": 2, "Jest": 2,
        "API Testing": 3, "CI/CD": 2, "SQL": 2, "Git": 3,
        "Test Frameworks": 3, "Bug Reporting": 3
    },
    # Product / Management
    "product manager": {
        "Product Roadmapping": 3, "Stakeholder Management": 3,
        "Agile/Scrum": 3, "Data Analysis": 2, "SQL basics": 2,
        "User Research": 2, "A/B Testing": 2, "Communication": 3,
        "Figma basics": 1, "Business Strategy": 2
    },
    "business analyst": {
        "SQL": 2, "Excel": 3, "Requirements Gathering": 3,
        "Stakeholder Management": 3, "Data Analysis": 2,
        "Process Mapping": 2, "Communication": 3, "Agile": 2,
        "Tableau or Power BI": 1, "Documentation": 2
    },
    # Design
    "ux designer": {
        "Figma": 3, "User Research": 3, "Wireframing": 3,
        "Prototyping": 3, "Usability Testing": 3, "HTML/CSS basics": 1,
        "Design Systems": 2, "Information Architecture": 2, "Communication": 2
    },
    # Cybersecurity
    "cybersecurity analyst": {
        "Networking": 3, "Linux": 3, "Security Tools (SIEM/IDS)": 3,
        "Python or Bash": 2, "Vulnerability Assessment": 3,
        "Incident Response": 2, "SQL": 1, "Cryptography basics": 2,
        "Cloud Security": 2, "Compliance (GDPR/ISO)": 1
    },
}

# Alias map to handle variations in how users type roles
ROLE_ALIASES = {
    "ml engineer": "machine learning engineer",
    "ai engineer": "machine learning engineer",
    "data science": "data scientist",
    "front end developer": "frontend developer",
    "front-end developer": "frontend developer",
    "back end developer": "backend developer",
    "back-end developer": "backend developer",
    "fullstack developer": "full stack developer",
    "full-stack developer": "full stack developer",
    "sde": "backend developer",
    "software engineer": "backend developer",
    "software developer": "backend developer",
    "dev ops": "devops engineer",
    "devops": "devops engineer",
    "qa": "qa engineer",
    "quality assurance": "qa engineer",
    "automation tester": "qa automation engineer",
    "pm": "product manager",
    "ba": "business analyst",
    "ux": "ux designer",
    "ui designer": "ux designer",
    "ui/ux designer": "ux designer",
    "security analyst": "cybersecurity analyst",
    "cloud architect": "cloud engineer",
    "de": "data engineer",
    "analyst": "data analyst",
    "ds": "data scientist",
}

# ─────────────────────────────────────────
# ALTERNATIVE ROLES POOL
# ─────────────────────────────────────────

ALTERNATIVE_ROLES = list(ROLE_SKILLS_MAP.keys())

# ─────────────────────────────────────────
# TIME ESTIMATES PER SKILL (months to learn from scratch)
# ─────────────────────────────────────────

SKILL_TIME_MAP = {
    # Easy / quick wins
    "Excel": 0.5, "Git": 0.5, "HTML": 0.5, "CSS": 0.75, "Bash Scripting": 0.5,
    "Bug Reporting": 0.5, "Manual Testing": 0.75, "Test Case Design": 0.75,
    "Documentation": 0.5, "Communication": 0.25, "Agile/Scrum": 0.5,
    # Moderate
    "SQL": 1.0, "Python": 1.5, "JavaScript": 1.5, "REST APIs": 1.0,
    "Linux": 1.0, "Docker": 1.0, "Tableau": 1.0, "Power BI": 1.0,
    "Data Visualization": 1.0, "Data Cleaning": 0.75, "Statistics": 1.5,
    "Responsive Design": 0.75, "API Testing": 0.75, "Agile": 0.5,
    "A/B Testing": 0.75, "User Research": 1.0, "Wireframing": 0.75,
    "Prototyping": 1.0, "Networking": 1.5, "Figma": 0.75,
    "Feature Engineering": 1.0, "Business Communication": 0.5,
    # Advanced
    "React": 2.0, "Node.js": 1.5, "TypeScript": 1.0, "PostgreSQL": 1.0,
    "MongoDB": 0.75, "AWS/Azure/GCP": 2.0, "Kubernetes": 2.0,
    "Terraform": 1.5, "CI/CD": 1.5, "Spark": 2.0, "Kafka": 1.5,
    "Airflow": 1.5, "Machine Learning": 3.0, "Deep Learning": 3.0,
    "TensorFlow": 2.0, "PyTorch": 2.0, "Scikit-learn": 1.5,
    "Model Deployment": 2.0, "MLOps": 2.5, "Pandas": 1.0, "NumPy": 0.75,
    "System Design": 2.5, "Selenium": 1.0, "Cypress": 1.0,
    "ETL Pipelines": 2.0, "dbt": 1.0, "Redis": 0.75,
    "Vulnerability Assessment": 2.0, "Incident Response": 1.5,
    "Security Tools (SIEM/IDS)": 2.0, "Cryptography basics": 1.0,
    "Data Storytelling": 1.0, "Product Roadmapping": 1.0,
    "Stakeholder Management": 1.0, "Requirements Gathering": 1.0,
    "Process Mapping": 0.75, "Networking basics": 1.0,
    "Authentication/Security": 1.0, "Networking": 1.5,
    "Cloud (AWS/GCP/Azure)": 2.0, "FastAPI": 0.75, "Flask": 0.75,
    "Spring Boot": 1.5, "NLP": 2.0, "Computer Vision": 2.5,
    "Usability Testing": 0.75, "Design Systems": 1.0, "Information Architecture": 1.0,
    "Cloud Security": 1.5, "Compliance (GDPR/ISO)": 0.75, "Testing (Jest/Cypress)": 1.0,
    "Figma/UI basics": 0.5, "Figma basics": 0.5, "SQL basics": 0.75,
    "HTML/CSS basics": 0.5, "Python or Java": 1.5, "Python or Java or Node.js": 1.5,
    "Python or Bash": 1.0, "Business Strategy": 1.5,
}

DEFAULT_SKILL_TIME = 1.0  # fallback if skill not in map

# ─────────────────────────────────────────
# PDF PARSING
# ─────────────────────────────────────────

def extract_text_from_pdf(file_bytes):
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.lower()
    except Exception:
        return ""

def extract_skills(text):
    found = []
    for skill in SKILL_KEYWORDS:
        if skill.lower() in text:
            found.append(skill.title())
    return list(set(found))

# ─────────────────────────────────────────
# ROLE RESOLUTION
# ─────────────────────────────────────────

def resolve_role(role_input):
    """Match user input to a known role, or generate a dynamic fallback."""
    normalized = role_input.strip().lower()
    # Direct match
    if normalized in ROLE_SKILLS_MAP:
        return normalized, ROLE_SKILLS_MAP[normalized]
    # Alias match
    if normalized in ROLE_ALIASES:
        canonical = ROLE_ALIASES[normalized]
        return canonical, ROLE_SKILLS_MAP[canonical]
    # Partial match
    for key in ROLE_SKILLS_MAP:
        if key in normalized or normalized in key:
            return key, ROLE_SKILLS_MAP[key]
    # Dynamic fallback for unknown roles
    return role_input, generate_dynamic_skills(role_input)

def generate_dynamic_skills(role):
    """Fallback skill generator for roles not in the map."""
    role_lower = role.lower()
    skills = {
        f"{role} fundamentals": 3,
        f"{role} tools & ecosystem": 2,
        "Problem Solving": 3,
        "Communication": 2,
        "Git": 2,
        "Documentation": 1,
    }
    if any(k in role_lower for k in ["data", "analyst", "science"]):
        skills.update({"SQL": 3, "Python": 2, "Statistics": 2, "Data Visualization": 2})
    if any(k in role_lower for k in ["dev", "engineer", "code", "software"]):
        skills.update({"Python": 2, "Git": 3, "REST APIs": 2, "SQL": 2})
    if any(k in role_lower for k in ["cloud", "devops", "infra"]):
        skills.update({"Linux": 2, "Docker": 2, "CI/CD": 2, "AWS/Azure/GCP": 2})
    return skills

# ─────────────────────────────────────────
# GAP & FEASIBILITY
# ─────────────────────────────────────────

def calculate_gap(detected_skills, required_skills_map):
    """
    Compare detected skills against required skills.
    Returns list of missing skills (only weight >= 2 are considered critical).
    """
    detected_lower = [s.lower() for s in detected_skills]
    missing = []
    for skill, weight in required_skills_map.items():
        skill_lower = skill.lower()
        matched = any(
            skill_lower in d or d in skill_lower or
            skill_lower.split()[0] in d  # partial match on first word
            for d in detected_lower
        )
        if not matched and weight >= 2:
            missing.append(skill)
    return missing

def estimate_time(missing_skills):
    """Calculate realistic learning time based on known skill durations."""
    total = 0.0
    for skill in missing_skills:
        # Try exact match, then partial
        time = SKILL_TIME_MAP.get(skill)
        if time is None:
            for key in SKILL_TIME_MAP:
                if key.lower() in skill.lower() or skill.lower() in key.lower():
                    time = SKILL_TIME_MAP[key]
                    break
        total += time if time else DEFAULT_SKILL_TIME
    # Add 20% buffer for revision and job prep
    return round(total * 1.2, 1)

def assess_feasibility(missing_skills, available_months):
    gap = len(missing_skills)
    months_needed = estimate_time(missing_skills)

    if gap == 0:
        status, level = "Ready to Apply", "low"
    elif gap <= 3:
        status, level = "Feasible", "low"
    elif gap <= 6:
        status, level = "Needs Work", "medium"
    else:
        status, level = "Significant Gap", "high"

    within_time = months_needed <= available_months

    return {
        "status": status,
        "level": level,
        "months_needed": months_needed,
        "within_time": within_time,
        "gap_count": gap
    }

# ─────────────────────────────────────────
# ALTERNATIVES
# ─────────────────────────────────────────

def suggest_alternatives(detected_skills, exclude_role=""):
    scores = []
    for role_name, reqs in ROLE_SKILLS_MAP.items():
        if role_name.lower() == exclude_role.lower():
            continue
        missing = calculate_gap(detected_skills, reqs)
        total_required = len([s for s, w in reqs.items() if w >= 2])
        match_pct = round((1 - len(missing) / max(total_required, 1)) * 100)
        match_pct = max(0, min(100, match_pct))
        scores.append({
            "role": role_name.title(),
            "missing_count": len(missing),
            "missing_skills": missing[:4],  # top 4 gaps
            "match_pct": match_pct
        })
    scores.sort(key=lambda x: (-x["match_pct"], x["missing_count"]))
    return scores[:4]

# ─────────────────────────────────────────
# ROADMAP
# ─────────────────────────────────────────

SKILL_RESOURCES = {
    "Python": "freeCodeCamp Python course, Automate the Boring Stuff (free online)",
    "SQL": "Mode SQL Tutorial, SQLZoo, LeetCode SQL problems",
    "Machine Learning": "Andrew Ng's ML Specialization (Coursera), fast.ai",
    "Deep Learning": "fast.ai Practical Deep Learning, DeepLearning.AI specialization",
    "React": "React official docs, Scrimba React course",
    "Docker": "Docker's official 'Get Started' guide, TechWorld with Nana (YouTube)",
    "Kubernetes": "Kubernetes official docs, KodeKloud",
    "AWS/Azure/GCP": "AWS Free Tier hands-on, A Cloud Guru, official docs",
    "Git": "Pro Git book (free), GitHub Skills",
    "Statistics": "Khan Academy Statistics, StatQuest (YouTube)",
    "Tableau": "Tableau Public free training videos",
    "Figma": "Figma official tutorials, Design with Figma (YouTube)",
    "Selenium": "Selenium official docs, Test Automation University",
}

def get_resource(skill):
    for key in SKILL_RESOURCES:
        if key.lower() in skill.lower() or skill.lower() in key.lower():
            return SKILL_RESOURCES[key]
    return "Search for free courses on YouTube, Coursera, or official documentation"

def generate_roadmap(missing_skills, months_needed):
    weeks = max(4, int(months_needed * 4))
    roadmap = []

    for i, skill in enumerate(missing_skills):
        week_num = i + 1
        resource = get_resource(skill)
        roadmap.append({
            "week": week_num,
            "skill": skill,
            "resource": resource,
            "days": [
                {"day": "Day 1–2", "task": f"Study the core concepts of {skill}. Use: {resource.split(',')[0]}."},
                {"day": "Day 3–4", "task": f"Complete hands-on exercises and follow-along tutorials for {skill}."},
                {"day": "Day 5–6", "task": f"Build a small project or solve practice problems using {skill}."},
                {"day": "Day 7",   "task": f"Review what you learned, push your work to GitHub, and note weak spots."},
            ]
        })
        if week_num >= weeks:
            break

    if len(roadmap) < weeks:
        for w in range(len(roadmap) + 1, min(weeks + 1, len(roadmap) + 4)):
            roadmap.append({
                "week": w,
                "skill": "Portfolio & Interview Prep",
                "resource": "LeetCode, Pramp (mock interviews), LinkedIn profile update",
                "days": [
                    {"day": "Day 1–2", "task": "Revisit weak areas and fill any knowledge gaps."},
                    {"day": "Day 3–4", "task": "Build a capstone project that combines your top 2–3 skills."},
                    {"day": "Day 5–6", "task": "Write a README, polish your GitHub, update LinkedIn."},
                    {"day": "Day 7",   "task": "Do a mock interview (Pramp or peer practice) and note feedback."},
                ]
            })
    return roadmap[:weeks]

# ─────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        file = request.files.get("resume")
        role_input = request.form.get("role", "").strip()
        months_str = request.form.get("months", "6")
        force_continue = request.form.get("force_continue") == "true"

        if not file or not role_input:
            return jsonify({"error": "Please upload a resume and enter a target role."}), 400

        try:
            available_months = float(months_str)
        except ValueError:
            available_months = 6

        # 1. Parse resume
        pdf_bytes = file.read()
        resume_text = extract_text_from_pdf(pdf_bytes)
        detected_skills = extract_skills(resume_text)
        if not detected_skills:
            detected_skills = ["Basic Computer Skills", "Communication"]

        # 2. Resolve role → required skills
        resolved_role, required_skills_map = resolve_role(role_input)

        # 3. Gap analysis
        missing_skills = calculate_gap(detected_skills, required_skills_map)
        feasibility = assess_feasibility(missing_skills, available_months)

        # 4. Alternatives (exclude current role)
        alternatives = suggest_alternatives(detected_skills, exclude_role=resolved_role)

        # 5. Roadmap
        roadmap = []
        if feasibility["level"] in ("low", "medium") or force_continue:
            roadmap = generate_roadmap(missing_skills, feasibility["months_needed"])

        # 6. Decision
        decision = None
        if feasibility["level"] == "high":
            decision = "continue" if force_continue else "switch"

        return jsonify({
            "detected_skills": detected_skills,
            "required_skills": list(required_skills_map.keys()),
            "missing_skills": missing_skills,
            "feasibility": feasibility,
            "alternatives": alternatives,
            "roadmap": roadmap,
            "decision": decision,
            "role": resolved_role.title(),
            "role_input": role_input,
            "available_months": available_months,
            "force_continue": force_continue
        })

    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
