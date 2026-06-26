# AI Resume Analyzer with ATS Score

An advanced AI-powered Resume Analyzer and Applicant Tracking System (ATS) matching tool built with Python, Streamlit, and NLP techniques. This project evaluates candidate resumes against job descriptions, calculates detailed ATS compatibility metrics, performs structured section audit, identifies missing keywords/skills, and offers actionable optimization tips.

---

## 🌟 Features

1. **Secure User Authentication**: Encrypted credentials stored locally using SQLite database and hashed with `bcrypt`.
2. **Multi-Format Text Extraction**: Full paragraph and table parsing for both PDF (`pdfplumber`) and DOCX (`python-docx`) formats.
3. **Advanced Semantic Analysis**: Implements TF-IDF Natural Language Processing and Cosine Similarity to compare semantic descriptions.
4. **Keyword & Skills Audit**: Compares resume text against job specifications using precise, boundary-checked Regex matches for over 60+ core languages, clouds, databases, frameworks, and DevOps tools.
5. **Structural Section Verification**: Checks for standard sections (Education, Skills, Experience, Projects, Certifications) to ensure format compliance.
6. **Detailed Analytics Dashboard**: Styled metrics cards, Plotly Gauge charts, and breakdown bars showing match attributes.
7. **Actionable Suggestions**: Recommends missing sections, lists top missing skills, and suggests word count formatting.
8. **Exportable PDF Reports**: Auto-generates clean, double-pass compiled ReportLab PDF summaries with color-coded badges, matching tables, and checklist bullet points.
9. **Historical Log Tracking**: Browse past evaluations and reload them into the active dashboard.

---

## 🛠️ Tech Stack

- **Frontend / UI**: Streamlit (Python) + Custom Glassmorphism CSS injection
- **Data Visualizations**: Plotly Graph Objects & Pandas DataFrames
- **Natural Language Processing**: Scikit-Learn TF-IDF / Custom Vectorizer & RegEx Tokenization
- **Parsing Libraries**: pdfplumber, python-docx
- **Database Engine**: SQLite3
- **Security**: bcrypt
- **Reporting Engine**: ReportLab (SimpleDocTemplate Flowables)

---

## 📁 Directory Structure

```
resume_analyzer/
├── app.py                  # Main Streamlit router, state management, and page interfaces
├── database.py             # SQLite3 schema definition, credentials hashing, and history logging
├── requirements.txt        # Python dependency manifest
├── README.md               # Setup and deployment documentation
├── create_samples.py       # Programmatic helper to generate sample resumes and JDs
├── test_analyzer.py        # Complete automated unit testing suite
├── uploaded_resumes/       # Directory containing uploaded raw resumes
├── reports/                # Cache for generated PDF evaluation reports
├── samples/                # Directory containing generated sample PDF/DOCX resumes and JDs
└── assets/
    └── custom.css          # Injected glassmorphism style rules and typography configuration
```

---

## 💻 Installation and Setup

### Prerequisites
- Python 3.8 to 3.13
- Git

### Step-by-Step Guide

1. **Clone the Repository** (or navigate to the workspace directory):
   ```bash
   cd "C:\Users\Rajesh\Pictures\Ai Resume"
   ```

2. **Set Up a Virtual Environment** (Recommended):
   ```bash
   python -m venv venv
   # Activate on Windows:
   venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: If `scikit-learn` compilation takes too long or fails due to missing C++ compilers on Windows, the application will automatically fall back to our pure Python TF-IDF Vectorizer and Cosine Similarity implementation.*

4. **Generate Demo Samples**:
   Generate mock PDF/DOCX resumes and Job Descriptions to test immediately:
   ```bash
   python create_samples.py
   ```

5. **Run the Verification Tests**:
   Run unit tests to ensure that parsing, text analysis, and DB states are passing:
   ```bash
   python test_analyzer.py
   ```

6. **Launch the Application Locally**:
   Start the Streamlit development server:
   ```bash
   streamlit run app.py
   ```
   The application will automatically load in your browser at `http://localhost:8501`.

---

## 🚀 Deployment Instructions

### 1. Streamlit Cloud (Recommended & Free)
1. Commit and push the project files to a public GitHub repository.
2. Log in to [Streamlit Share](https://share.streamlit.io/).
3. Click **New App**, select your Repository, Branch, and choose `app.py` as the Main File Path.
4. Click **Deploy**. Streamlit Cloud will parse `requirements.txt` and set up the server environment in minutes.

### 2. Render
1. Create a `render.yaml` or set up a Web Service pointing to your GitHub repository.
2. Select **Python** runtime environment.
3. Configure the following build and start commands:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
4. Deploy the service.

### 3. Railway
1. Sign up on [Railway.app](https://railway.app/) and create a new project.
2. Link your GitHub repository.
3. Railway automatically detects Python projects. Go to your service variables and add:
   - Variable `PORT` (Railway binds this automatically).
4. Under settings, configure the start command:
   - `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
5. Deploy.
