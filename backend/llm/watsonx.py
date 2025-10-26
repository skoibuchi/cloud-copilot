# Note:
# As of langchain_ibm version==0.3.19, there is an issue where it cannot be used unless langchain-core<0.4.0.
# The library cannot be used because it conflicts with langchain-core used elsewhere.


# from ibm_watsonx_ai.foundation_models.utils.enums import ModelTypes
# from ibm_watsonx_ai.foundation_models import Model
# from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
# from langchain_ibm import WatsonxLLM


# class LLM:
#     def __init__(self, apikey, url, project_id,
#                  model_id=ModelTypes.LLAMA_3_70B_INSTRUCT.value, min_new_token=0, max_new_token=500,
#                  temperature=0.7, top_p=1, top_k=50, random_seed=None, stop_sequences=None,
#                  decoding_method='greedy', repetition_penalty=1):
#         self.credentials = {
#             'url': url,
#             'apikey': apikey
#         }

#         self.generate_params = {
#             GenParams.MAX_NEW_TOKENS: max_new_token,
#             GenParams.MIN_NEW_TOKENS: min_new_token,
#             GenParams.DECODING_METHOD: decoding_method,
#             GenParams.REPETITION_PENALTY: repetition_penalty,
#             GenParams.TEMPERATURE: temperature,
#             GenParams.TOP_P: top_p,
#             GenParams.TOP_K: top_k,
#             GenParams.RANDOM_SEED: random_seed,
#             GenParams.STOP_SEQUENCES: stop_sequences
#         }

#         self.llm = WatsonxLLM(
#             model_id=model_id,
#             url=url,
#             apikey=apikey,
#             project_id=project_id,
#             params=self.generate_params,
#         )

import os
import requests
from typing import List, Optional
from langchain.chat_models.base import BaseChatModel
from langchain.messages import HumanMessage
from langchain_core.messages.base import BaseMessage

from dotenv import load_dotenv
load_dotenv()


class LLM(BaseChatModel):

    model_id: str
    api_key: str
    base_url: str
    project_id: str
    api_version: str = "2023-08-01"

    def __init__(
        self,
        project_id: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_id: str = "mistralai/mistral-medium-2505",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.model_id = model_id or os.getenv("WATSONX_MODEL_ID")
        self.project_id = project_id or os.getenv("WATSONX_PRIJECT_ID")
        self.base_url = base_url or os.getenv("WATSONX_URL")
        self.api_key = api_key or os.getenv("WATSONX_API_KEY")
        self.api_version = os.getenv("WATSONX_API_VERSION", self.api_version)

        if not self.base_url or not self.api_key or not self.project_id:
            raise ValueError("base_url, api_key, project_id are invalid.")

    @property
    def _llm_type(self) -> str:
        return "watsonx"

    def _get_token(self) -> str:
        url = "https://iam.cloud.ibm.com/identity/token"
        payload = {
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": self.api_key,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        resp = requests.post(url, data=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()["access_token"]

    def _call(self, messages: List[BaseMessage], stop: Optional[List[str]] = None) -> str:
        prompt = "\n".join([m.content for m in messages if isinstance(m, HumanMessage)])
        token = self._get_token()

        url = f"{self.base_url}/ml/v1/text/generation?version={self.api_version}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {
            "input": prompt,
            "model_id": self.model_id,
            "parameters": {
                "max_new_tokens": 500,
                "time_limit": 1000,
            },
            "project_id": self.project_id,
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get("output_text") or data.get("text") or str(data)

    async def _acall(self, messages: List[BaseMessage], stop: Optional[List[str]] = None) -> str:
        """just call sync method"""
        return self._call(messages, stop)
