import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SERVER_BASE_ADDRESS = os.environ.get('SERVER_BASE_ADDRESS', '')
FOLDER = BASE_DIR / 'downloads/'

API_USER = os.environ.get('API_USER', 'admin')
API_PASSWORD = os.environ.get('API_PASSWORD', 'admin')

RECEIVER = os.environ.get('API_USER', 'admin')
