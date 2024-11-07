# db_setup.py
import sqlite3
import os
import logging
from config import Config

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Create a database connection."""
    return sqlite3.connect(Config.DB_PATH)

def init_db():
    """Initialize the database with tables and schema versioning."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Create a table for job applications
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

            # Create a table for storing resume embeddings
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS resume_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER,
                embedding BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (resume_id) REFERENCES resumes(id)
            )
            """)

            # Create a table for resumes
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                resume_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_applications_company ON job_applications(company)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_applications_job_title ON job_applications(job_title)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_resumes_user_name ON resumes(user_name)")

            # Create a table for schema version
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            )
            """)

            # Insert initial schema version if not exists
            cursor.execute("INSERT OR IGNORE INTO schema_version (version) VALUES (1)")

            conn.commit()
            logger.info("Database initialized and tables created.")
    except sqlite3.Error as e:
        logger.error(f"An error occurred during database initialization: {e}")

def get_schema_version():
    """Retrieve the current schema version from the database."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version FROM schema_version")
            version = cursor.fetchone()
            return version[0] if version else 0
    except sqlite3.Error as e:
        logger.error(f"An error occurred while getting schema version: {e}")
        return 0

def update_schema_version(new_version):
    """Update the schema version in the database."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE schema_version SET version = ?", (new_version,))
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"An error occurred while updating schema version: {e}")

def upgrade_schema():
    """Apply schema upgrades if the current version is outdated."""
    current_version = get_schema_version()
    if current_version < 1:
        # Placeholder for future upgrade steps
        update_schema_version(1)

if __name__ == "__main__":
    if not os.path.exists(Config.DB_PATH):
        init_db()
    upgrade_schema()
