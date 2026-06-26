import re
import math
from collections import Counter
from utils.parser import detect_sections

# Try to import sklearn, use fallback if not available
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# Comprehensive skill bank for resume evaluation
TECHNICAL_SKILLS = [
    # Programming Languages
    "python", "java", "sql", "javascript", "typescript", "c++", "c#", "c", "html", "css", "rust", "go", "ruby", "php", "swift", "kotlin", "bash", "shell",
    # AI/ML/Data Science
    "machine learning", "deep learning", "data science", "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn", "pandas", "numpy", "natural language processing", "nlp", "computer vision", "opencv", "matplotlib", "seaborn", "plotly", "scipy", "xgboost",
    # Frameworks & Libraries
    "react", "angular", "vue", "node.js", "nodejs", "express", "django", "flask", "fastapi", "spring boot", "springboot", "laravel", "next.js", "nextjs", "bootstrap", "tailwind", "jquery", "streamlit",
    # Cloud & DevOps
    "aws", "amazon web services", "azure", "gcp", "google cloud", "docker", "kubernetes", "git", "github", "gitlab", "jenkins", "ci/cd", "terraform", "ansible", "linux", "unix",
    # Databases
    "mysql", "postgresql", "postgres", "mongodb", "sqlite", "redis", "oracle", "mariadb", "cassandra", "elasticsearch",
    # Other Tools / Concepts
    "rest api", "graphql", "microservices", "agile", "scrum", "jira", "oop", "system design", "tableau", "power bi", "excel"
]

# Simple English stopwords for fallback similarity
STOPWORDS = set([
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself", "yourselves",
    "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their",
    "theirs", "themselves", "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are",
    "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an",
    "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about",
    "against", "between", "into", "through", "during", "before", "after", "above", "below", "to", "from", "up",
    "down", "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when",
    "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don",
    "should", "now"
])

def compile_skill_regexes():
    """Compile regexes for each skill to ensure word boundaries and handle special chars."""
    regexes = {}
    for skill in TECHNICAL_SKILLS:
        escaped = re.escape(skill)
        # Apply bounds: C++ or C# don't end with word characters, so \b won't match.
        # Use negative lookahead/lookbehind for word chars to be safe.
        start_boundary = r'\b' if skill[0].isalnum() else r'(?<!\w)'
        end_boundary = r'\b' if skill[-1].isalnum() else r'(?!\w)'
        regexes[skill] = re.compile(start_boundary + escaped + end_boundary, re.IGNORECASE)
    return regexes

SKILL_REGEXES = compile_skill_regexes()

def extract_skills(text):
    """
    Extract technical skills present in the text based on our skill bank.
    Returns a set of matched skill names (in standardized format).
    """
    matched_skills = set()
    if not text:
        return matched_skills
        
    text_lower = text.lower()
    for skill, regex in SKILL_REGEXES.items():
        if regex.search(text_lower):
            matched_skills.add(skill)
            
    return list(matched_skills)

def calculate_cosine_similarity_fallback(text1, text2):
    """Fallback Cosine Similarity calculation in pure Python when sklearn is missing."""
    def tokenize(t):
        return re.findall(r'\b[a-z0-9\-]+\b', t.lower())

    tokens1 = [t for t in tokenize(text1) if t not in STOPWORDS]
    tokens2 = [t for t in tokenize(text2) if t not in STOPWORDS]
    
    if not tokens1 or not tokens2:
        return 0.0
        
    tf1 = Counter(tokens1)
    tf2 = Counter(tokens2)
    
    vocab = set(tf1.keys()).union(set(tf2.keys()))
    
    # Calculate simple TF-IDF weights
    # IDF(t) = ln( 3 / (1 + DF(t)) ) + 1 (since doc count = 2)
    idf = {}
    for term in vocab:
        df = 0
        if term in tf1: df += 1
        if term in tf2: df += 1
        idf[term] = math.log(3.0 / (1.0 + df)) + 1.0
        
    vec1 = {term: tf1[term] * idf[term] for term in tf1}
    vec2 = {term: tf2[term] * idf[term] for term in tf2}
    
    dot_product = sum(vec1.get(term, 0) * vec2.get(term, 0) for term in vocab)
    mag1 = math.sqrt(sum(v**2 for v in vec1.values()))
    mag2 = math.sqrt(sum(v**2 for v in vec2.values()))
    
    if mag1 == 0 or mag2 == 0:
        return 0.0
        
    return dot_product / (mag1 * mag2)

