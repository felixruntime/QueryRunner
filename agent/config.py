# agent/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Segredos
    GEMINI_API_KEY: str = (
        os.getenv("GEMINI_API_KEY") 
        or os.getenv("OPENAI_API_KEY") 
        or os.getenv("GROQ_API_KEY") 
        or ""
    )
    
    # Defaults operacionais sobrescrevíveis pelo .env
    LLM_BASE_URL: str = os.getenv(
        "LLM_BASE_URL", 
        "https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.5-flash")

settings = Settings()
