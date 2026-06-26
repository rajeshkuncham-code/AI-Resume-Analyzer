import os
import sys
import unittest
import json
import sqlite3

# Ensure current directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import database as db
from utils.parser import clean_text, detect_sections
from utils.analyzer import extract_skills, calculate_cosine_similarity, analyze_resume

class TestResumeAnalyzer(unittest.TestCase):
    
    def setUp(self):
        # Initialize database tables
        db.init_db()
        self.sample_resume = """
        John Doe
        Email: john@example.com | Phone: 1234567890
        
        Education:
        B.Tech in Computer Science, 2024
        
        Skills:
        Python, Machine Learning, Deep Learning, SQL, PyTorch, Git
        
        Experience:
        AI Research Intern at TechCorp (2023)
        Worked on training neural networks using PyTorch.
        
        Projects:
        Cancer Segmentation App using Deep Learning.
        
        Certifications:
        AWS Cloud Practitioner
        """
        
        self.sample_jd = """
        We are looking for an AI Engineer with:
        - Strong experience in Python and SQL.
        - Experience in Machine Learning and Deep Learning.
        - Knowledge of PyTorch and TensorFlow.
        - Understanding of Git version control.
        - Cloud deployment experience (AWS preferred).
        """

    def test_text_cleaning(self):
        raw_text = "Hello \xa0 World!   This is\ttext  with\nmultiple   spaces."
        cleaned = clean_text(raw_text)
        self.assertEqual(cleaned, "Hello World! This is text with multiple spaces.")

    def test_section_detection(self):
        sections = detect_sections(self.sample_resume)
        self.assertTrue(sections["Education"])
        self.assertTrue(sections["Skills"])
        self.assertTrue(sections["Projects"])
        self.assertTrue(sections["Experience"])
        self.assertTrue(sections["Certifications"])

    def test_skill_extraction(self):
        skills = extract_skills(self.sample_resume)
        expected_skills = ["python", "machine learning", "deep learning", "sql", "pytorch", "git", "aws"]
        for skill in expected_skills:
            self.assertIn(skill, skills)

    def test_cosine_similarity(self):
        # Test similarity of identical texts
        sim_identical = calculate_cosine_similarity("Python Machine Learning PyTorch", "Python Machine Learning PyTorch")
        self.assertAlmostEqual(sim_identical, 1.0, places=2)
        
        # Test similarity of completely different texts
        sim_diff = calculate_cosine_similarity("Python Machine Learning PyTorch", "Recipe for apple pie vanilla ice cream")
        self.assertLess(sim_diff, 0.2)

    def test_resume_analysis(self):
        report = analyze_resume(self.sample_resume, self.sample_jd)
        
        # Check output structure
        self.assertIn("ats_score", report)
        self.assertIn("skill_match_score", report)
        self.assertIn("semantic_score", report)
        self.assertIn("section_score", report)
        self.assertIn("matching_skills", report)
        self.assertIn("missing_skills", report)
        self.assertIn("suggestions", report)
        
        # Verify scores are bounds [0, 100]
        self.assertTrue(0 <= report["ats_score"] <= 100)
        self.assertTrue(0 <= report["skill_match_score"] <= 100)
        self.assertTrue(0 <= report["section_score"] <= 100)

    def test_database_operations(self):
        # Register user
        username = "test_user_unique_123"
        email = "test@example.com"
        password = "password123"
        
        # Clear if already exists to ensure test isolation
        conn = db.get_db_connection()
        conn.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        conn.close()
        
        # Try registration
        registered = db.register_user(username, email, password)
        self.assertTrue(registered)
        
        # Authenticate
        user = db.authenticate_user(username, password)
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], username)
        
        # Save resume
        resume_id = db.save_resume(user["id"], "resume.pdf", "path/to/resume.pdf", self.sample_resume)
        self.assertTrue(resume_id > 0)
        
        # Save analysis
        analysis_id = db.save_analysis(
            user["id"],
            resume_id,
            "AI Engineer",
            self.sample_jd,
            85.5,
            80.0,
            ["python", "sql"],
            ["tensorflow"],
            ["Add TensorFlow to projects."]
        )
        self.assertTrue(analysis_id > 0)
        
        # Get history
        history = db.get_user_history(user["id"])
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["job_title"], "AI Engineer")
        
        # Get details
        details = db.get_analysis_details(analysis_id, user["id"])
        self.assertIsNotNone(details)
        self.assertEqual(details["ats_score"], 85.5)
        self.assertEqual(details["matching_skills"], ["python", "sql"])
        
        # Clean up
        conn = db.get_db_connection()
        conn.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        conn.close()

if __name__ == "__main__":
    unittest.main()
