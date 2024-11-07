# database/models.py
import sqlite3
from contextlib import contextmanager
import logging
from config import Config

# Set up logging
logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(Config.DB_PATH)
    try:
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()

def initialize_database():
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Create job_applications table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            job_title TEXT NOT NULL,
            job_description TEXT,
            application_status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Create resumes table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            resume_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Create resume_embeddings table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS resume_embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_id INTEGER,
            embedding BLOB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (resume_id) REFERENCES resumes(id)
        )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_applications_company ON job_applications(company)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_applications_job_title ON job_applications(job_title)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resumes_user_name ON resumes(user_name)")

        conn.commit()
        logger.info("Database initialized and tables created.")

def add_job_application(company, job_title, job_description, application_status="Pending"):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO job_applications (company, job_title, job_description, application_status)
        VALUES (?, ?, ?, ?)
        """, (company, job_title, job_description, application_status))
        conn.commit()
        return cursor.lastrowid

def get_job_applications():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM job_applications")
        return _fetch_all_as_dict(cursor)

def get_companies_and_titles():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT company, job_title FROM job_applications")
        return cursor.fetchall()

def add_resume(user_name, resume_text):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO resumes (user_name, resume_text)
        VALUES (?, ?)
        """, (user_name, resume_text))
        conn.commit()
        return cursor.lastrowid

def add_resume_embedding(resume_id, embedding):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO resume_embeddings (resume_id, embedding)
        VALUES (?, ?)
        """, (resume_id, embedding))
        conn.commit()
        return cursor.lastrowid

def get_resume(resume_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,))
        result = cursor.fetchone()
        return _fetch_one_as_dict(cursor, result)

def update_job_application_status(application_id, new_status):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE job_applications
        SET application_status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """, (new_status, application_id))
        conn.commit()
        return cursor.rowcount > 0

# Helper functions
def _fetch_all_as_dict(cursor):
    """Convert all rows to a list of dictionaries"""
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def _fetch_one_as_dict(cursor, row):
    """Convert a single row to a dictionary"""
    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row)) if row else None