def calculate_cosine_similarity(text1, text2):
    """Calculate TF-IDF Cosine Similarity between two texts, with pure Python fallback."""
    if not text1 or not text2:
        return 0.0
        
    if SKLEARN_AVAILABLE:
        try:
            vectorizer = TfidfVectorizer(stop_words='english')
            tfidf = vectorizer.fit_transform([text1, text2])
            sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
            return float(sim)
        except Exception as e:
            print(f"Error in sklearn similarity calculation: {e}. Falling back...")
            
    # Fallback to pure Python TF-IDF cosine similarity
    return calculate_cosine_similarity_fallback(text1, text2)

def analyze_resume(resume_text, job_description):
    """
    Core ATS scoring engine.
    Calculates overall score, breakdown, matching/missing skills, and recommendations.
    """
    # 1. Skill Extraction
    resume_skills = set(extract_skills(resume_text))
    jd_skills = set(extract_skills(job_description))
    
    # Matching and Missing
    if jd_skills:
        matching_skills = list(resume_skills.intersection(jd_skills))
        missing_skills = list(jd_skills.difference(resume_skills))
        skill_match_score = (len(matching_skills) / len(jd_skills)) * 100
    else:
        # If no skills are found in JD, look for all resume skills as a general positive matching
        matching_skills = list(resume_skills)
        missing_skills = []
        skill_match_score = 100.0 if resume_skills else 0.0
        
    # 2. Semantic Text Similarity
    semantic_score = calculate_cosine_similarity(resume_text, job_description) * 100
    
    # 3. Section Presence Detection
    sections_detected = detect_sections(resume_text)
    detected_count = sum(1 for v in sections_detected.values() if v)
    section_score = (detected_count / len(sections_detected)) * 100
    
    # 4. Final ATS Score calculation
    # Weights: 40% Skill Match, 40% Semantic Similarity, 20% Section Presence
    ats_score = (0.4 * skill_match_score) + (0.4 * semantic_score) + (0.2 * section_score)
    # Bound to [0, 100]
    ats_score = max(0.0, min(100.0, ats_score))
    
    # 5. Generate Suggestions
    suggestions = []
    
    # Section Suggestions
    missing_sections = [sec for sec, found in sections_detected.items() if not found]
    if missing_sections:
        suggestions.append(f"Add missing sections to your resume: {', '.join(missing_sections)}.")
        
    # Skill Suggestions
    if missing_skills:
        # Prioritize top 5 missing skills if too many
        top_missing = missing_skills[:5]
        suggestions.append(f"Incorporate these missing skills from the job description: {', '.join(top_missing)}.")
        
    # Length / Word Count Suggestions
    word_count = len(resume_text.split())
    if word_count < 200:
        suggestions.append("Your resume seems very short (under 200 words). Try to add more details about your achievements and responsibilities.")
    elif word_count > 800:
        suggestions.append("Your resume is quite long (over 800 words). Try to keep it concise and focused on high-impact points.")
        
    # Formatting/Keywords suggestions
    if semantic_score < 30:
        suggestions.append("The wording in your resume is significantly different from the job description. Try to rephrase your experience to match the terminology used in the job description.")
        
    if not sections_detected["Projects"]:
        suggestions.append("Consider adding a 'Projects' section highlighting your academic or personal technical builds, showcasing your hands-on AI/ML or development experience.")
        
    if not sections_detected["Certifications"]:
        suggestions.append("Adding professional certifications (e.g., AWS, TensorFlow, Coursera) will validate your specialized training and strengthen your application.")

    return {
        "ats_score": round(ats_score, 1),
        "skill_match_score": round(skill_match_score, 1),
        "semantic_score": round(semantic_score, 1),
        "section_score": round(section_score, 1),
        "sections_detected": sections_detected,
        "matching_skills": sorted(matching_skills),
        "missing_skills": sorted(missing_skills),
        "suggestions": suggestions,
        "word_count": word_count
    }
