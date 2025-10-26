from langchain_openai import ChatOpenAI


class LLM:
    def __init__(self, api_key: str, model="gpt-3.5-turbo"):
        if not api_key:
            raise ValueError("OpenAI APIキーを指定してください")
        self.llm = ChatOpenAI(api_key=api_key, model=model)
