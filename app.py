import streamlit as st
import os
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

# Import project modules
import database as db
import utils.parser as parser
import utils.analyzer as analyzer
import utils.reporter as reporter

# Set page config
st.set_page_config(
    page_title="AI Resume Analyzer with ATS Score",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants & Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_resumes")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
CSS_PATH = os.path.join(BASE_DIR, "assets", "custom.css")

# Ensure necessary directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# Load and inject custom CSS
if os.path.exists(CSS_PATH):
    with open(CSS_PATH, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
else:
    st.warning("Custom CSS file not found. Falling back to default layout.")

# Initialize session state for user session
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "current_analysis" not in st.session_state:
    st.session_state.current_analysis = None

# --- Page Render Helpers ---

def render_login():
    """Render Login Page."""
    st.markdown("<h1 class='header-title' style='margin-top: 3rem; margin-bottom: 2rem;'>Resume Analyzer</h1>", unsafe_allow_html=True)
    
    # Decrease login entity size and center it
    _, col, _ = st.columns([1.2, 1.6, 1.2])
    with col:
        with st.container(border=True):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Log In", use_container_width=True):
                    if username and password:
                        user = db.authenticate_user(username, password)
                        if user:
                            st.session_state.logged_in = True
                            st.session_state.user_info = user
                            st.success(f"Successfully logged in as {username}!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password.")
                    else:
                        st.warning("Please fill in all fields.")
            with col2:
                if st.button("Go to Register", use_container_width=True):
                    st.session_state.auth_action = "register"
                    st.rerun()

def render_register():
    """Render Registration Page."""
    st.markdown("<h1 class='header-title' style='margin-top: 3rem; margin-bottom: 2rem;'>Resume Analyzer</h1>", unsafe_allow_html=True)
    
    # Decrease registration entity size and center it
    _, col, _ = st.columns([1.2, 1.6, 1.2])
    with col:
        with st.container(border=True):
            new_username = st.text_input("Username", key="reg_username")
            new_email = st.text_input("Email Address", key="reg_email")
            new_password = st.text_input("Password", type="password", key="reg_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
            
            st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Sign Up", use_container_width=True):
                    if new_username and new_email and new_password and confirm_password:
                        if new_password != confirm_password:
                            st.error("Passwords do not match.")
                        elif "@" not in new_email or "." not in new_email:
                            st.error("Invalid email address format.")
                        else:
                            registered = db.register_user(new_username, new_email, new_password)
                            if registered:
                                st.success("Registration successful! You can now log in.")
                                st.session_state.auth_action = "login"
                                st.rerun()
                            else:
                                st.error("Username already exists. Choose another.")
                    else:
                        st.warning("Please fill in all fields.")
            with col2:
                if st.button("Go to Login", use_container_width=True):
                    st.session_state.auth_action = "login"
                    st.rerun()


# --- Gauge & Chart Helpers ---

def get_gauge_chart(score):
    """Generate a high-fidelity Plotly gauge chart for the ATS score."""
    # Custom color based on score range
    if score >= 80:
        bar_color = "#10B981"  # Emerald
    elif score >= 60:
        bar_color = "#F59E0B"  # Amber
    else:
        bar_color = "#EF4444"  # Red
        
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "ATS Fit Score", 'font': {'size': 20, 'color': '#FFFFFF', 'family': 'Outfit'}},
        number={'font': {'size': 48, 'color': '#FFFFFF', 'family': 'Outfit'}, 'suffix': "%"},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#94A3B8"},
            'bar': {'color': bar_color},
            'bgcolor': "rgba(255, 255, 255, 0.05)",
            'borderwidth': 2,
            'bordercolor': "rgba(255, 255, 255, 0.1)",
            'steps': [
                {'range': [0, 50], 'color': 'rgba(239, 68, 68, 0.1)'},
                {'range': [50, 75], 'color': 'rgba(245, 158, 11, 0.1)'},
                {'range': [75, 100], 'color': 'rgba(16, 185, 129, 0.1)'}
            ],
        }
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': '#FFFFFF', 'family': 'Outfit'},
        height=280,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

def get_subscore_chart(scores):
    """Generate a horizontal bar chart breaking down the sub-scores."""
    categories = ["Skill Match", "Semantic Match", "Section Match"]
    vals = [scores["skill_match_score"], scores["semantic_score"], scores["section_score"]]
    
    fig = go.Figure(go.Bar(
        x=vals,
        y=categories,
        orientation='h',
        marker=dict(
            color=['#8B5CF6', '#3B82F6', '#10B981'],
            line=dict(color='rgba(255, 255, 255, 0.15)', width=1)
        ),
        text=[f"{v}%" for v in vals],
        textposition='auto',
        textfont=dict(color='#FFFFFF', size=11, family='Outfit')
    ))
    
    fig.update_layout(
        title={'text': "Score Breakdown", 'font': {'size': 18, 'color': '#FFFFFF', 'family': 'Outfit'}},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            range=[0, 100],
            showgrid=True,
            gridcolor='rgba(255, 255, 255, 0.05)',
            tickfont=dict(color='#94A3B8')
        ),
        yaxis=dict(
            tickfont=dict(color='#FFFFFF', size=12)
        ),
        height=200,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

# --- Main App Routing ---

def main():
    # Render Navigation/Sidebar if logged in
    if not st.session_state.logged_in:
        # Toggle authentication sub-state
        if "auth_action" not in st.session_state:
            st.session_state.auth_action = "login"
            
        if st.session_state.auth_action == "login":
            render_login()
        else:
            render_register()
    else:
        # Sidebar Setup
        st.sidebar.markdown(f"<div style='text-align: center; padding: 1rem;'><h3 style='color:#A855F7; margin-bottom:0;'>🤖 ATS Analyzer</h3><p style='color:#64748B; font-size:0.85rem;'>Hello, {st.session_state.user_info['username']}</p></div>", unsafe_allow_html=True)
        
        menu = ["Resume Analyzer", "Dashboard", "Evaluation History", "About & Help"]
        choice = st.sidebar.radio("Navigation Menu", menu)
        
        # Log out button at bottom of sidebar
        st.sidebar.markdown("<br><hr style='border-color: rgba(255,255,255,0.05);'><br>", unsafe_allow_html=True)
        if st.sidebar.button("Sign Out", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_info = None
            st.session_state.current_analysis = None
            st.rerun()

        # Route Pages
        if choice == "Resume Analyzer":
            render_analyzer_page()
        elif choice == "Dashboard":
            render_dashboard_page()
        elif choice == "Evaluation History":
            render_history_page()
        elif choice == "About & Help":
            render_about_page()

# --- Page Render Implementations ---

def render_analyzer_page():
    st.markdown("<h1 class='header-title'>AI Resume & ATS Analyzer</h1>", unsafe_allow_html=True)
    st.markdown("<p class='header-subtitle'>Upload your resume and paste the job description to calculate your matching score</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Left Capsule: Resume Match Score
        score_text = "--/100"
        if st.session_state.current_analysis:
            score_text = f"{st.session_state.current_analysis['ats_score']:.1f}/100"
        st.markdown(f"<div class='glass-card' style='text-align: center; padding: 0.8rem; margin-bottom: 1rem;'><span style='color:#94A3B8; font-size:0.85rem; font-weight:600; text-transform:uppercase; letter-spacing:0.05em;'>Resume Match Score (predicted/100)</span><h3 style='margin:0.25rem 0 0 0; color:#10B981; font-weight:800; font-size:1.6rem;'>{score_text}</h3></div>", unsafe_allow_html=True)
        
        with st.container(border=True):
            st.subheader("1. Upload Resume")
            uploaded_file = st.file_uploader("Upload PDF or Word (DOCX) formats", type=["pdf", "docx"])
            
            extracted_text = ""
            filename = ""
            
            if uploaded_file is not None:
                filename = uploaded_file.name
                # Save temporary file
                temp_path = os.path.join(UPLOAD_DIR, filename)
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                    
                # Extract text
                if filename.endswith(".pdf"):
                    extracted_text = parser.extract_text_from_pdf(temp_path)
                elif filename.endswith(".docx"):
                    extracted_text = parser.extract_text_from_docx(temp_path)
                    
                if extracted_text:
                    st.success(f"File '{filename}' successfully uploaded and parsed.")
                    with st.expander("Preview Extracted Text"):
                        st.text(extracted_text[:1000] + "\n... [truncated]")
                else:
                    st.error("Could not extract text from file. Please ensure it contains readable text.")
        
    with col2:
        # Right Capsule: Job Role
        job_role_text = "--"
        if st.session_state.current_analysis:
            job_role_text = st.session_state.current_analysis['job_title']
        st.markdown(f"<div class='glass-card' style='text-align: center; padding: 0.8rem; margin-bottom: 1rem;'><span style='color:#94A3B8; font-size:0.85rem; font-weight:600; text-transform:uppercase; letter-spacing:0.05em;'>Job Role</span><h3 style='margin:0.25rem 0 0 0; color:#3B82F6; font-weight:800; font-size:1.6rem;'>{job_role_text}</h3></div>", unsafe_allow_html=True)
        
        with st.container(border=True):
            st.subheader("2. Job Specification")
            job_title = st.text_input("Job Profile / Title", placeholder="e.g. AI Engineer, Fullstack Developer")
            job_desc = st.text_area("Paste Job Description", placeholder="Enter the key duties, required skills, and competencies here...", height=200)
        
    # Analyze Trigger Button
    if st.button("Evaluate ATS Compatibility", use_container_width=True):
        if not extracted_text:
            st.warning("Please upload a valid resume file first.")
        elif not job_desc.strip():
            st.warning("Please provide a job description for comparison.")
        elif not job_title.strip():
            st.warning("Please specify a target Job Profile / Title.")
        else:
            with st.spinner("Analyzing semantics, matching skills, and computing scores..."):
                # Run evaluation engine
                res = analyzer.analyze_resume(extracted_text, job_desc)
                
                # Save resume record to SQLite
                temp_path = os.path.join(UPLOAD_DIR, filename)
                resume_id = db.save_resume(
                    st.session_state.user_info["id"],
                    filename,
                    temp_path,
                    extracted_text
                )
                
                # Save analysis to database
                db.save_analysis(
                    st.session_state.user_info["id"],
                    resume_id,
                    job_title,
                    job_desc,
                    res["ats_score"],
                    res["skill_match_score"],
                    res["matching_skills"],
                    res["missing_skills"],
                    res["suggestions"]
                )
                
                # Prepare current report details
                res["filename"] = filename
                res["job_title"] = job_title
                res["job_description"] = job_desc
                st.session_state.current_analysis = res
                
                st.success("Analysis complete! Redirecting to Dashboard...")
                st.rerun()

def render_dashboard_page():
    analysis = st.session_state.current_analysis
    
    if not analysis:
        st.markdown("<h1 class='header-title'>Result Dashboard</h1>", unsafe_allow_html=True)
        st.info("No active evaluation. Please go to 'Resume Analyzer' in the menu to evaluate your resume first.")
        return
        
    st.markdown(f"<h1 class='header-title'>Analysis: {analysis['job_title']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p class='header-subtitle'>ATS Evaluation results for resume: {analysis['filename']}</p>", unsafe_allow_html=True)
    
    # Grid Layout
    col_g, col_b = st.columns([1, 1])
    
    # 1. Gauge chart
    with col_g:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.plotly_chart(get_gauge_chart(analysis["ats_score"]), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    # 2. Score breakdown bar chart
    with col_b:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.plotly_chart(get_subscore_chart(analysis), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    # Row 2: Skills Match details
    col_sm, col_ms = st.columns([1, 1])
    
    with col_sm:
        st.markdown("<div class='glass-card' style='min-height: 250px;'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#34D399; margin-top:0;'>Matching Skills</h3>", unsafe_allow_html=True)
        matching = analysis.get("matching_skills", [])
        if matching:
            st.markdown("<div class='chip-container'>", unsafe_allow_html=True)
            for skill in matching:
                st.markdown(f"<span class='chip chip-match'>{skill}</span>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.write("No matching tech terms identified.")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_ms:
        st.markdown("<div class='glass-card' style='min-height: 250px;'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#FBBF24; margin-top:0;'>Missing Skills</h3>", unsafe_allow_html=True)
        missing = analysis.get("missing_skills", [])
        if missing:
            st.markdown("<div class='chip-container'>", unsafe_allow_html=True)
            for skill in missing:
                st.markdown(f"<span class='chip chip-missing'>{skill}</span>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.success("Great! No critical skills missing from your resume.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Row 3: Section verification & Suggestions
    col_sec, col_sug = st.columns([1, 2])
    
    with col_sec:
        st.markdown("<div class='glass-card' style='min-height: 300px;'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#8B5CF6; margin-top:0;'>Sections Found</h3>", unsafe_allow_html=True)
        sections = analysis.get("sections_detected", {})
        for sec, found in sections.items():
            status = "✅ Detected" if found else "❌ Missing"
            color = "#10B981" if found else "#EF4444"
            st.markdown(f"<div style='display:flex; justify-content:space-between; padding:0.5rem 0; border-bottom:1px solid rgba(255,255,255,0.05);'><span style='font-weight:600;'>{sec}</span><span style='color:{color};'>{status}</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_sug:
        st.markdown("<div class='glass-card' style='min-height: 300px;'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#3B82F6; margin-top:0;'>Resume Recommendations</h3>", unsafe_allow_html=True)
        suggestions = analysis.get("suggestions", [])
        if suggestions:
            for sug in suggestions:
                st.markdown(f"<div class='suggestion-item'><span class='suggestion-bullet'>•</span><span class='suggestion-text'>{sug}</span></div>", unsafe_allow_html=True)
        else:
            st.write("Excellent! No suggestions to display. Your resume matches the job details perfectly.")
        st.markdown("</div>", unsafe_allow_html=True)
        
    # PDF Report Download
    report_filename = f"ATS_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    report_filepath = os.path.join(REPORTS_DIR, report_filename)
    
    # Generate the PDF file
    reporter.generate_pdf_report(analysis, report_filepath)
    
    # Load bytes for button
    with open(report_filepath, "rb") as f:
        pdf_bytes = f.read()
        
    st.download_button(
        label="📥 Download Detailed Evaluation Report (PDF)",
        data=pdf_bytes,
        file_name=report_filename,
        mime="application/pdf",
        use_container_width=True
    )

def render_history_page():
    st.markdown("<h1 class='header-title'>Evaluation History</h1>", unsafe_allow_html=True)
    st.markdown("<p class='header-subtitle'>Browse your historical resume scans and download generated reports</p>", unsafe_allow_html=True)
    
    history = db.get_user_history(st.session_state.user_info["id"])
    
    if not history:
        st.info("You haven't run any evaluations yet. Check out the 'Resume Analyzer' tab to begin.")
        return
        
    df = pd.DataFrame(history)
    # Rename columns for presentation
    df.columns = ["Evaluation ID", "Job Title", "ATS Score", "Skill Match", "Evaluated At", "Resume File"]
    df["ATS Score"] = df["ATS Score"].map(lambda x: f"{x:.1f}%")
    df["Skill Match"] = df["Skill Match"].map(lambda x: f"{x:.1f}%")
    
    # Render table in glass card
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Selection to inspect details
    st.subheader("Inspect past evaluation")
    history_ids = [row["id"] for row in history]
    selected_id = st.selectbox(
        "Select an evaluation to reload into the active dashboard:",
        history_ids,
        format_func=lambda x: next(f"ID {row['id']} - {row['job_title']} ({row['evaluated_at']})" for row in history if row["id"] == x)
    )
    
    if st.button("Load Selected Analysis Details", use_container_width=True):
        detail = db.get_analysis_details(selected_id, st.session_state.user_info["id"])
        if detail:
            st.session_state.current_analysis = detail
            st.success("Loaded selected evaluation! Head over to the 'Dashboard' page in the menu to review the details.")
            st.rerun()

def render_about_page():
    st.markdown("<h1 class='header-title'>About & Support</h1>", unsafe_allow_html=True)
    
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("""
    ### 🚀 AI Resume Analyzer with ATS Score
    This project is a B.Tech 4th Year Computer Science minor project specializing in **Artificial Intelligence and Machine Learning (AI-ML)**.
    
    #### 🌟 Key Functionality
    1. **Semantic Comparison**: Uses natural language processing (TF-IDF Vectorization) and Cosine Similarity to compare candidate resumes against complex corporate job specifications.
    2. **Section Presence Verification**: Custom parsing rules to locate 'Education', 'Experience', 'Projects', 'Skills', and 'Certifications' to verify resume structure compliance.
    3. **Skill Matrix Matching**: Extracts explicit matching/missing terms from a dense index of languages, databases, libraries, clouds, and tools.
    4. **Downloadable Analytics**: Compiles details dynamically into ReportLab flowables to download printable PDF summaries.
    
    #### 🛠️ Technology Stack
    - **UI Layer**: Streamlit Python Frontend framework with injected CSS style sheets.
    - **Persistence**: Local SQLite relational database with secure password hashing (`bcrypt`).
    - **NLP Core**: Custom RegEx parsers, NLTK/Count-based tokenizers, and Scikit-Learn TF-IDF vectorization.
    - **Visualization**: Plotly Graph Objects (Gauge indicators, horizontal subscores) and Pandas data tracking.
    - **Reporting**: ReportLab SimpleDocTemplates.
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
