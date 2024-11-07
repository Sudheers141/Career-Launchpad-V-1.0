# nvidia_embeddings.py
from llama_index.embeddings.nvidia import NVIDIAEmbedding
from config import Config
import asyncio
import logging
from functools import lru_cache

# Configure logging
logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        try:
            if Config.NVIDIA_API_KEY:
                self.embedder = NVIDIAEmbedding(model="NV-Embed-QA", api_key=Config.NVIDIA_API_KEY)
                logger.info("NVIDIA Embedding initialized successfully.")
            else:
                self.embedder = None
                logger.warning("NVIDIA API key not found. Embedding service is unavailable.")
        except Exception as e:
            logger.error(f"Error initializing NVIDIA Embedding: {e}")
            self.embedder = None

    @lru_cache(maxsize=10000)
    def get_job_description_embedding(self, job_description):
        if not self.embedder:
            raise Exception("Embedder not initialized. NVIDIA API key is required.")
        try:
            return self.embedder.get_query_embedding(job_description)
        except Exception as e:
            logger.error(f"Error getting job description embedding: {e}")
            return None

    @lru_cache(maxsize=10000)
    def get_resume_embedding(self, resume_text):
        if not self.embedder:
            raise Exception("Embedder not initialized. NVIDIA API key is required.")
        try:
            return self.embedder.get_text_embedding_batch([resume_text])[0]
        except Exception as e:
            logger.error(f"Error getting resume embedding: {e}")
            return None

    async def get_job_description_embedding_async(self, job_description):
        return await asyncio.to_thread(self.get_job_description_embedding, job_description)

    async def get_resume_embedding_async(self, resume_text):
        return await asyncio.to_thread(self.get_resume_embedding, resume_text)
