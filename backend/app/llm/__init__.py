from app.core.config import settings
from app.llm.gemini import LLM as GeminiLLM
from app.llm.openai import LLM as OpenAILLM
from app.llm.watsonx import LLM as WatsonxLLM

from dotenv import load_dotenv
load_dotenv()


def get_llm(provider: str):
    provider = provider.lower()
    if provider == "gemini":
        api_key = settings.GEMINI_API_KEY
        model = settings.GEMINI_MODEL
        return GeminiLLM(api_key=api_key, model=model).llm
    elif provider == "openai":
        api_key = settings.OPENAI_API_KEY
        model = settings.OPENAI_MODEL
        return OpenAILLM(api_key=api_key, model=model).llm
    elif provider == "watsonx":
        api_key = settings.WATSONX_API_KEY
        project_id = settings.WATSONX_PROJECT_ID
        url = settings.WATSONX_URL
        model = settings.WATSONX_MODEL
        return WatsonxLLM(api_key=api_key, project_id=project_id, url=url, model_id=model).llm
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
