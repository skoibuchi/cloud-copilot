from langchain_google_genai import ChatGoogleGenerativeAI


class LLM:
    def __init__(self, model="gemini-1.5-flash", api_key: str = None):
        if not api_key:
            raise ValueError("Gemini APIキーを明示的に指定してください。")
        self.llm = ChatGoogleGenerativeAI(model=model, api_key=api_key)
