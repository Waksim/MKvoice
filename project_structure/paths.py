# ============================= FILE: project_structure/paths.py =============================
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / 'MKvoiceDB.sqlite'

STRUCTURE_DIR = PROJECT_ROOT / 'project_structure' / 'backup'
STRUCTURE_DIR.mkdir(parents=True, exist_ok=True)

STRUCTURE_FILE = STRUCTURE_DIR / 'project_structure.txt'
IMAGES_STRUCTURE_FILE = STRUCTURE_DIR / 'images_structure.txt'
ARCHIVE_FILE = STRUCTURE_DIR / 'project_archive.zip'
DATABASE_SCHEMA_FILE = STRUCTURE_DIR / 'database_schema_telegram_messages.sql'
DB_DESCRIPTION_FILE = STRUCTURE_DIR / 'db_description.txt'

IGNORE_DIRS = {
    '.git', '.idea', '__pycache__', 'venv', 'env',
    '.venv', '.env', 'node_modules', 'backup'
}
IGNORE_FILES = {'.DS_Store', 'project_archive.zip'}
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.svg', '.webp'}
IGNORE_EXT = {'.pyc', '.pyo', '.log', '.db', '.zip', '.tar', '.gz', '.bz2', '.7z', '.rar'}

LOG_DIR = PROJECT_ROOT / 'logs'
LOG_DIR.mkdir(exist_ok=True)