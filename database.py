import sqlite3
import os
import bcrypt
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resume_analyzer.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the SQLite database schema."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create Resumes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        extracted_text TEXT NOT NULL,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    """)
    
    # Create ATS History table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ats_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        resume_id INTEGER NOT NULL,
        job_title TEXT NOT NULL,
        job_description TEXT NOT NULL,
        ats_score REAL NOT NULL,
        match_percentage REAL NOT NULL,
        matching_skills TEXT NOT NULL,  -- JSON string of matching skills
        missing_skills TEXT NOT NULL,   -- JSON string of missing skills
        suggestions TEXT NOT NULL,      -- JSON string of lists of advice
        evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (resume_id) REFERENCES resumes (id) ON DELETE CASCADE
    )
    """)
    
    conn.commit()
    conn.close()

# --- User Management ---

def register_user(username, email, password):
    """Register a new user in the database. Returns True if successful, False if username exists."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Hash password
    salt = bcrypt.gensalt()
    pwd_bytes = password.encode('utf-8')
    pwd_hash = bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')
    
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, pwd_hash)
        )
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    finally:
        conn.close()
        
    return success

def authenticate_user(username, password):
    """Authenticate user credentials. Returns user dict if successful, None otherwise."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        # Check password
        pwd_hash = user['password_hash'].encode('utf-8')
        pwd_bytes = password.encode('utf-8')
        if bcrypt.checkpw(pwd_bytes, pwd_hash):
            return {
                "id": user['id'],
                "username": user['username'],
                "email": user['email']
            }
    return None

# --- Resume & Analysis Tracking ---

def save_resume(user_id, filename, file_path, extracted_text):
    """Save resume record and return its row ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO resumes (user_id, filename, file_path, extracted_text) VALUES (?, ?, ?, ?)",
        (user_id, filename, file_path, extracted_text)
    )
    resume_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return resume_id

def save_analysis(user_id, resume_id, job_title, job_description, ats_score, match_percentage, matching_skills, missing_skills, suggestions):
    """Save an ATS analysis record to history."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Serialize lists to JSON strings
    matching_skills_json = json.dumps(matching_skills)
    missing_skills_json = json.dumps(missing_skills)
    suggestions_json = json.dumps(suggestions)
    
    cursor.execute(
        """
        INSERT INTO ats_history 
        (user_id, resume_id, job_title, job_description, ats_score, match_percentage, matching_skills, missing_skills, suggestions)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, resume_id, job_title, job_description, ats_score, match_percentage, matching_skills_json, missing_skills_json, suggestions_json)
    )
    analysis_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return analysis_id

def get_user_history(user_id):
    """Retrieve history of resume evaluations for a given user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT h.id, h.job_title, h.ats_score, h.match_percentage, h.evaluated_at, r.filename
        FROM ats_history h
        JOIN resumes r ON h.resume_id = r.id
        WHERE h.user_id = ?
        ORDER BY h.evaluated_at DESC
        """,
        (user_id,)
    )
    history = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return history

def get_analysis_details(analysis_id, user_id):
    """Fetch complete evaluation details by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT h.*, r.filename, r.extracted_text
        FROM ats_history h
        JOIN resumes r ON h.resume_id = r.id
        WHERE h.id = ? AND h.user_id = ?
        """,
        (analysis_id, user_id)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row:
        detail = dict(row)
        # Deserialize JSON strings
        detail['matching_skills'] = json.loads(detail['matching_skills'])
        detail['missing_skills'] = json.loads(detail['missing_skills'])
        detail['suggestions'] = json.loads(detail['suggestions'])
        return detail
    return None

# Initialize db when this module is imported/run
init_db()
