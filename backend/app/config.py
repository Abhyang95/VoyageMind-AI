import os
from pathlib import Path

from dotenv import load_dotenv


# backend/
BASE_DIR = Path(__file__).resolve().parent.parent


# Load backend/.env
load_dotenv(BASE_DIR / ".env")


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")