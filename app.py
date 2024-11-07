from flask import Flask, render_template, request, jsonify
from database.models import initialize_database, add_job_application, get_job_applications, get_companies_and_titles
from services.resume_matching import ResumeMatchingService
from services.feedback import FeedbackGenerator
from config import Config
from docx import Document
import PyPDF2
import os
import logging

# Initialize the Flask app and logging
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the database
initialize_database()

# Initialize services based on NVIDIA API key availability
if Config.NVIDIA_API_KEY:
    resume_matcher = ResumeMatchingService()
    feedback_generator = FeedbackGenerator()
    logger.info("NVIDIA services initialized.")
else:
    resume_matcher = None
    feedback_generator = None
    logger.warning("NVIDIA API key not available. Resume matching and feedback services are disabled.")

@app.route('/')
def home():
    return render_template('index.html')

# Helper functions to read PDF and DOCX files
def read_pdf(file):
    """Extract text from a PDF file."""
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        logger.error(f"Failed to read PDF file: {e}")
        raise

def read_docx(file):
    """Extract text from a DOCX file."""
    try:
        doc = Document(file)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    except Exception as e:
        logger.error(f"Failed to read DOCX file: {e}")
        raise

@app.route('/submit_application', methods=['POST'])
def submit_application():
    """Submit a job application with resume matching and feedback generation."""
    try:
        # Check if NVIDIA services are initialized
        if not resume_matcher or not feedback_generator:
            return jsonify({"error": "NVIDIA services unavailable. Ensure NVIDIA API key is set."}), 500

        # Extract form data
        company_name = request.form.get('company')
        job_title = request.form.get('job_title')
        job_description = request.form.get('job_description')
        resume_text = request.form.get('resume_text')
        
        job_file = request.files.get('job_file')
        resume_file = request.files.get('resume_file')

        # Validate required inputs
        if not company_name or not job_title:
            return jsonify({"error": "Company name and job title are required."}), 400

        # Read job description and resume text from files if provided
        if job_file and not job_description:
            job_description = job_file.read().decode('utf-8', errors='replace')
        if resume_file:
            if resume_file.filename.endswith('.pdf'):
                resume_text = read_pdf(resume_file)
            elif resume_file.filename.endswith('.docx'):
                resume_text = read_docx(resume_file)
            elif resume_file.filename.endswith('.txt'):
                resume_text = resume_file.read().decode('utf-8', errors='replace')
        
        # Ensure either job description or resume text is provided
        if not job_description and not resume_text:
            return jsonify({"error": "Job description or resume text must be provided."}), 400

        # Calculate the match score
        match_score = resume_matcher.calculate_match_score(job_description, resume_text)
        
        # Ensure match_score is a float/int, not a dict
        if not isinstance(match_score, (int, float)):
            logger.error("Error: match_score is not a numeric value.")
            return jsonify({"error": "Match score calculation returned an unexpected format."}), 500

        # Generate feedback and suggestions
        feedback = feedback_generator.generate_feedback(job_description, resume_text, match_score)
        suggestions = feedback_generator.get_improvement_suggestions(feedback)

        # Store job application in the database
        add_job_application(company_name, job_title, job_description)

        response = {
            'match_score': match_score,
            'feedback': feedback,
            'suggestions': suggestions
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error in /submit_application: {str(e)}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred. Please check the server logs for more details."}), 500

if __name__ == '__main__':
    app.run(debug=True)
