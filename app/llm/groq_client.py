from langchain_groq import ChatGroq
from app.core.config import GROQ_API_KEY, MODEL_NAME, TEMPERATURE


def get_llm():
    return ChatGroq(groq_api_key=GROQ_API_KEY, model=MODEL_NAME, temperature=TEMPERATURE)