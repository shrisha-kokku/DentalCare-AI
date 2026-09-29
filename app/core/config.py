import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-oss-120b")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0"))

DATABASE_URL = os.getenv("DATABASE_URL")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")

VALID_SPECIALIZATIONS = [
    "general_dentist", "oral_surgeon", "orthodontist", "cosmetic_dentist",
    "prosthodontist", "pediatric_dentist", "emergency_dentist",
]

DATE_FORMAT = "%m/%d/%Y %H:%M"
CSV_PATH = str(Path(__file__).resolve().parent.parent.parent / "doctor_availability.csv")