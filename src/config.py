# import os
# from dotenv import load_dotenv

# # Load environment variables from .env file
# load_dotenv()

# GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")