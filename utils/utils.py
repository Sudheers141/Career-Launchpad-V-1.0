# utils.py
import os
import re
import logging
import hashlib
from datetime import datetime
from typing import Optional, Set, Dict, Union
import docx2txt
import PyPDF2
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import magic
import chardet
from collections import Counter
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FileProcessingError(Exception):
    """Custom exception for file processing errors."""
    pass

class FileHandler:
    ALLOWED_EXTENSIONS = {'.txt', '.pdf', '.docx', '.doc'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    @staticmethod
    def get_file_hash(file_path: str) -> str:
        """Generate SHA-256 hash of file content."""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def get_mime_type(file_path: str) -> str:
        """Detect real file type using python-magic."""
        return magic.from_file(file_path, mime=True)

    @staticmethod
    def detect_encoding(file_path: str) -> str:
        """Detect character encoding of text file using chardet."""
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        return chardet.detect(raw_data)['encoding']

class TextExtractor:
    """Class for extracting text from various file types."""
    
    def __init__(self):
        self.supported_formats = {
            '.txt': self._extract_from_txt,
            '.pdf': self._extract_from_pdf,
            '.docx': self._extract_from_docx,
            '.doc': self._extract_from_docx  # Assuming .doc files can be handled by docx2txt
        }

    def extract_text(self, file_path: str) -> str:
        """Main method to extract text based on file type."""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in self.supported_formats:
                raise FileProcessingError(f"Unsupported file format: {file_ext}")

            # Verify file size
            if os.path.getsize(file_path) > FileHandler.MAX_FILE_SIZE:
                raise FileProcessingError("File size exceeds maximum limit")

            # Extract text using appropriate method
            text = self.supported_formats[file_ext](file_path)
            return self.clean_text(text)

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            raise FileProcessingError(f"Error processing file: {str(e)}")

    def _extract_from_txt(self, file_path: str) -> str:
        """Extract text from TXT files."""
        encoding = FileHandler.detect_encoding(file_path)
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                return file.read()
        except UnicodeDecodeError:
            logger.warning(f"Failed to decode with {encoding}, trying utf-8")
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                return file.read()

    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF files with OCR fallback for images."""
        try:
            text = ""
            with open(file_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if not page_text.strip():
                        # If no text extracted, try OCR
                        text += self._ocr_pdf_page(file_path, reader.pages.index(page))
                    else:
                        text += page_text
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise FileProcessingError(f"PDF extraction failed: {str(e)}")

    def _ocr_pdf_page(self, pdf_path: str, page_number: int) -> str:
        """Perform OCR on a PDF page."""
        try:
            images = convert_from_path(pdf_path, first_page=page_number + 1, last_page=page_number + 1)
            if images:
                return pytesseract.image_to_string(images[0])
            return ""
        except Exception as e:
            logger.warning(f"OCR failed for page {page_number}: {str(e)}")
            return ""

    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX files."""
        try:
            return docx2txt.process(file_path)
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {str(e)}")
            raise FileProcessingError(f"DOCX extraction failed: {str(e)}")

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize extracted text."""
        text = text.lower()
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\.+', '.', text)
        return text.strip()

class FileManager:
    """Handles file saving, path management, and validation."""
    
    def __init__(self, upload_folder: str):
        self.upload_folder = upload_folder
        self.ensure_upload_folder()

    def ensure_upload_folder(self):
        """Create upload folder if it doesn't exist."""
        os.makedirs(self.upload_folder, exist_ok=True)

    def generate_unique_filename(self, original_filename: str) -> str:
        """Generate a unique filename with timestamp."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base, ext = os.path.splitext(original_filename)
        return f"{base}_{timestamp}{ext}"

    def save_file(self, file, filename: Optional[str] = None) -> Dict[str, str]:
        """Save uploaded file and return metadata."""
        if filename is None:
            filename = self.generate_unique_filename(file.filename)

        file_path = os.path.join(self.upload_folder, filename)
        
        try:
            file.save(file_path)
            file_hash = FileHandler.get_file_hash(file_path)
            mime_type = FileHandler.get_mime_type(file_path)

            return {
                'filename': filename,
                'path': file_path,
                'hash': file_hash,
                'mime_type': mime_type,
                'size': os.path.getsize(file_path)
            }

        except Exception as e:
            logger.error(f"Error saving file {filename}: {str(e)}")
            raise FileProcessingError(f"Error saving file: {str(e)}")

# Additional utility classes and functions (CacheManager, SecurityUtils, etc.) remain as in the provided code.


def validate_file(file, max_size: int = FileHandler.MAX_FILE_SIZE) -> bool:
    """
    Validate file before processing
    """
    if not file:
        return False
    
    filename = file.filename
    file_size = file.content_length if hasattr(file, 'content_length') else 0

    return (
        '.' in filename and
        os.path.splitext(filename)[1].lower() in FileHandler.ALLOWED_EXTENSIONS and
        file_size <= max_size
    )

class TextAnalyzer:
    """Utility class for text analysis"""
    
    @staticmethod
    def get_word_count(text: str) -> int:
        """Count words in text"""
        return len(text.split())

    @staticmethod
    def get_keyword_density(text: str, keyword: str) -> float:
        """Calculate keyword density in text"""
        words = text.split()
        keyword_count = sum(1 for word in words if word.lower() == keyword.lower())
        return (keyword_count / len(words)) * 100 if words else 0

    @staticmethod
    def extract_contact_info(text: str) -> Dict[str, str]:
        """Extract contact information from text"""
        contact_info = {
            'email': [],
            'phone': [],
            'linkedin': []
        }
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        contact_info['email'] = re.findall(email_pattern, text)
        
        # Phone pattern (various formats)
        phone_pattern = r'\b(?:\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b'
        contact_info['phone'] = re.findall(phone_pattern, text)
        
        # LinkedIn URL pattern
        linkedin_pattern = r'(?:https?:)?//(?:[\w]+\.)?linkedin\.com/in/[\w\-_]+/?'
        contact_info['linkedin'] = re.findall(linkedin_pattern, text)
        
        return contact_info

class CacheManager:
    """Simple cache manager for file processing results"""
    
    def __init__(self):
        self.cache = {}
        self.max_cache_size = 1000
        self.cache_timeout = 3600  # 1 hour in seconds

    def get(self, key: str) -> Optional[Dict]:
        """Get item from cache"""
        if key in self.cache:
            item = self.cache[key]
            if (datetime.now() - item['timestamp']).seconds < self.cache_timeout:
                return item['data']
            else:
                del self.cache[key]
        return None

    def set(self, key: str, value: Dict):
        """Set item in cache"""
        if len(self.cache) >= self.max_cache_size:
            # Remove oldest items
            oldest = min(self.cache.items(), key=lambda x: x[1]['timestamp'])
            del self.cache[oldest[0]]
        
        self.cache[key] = {
            'data': value,
            'timestamp': datetime.now()
        }

class SecurityUtils:
    """Security-related utility functions"""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal"""
        return os.path.basename(filename)

    @staticmethod
    def is_file_safe(file_path: str) -> bool:
        """
        Check if file is safe (not malicious)
        Basic implementation - could be extended with virus scanning etc.
        """
        try:
            mime_type = FileHandler.get_mime_type(file_path)
            return mime_type in [
                'text/plain',
                'application/pdf',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ]
        except Exception:
            return False

def setup_logging(log_file: str = 'file_processing.log'):
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

class MetricsCollector:
    """Collect metrics about file processing"""
    
    def __init__(self):
        self.metrics = {
            'processed_files': 0,
            'failed_files': 0,
            'processing_times': [],
            'file_sizes': [],
            'file_types': Counter()
        }

    def add_metric(self, metric_type: str, value: Union[int, float, str]):
        """Add a metric measurement"""
        if metric_type == 'processing_time':
            self.metrics['processing_times'].append(value)
        elif metric_type == 'file_size':
            self.metrics['file_sizes'].append(value)
        elif metric_type == 'file_type':
            self.metrics['file_types'][value] += 1

    def get_statistics(self) -> Dict:
        """Get statistical summary of metrics"""
        return {
            'total_processed': self.metrics['processed_files'],
            'total_failed': self.metrics['failed_files'],
            'avg_processing_time': np.mean(self.metrics['processing_times']) if self.metrics['processing_times'] else 0,
            'avg_file_size': np.mean(self.metrics['file_sizes']) if self.metrics['file_sizes'] else 0,
            'file_type_distribution': dict(self.metrics['file_types'])
        }

# Initialize global instances
text_extractor = TextExtractor()
file_manager = FileManager(upload_folder='uploads')
cache_manager = CacheManager()
metrics_collector = MetricsCollector()

# Setup logging
setup_logging()