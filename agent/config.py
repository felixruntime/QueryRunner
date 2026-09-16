# agent/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Suporte automático para Streamlit Community Cloud (lê de st.secrets se disponível)
try:
    import streamlit as st
    if hasattr(st, "secrets"):
        for key in ["GEMINI_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY", "LLM_BASE_URL", "LLM_MODEL"]:
            if key in st.secrets and not os.getenv(key):
                os.environ[key] = str(st.secrets[key])
except Exception:
    pass

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
