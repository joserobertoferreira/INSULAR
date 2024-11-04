import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup environment variables
BASE_DIR = Path(__file__).resolve().parent.parent

SERVER_BASE_ADDRESS = os.environ.get('SERVER_BASE_ADDRESS', '')

API_USER = os.environ.get('API_USER', 'admin')
API_PASSWORD = os.environ.get('API_PASSWORD', 'admin')

FOLDER = os.environ.get('FOLDER', BASE_DIR / 'downloads/')

RECEIVER = os.environ.get('API_USER', 'admin')
