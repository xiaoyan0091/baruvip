import os
import zipfile
import logging
from datetime import datetime

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

DB_PATH = "bot_vvip/database.db"
BACKUP_DIR = "bot_vvip/backups"

def create_backup():
    """Creates a zip archive of the database file."""
    if not os.path.exists(DB_PATH):
        logger.error("Database file not found for backup.")
        return None, 0

    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{timestamp}.zip"
    backup_filepath = os.path.join(BACKUP_DIR, backup_filename)

    try:
        with zipfile.ZipFile(backup_filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(DB_PATH, os.path.basename(DB_PATH))

        file_size = os.path.getsize(backup_filepath)
        logger.info(f"Database backup created successfully: {backup_filepath}")
        return backup_filepath, file_size
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return None, 0
