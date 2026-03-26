# PathPilot AI — Career Decision System

An AI-powered career decision-support web app built with Python Flask.

---

## 📁 Project Structure

```
pathpilot/
├── app.py                  ← Flask backend (all logic)
├── requirements.txt        ← Python dependencies
├── README.md               ← This file
└── templates/
    └── index.html          ← Frontend UI
```

---

## 🚀 How to Run

### 1. Install Python
Make sure Python 3.8+ is installed:
```bash
python --version
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv

# Activate it:
# macOS / Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
python app.py
```

### 5. Open in browser
Visit: **http://127.0.0.1:5000**

---

## 🧠 How It Works

| Step | What Happens |
|------|-------------|
| 1 | User uploads a PDF resume |
| 2 | PyPDF2 extracts text; keywords matched to detect skills |
| 3 | Target role → dynamically generates required skills |
| 4 | Skill gap calculated → Feasibility assessed (Low / Medium / High) |
| 5 | Decision flow: alternatives shown OR extended roadmap if user commits |
| 6 | Weekly + daily roadmap generated for all missing skills |

---

## ⚙️ Configuration
- Max upload size: 10MB (editable in `app.py`)
- No database required — fully stateless per request
- No external AI API needed — simulated intelligence built-in

---

## 🛠 Dependencies
- **Flask** — web framework
- **PyPDF2** — PDF text extraction
