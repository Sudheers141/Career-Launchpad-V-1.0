# services/resume_matching.py
from openai import OpenAI
import logging
from typing import Dict
import numpy as np
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

class ResumeMatchingService:
    def __init__(self):
        try:
            logger.info("ResumeMatchingService initialized.")
        except Exception as e:
            logger.error(f"Error initializing ResumeMatchingService: {e}")
            raise

    def truncate_text(self, text: str, max_length: int = 512) -> str:
        """Truncate text to a specified maximum length."""
        return text[:max_length]

    def get_embedding(self, text: str):
        """Generate embeddings for a given text using NVIDIA's nv-embedqa-e5-v5 model."""
        truncated_text = self.truncate_text(text)
        response = client.embeddings.create(
            input=[truncated_text],
            model="nvidia/nv-embedqa-e5-v5",
            encoding_format="float",
            extra_body={"input_type": "query", "truncate": "NONE"}
        )
        return np.array(response.data[0].embedding)

    def calculate_match_score(self, job_description: str, resume_text: str) -> float:
        """Calculate the similarity score using NVIDIA embeddings, with input truncation."""
        try:
            # Truncate texts to meet NVIDIA API's token limit
            job_description = self.truncate_text(job_description)
            resume_text = self.truncate_text(resume_text)

            # Get embeddings
            job_embedding = self.get_embedding(job_description)
            resume_embedding = self.get_embedding(resume_text)

            # Calculate cosine similarity
            similarity = np.dot(job_embedding, resume_embedding) / (np.linalg.norm(job_embedding) * np.linalg.norm(resume_embedding))
            return round(similarity * 100, 2)
        except Exception as e:
            logger.error(f"Error in calculating match score: Error code: {e}")
            return 0.0
