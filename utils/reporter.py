import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from datetime import datetime

class NumberedCanvas(canvas.Canvas):
    """Canvas that performs a two-pass rendering to add 'Page X of Y' footers and headers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#4A154B")) # Plum accent
        
        # Header (Skip on first page if it's a cover or header-heavy page, but let's keep it clean on all)
        self.drawString(54, 750, "AI RESUME ANALYZER & ATS EVALUATION REPORT")
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#7F8C8D"))
        
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 742, 558, 742)
        
        # Footer
        self.drawString(54, 35, f"Confidential evaluation generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 35, page_text)
        self.line(54, 48, 558, 48)
        self.restoreState()

def generate_pdf_report(analysis, output_path):
    """
    Generate a professional PDF evaluation report.
    `analysis` is a dictionary containing:
        - filename: str
        - job_title: str
        - ats_score: float
        - skill_match_score: float
        - semantic_score: float
        - section_score: float
        - matching_skills: list
        - missing_skills: list
        - suggestions: list
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#1A1A24")
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#7F8C8D")
    )
    
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#4A154B"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#2D3748")
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#2D3748"),
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )
    
    score_label_style = ParagraphStyle(
        'ScoreLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        alignment=1, # Centered
        textColor=colors.HexColor("#FFFFFF")
    )
    
    score_val_style = ParagraphStyle(
        'ScoreVal',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=26,
        leading=30,
        alignment=1, # Centered
        textColor=colors.HexColor("#FFFFFF")
    )
    
    story = []
    
    # Title Section
    story.append(Paragraph("ATS Evaluation Report", title_style))
    story.append(Paragraph(f"Candidate Resume: <b>{analysis.get('filename', 'N/A')}</b>", subtitle_style))
    story.append(Paragraph(f"Target Job Profile: <b>{analysis.get('job_title', 'N/A')}</b>", subtitle_style))
    story.append(Spacer(1, 15))
    
    # Score Summary Table (Banner style)
    overall_score = analysis.get('ats_score', 0.0)
    # Determine badge color
    if overall_score >= 80:
        bg_color = colors.HexColor("#2E7D32") # Emerald
    elif overall_score >= 60:
        bg_color = colors.HexColor("#F57F17") # Amber
    else:
        bg_color = colors.HexColor("#C62828") # Crimson
        
    score_data = [
        [
            Paragraph("ATS MATCH SCORE", score_label_style),
            Paragraph("SKILL MATCH", score_label_style),
            Paragraph("SEMANTIC MATCH", score_label_style),
            Paragraph("SECTION MATCH", score_label_style)
        ],
        [
            Paragraph(f"{overall_score}%", score_val_style),
            Paragraph(f"{analysis.get('skill_match_score', 0.0)}%", score_val_style),
            Paragraph(f"{analysis.get('semantic_score', 0.0)}%", score_val_style),
            Paragraph(f"{analysis.get('section_score', 0.0)}%", score_val_style)
        ]
    ]
    
    score_table = Table(score_data, colWidths=[126, 126, 126, 126])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg_color),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,1), (-1,1), 12),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#FFFFFF")),
        ('BOX', (0,0), (-1,-1), 1, bg_color),
    ]))
    
    story.append(score_table)
    story.append(Spacer(1, 15))
    
    # Section: Skills Analysis
    story.append(Paragraph("Skills Match Analysis", h1_style))
    
    matching_skills = analysis.get("matching_skills", [])
    missing_skills = analysis.get("missing_skills", [])
    
    # Skills display format
    match_str = ", ".join(matching_skills) if matching_skills else "No matching skills identified."
    miss_str = ", ".join(missing_skills) if missing_skills else "No critical skills missing."
    
    skills_data = [
        [Paragraph("<b>Matching Skills:</b>", body_style), Paragraph(match_str, body_style)],
        [Paragraph("<b>Missing Skills:</b>", body_style), Paragraph(miss_str, body_style)]
    ]
    
    skills_table = Table(skills_data, colWidths=[120, 384])
    skills_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LINEBELOW', (0,0), (-1,-2), 0.5, colors.HexColor("#E2E8F0")),
        ('TEXTCOLOR', (0,1), (0,1), colors.HexColor("#C62828")), # Red text for missing
    ]))
    
    story.append(skills_table)
    story.append(Spacer(1, 10))
    
    # Section: Resume Optimization Advice
    story.append(Paragraph("Actionable Suggestions", h1_style))
    suggestions = analysis.get("suggestions", [])
    if suggestions:
        for idx, sug in enumerate(suggestions, 1):
            story.append(Paragraph(f"&bull; {sug}", bullet_style))
    else:
        story.append(Paragraph("No major recommendations! Your resume is highly optimized for this job description.", body_style))
        
    story.append(Spacer(1, 15))
    
    # Section: Details & Metadata
    story.append(Paragraph("Evaluation Metrics Information", h1_style))
    story.append(Paragraph(
        "This evaluation utilizes a three-dimensional scoring system. "
        "The <b>Skill Match Score</b> checks exact matches of key technical terms. "
        "The <b>Semantic Match Score</b> evaluates language compatibility using NLP Vectorization "
        "and Cosine Similarity. The <b>Section Match Score</b> verifies that standard segments (Education, Experience, Skills, Projects, Certifications) are present.",
        body_style
    ))
    
    # Render PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    return output_path
