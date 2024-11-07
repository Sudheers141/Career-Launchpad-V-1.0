# feedback.py
from openai import OpenAI
import logging
import numpy as np
from typing import Dict, List
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the NVIDIA API client with the masked API key
client = OpenAI(
    api_key=os.getenv("NVIDIA_API_KEY"),  # Load API key from environment
    base_url="https://integrate.api.nvidia.com/v1"
)

logger = logging.getLogger(__name__)

class FeedbackGenerator:
    def __init__(self):
        try:
            logger.info("FeedbackGenerator initialized.")
        except Exception as e:
            logger.error(f"Error initializing FeedbackGenerator: {e}")
            raise

    def get_embedding(self, text: str):
        """Generate embeddings for a given text using NVIDIA's nv-embedqa-e5-v5 model."""
        response = client.embeddings.create(
            input=[text],
            model="nvidia/nv-embedqa-e5-v5",
            encoding_format="float",
            extra_body={"input_type": "query", "truncate": "NONE"}
        )
        return np.array(response.data[0].embedding)

    def calculate_keyword_match(self, job_description: str, resume_text: str) -> Dict:
        """Calculate the similarity score for keywords using NVIDIA embeddings."""
        try:
            job_embedding = self.get_embedding(job_description)
            resume_embedding = self.get_embedding(resume_text)
            similarity = np.dot(job_embedding, resume_embedding) / (np.linalg.norm(job_embedding) * np.linalg.norm(resume_embedding))
            return {"match_score": round(similarity * 100, 2)}
        except Exception as e:
            logger.error(f"Error in calculating keyword match: {e}")
            return {"match_score": 0.0}

    def generate_feedback(self, job_description: str, resume_text: str, match_score: float) -> Dict:
        """Generate feedback based on match score and content analysis."""
        # Analyze keywords (this can be expanded with actual analysis logic)
        missing_keywords = self.analyze_keywords(job_description, resume_text)

        feedback = {
            "overall_match": {
                "assessment": f"The resume matches the job description with a score of {match_score}."
            },
            "keywords_analysis": {
                "missing_keywords": missing_keywords
            },
            "detailed_recommendations": [
                "Consider adding more specific skills related to the job requirements.",
                "Emphasize relevant experience in the job field."
            ]
        }
        return feedback

    def analyze_keywords(self, job_description: str, resume_text: str) -> List[str]:
        """Identify missing keywords from job description in resume."""
        job_keywords = set(job_description.lower().split())
        resume_keywords = set(resume_text.lower().split())
        missing_keywords = list(job_keywords - resume_keywords)
        return missing_keywords[:15]  # Limit to top 15 missing keywords for brevity

    def get_improvement_suggestions(self, feedback: Dict) -> List[str]:
        """Provide improvement suggestions based on feedback."""
        return feedback.get("detailed_recommendations", [])
