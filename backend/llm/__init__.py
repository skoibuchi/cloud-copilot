import os
from llm.gemini import LLM as GeminiLLM
from llm.openai import LLM as OpenAILLM
from llm.watsonx import LLM as WatsonxLLM

from dotenv import load_dotenv
load_dotenv()


def get_llm(provider: str):
    provider = provider.lower()
    if provider == "gemini":
        api_key = os.getenv("LLM_GEMINI_API_KEY")
        model = os.getenv("LLM_GEMINI_MODEL")
        return GeminiLLM(api_key=api_key, model=model)
    elif provider == "openai":
        api_key = os.getenv("LLM_OPENAI_API_KEY")
        model = os.getenv("LLM_OPENAI_MODEL")
        return OpenAILLM(api_key=api_key, model=model)
    elif provider == "watsonx":
        api_key = os.getenv("LLM_WATSONX_API_KEY")
        project_id = os.getenv("LLM_WATSONX_PROJECT_ID")
        url = os.getenv("LLM_WATSONX_URL")
        model = os.getenv("LLM_WATSONX_MODEL")
        return WatsonxLLM(api_key=api_key, project_id=project_id, base_url=url, model_id=model)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
