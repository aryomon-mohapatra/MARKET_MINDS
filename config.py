import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL    = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
MAX_TOKENS    = int(os.getenv("MAX_TOKENS", "4096"))
PORT          = int(os.getenv("PORT", "8000"))
