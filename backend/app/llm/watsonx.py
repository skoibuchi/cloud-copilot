from ibm_watsonx_ai.foundation_models.utils.enums import ModelTypes
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
from langchain_ibm import WatsonxLLM


class LLM:
    def __init__(self, apikey, url, project_id,
                 model_id=ModelTypes.GRANITE_13B_CHAT.value, min_new_token=0, max_new_token=500,
                 temperature=0.7, top_p=1, top_k=50, random_seed=None, stop_sequences=None,
                 decoding_method='greedy', repetition_penalty=1):
        self.credentials = {
            'url': url,
            'apikey': apikey
        }

        self.generate_params = {
            GenParams.MAX_NEW_TOKENS: max_new_token,
            GenParams.MIN_NEW_TOKENS: min_new_token,
            GenParams.DECODING_METHOD: decoding_method,
            GenParams.REPETITION_PENALTY: repetition_penalty,
            GenParams.TEMPERATURE: temperature,
            GenParams.TOP_P: top_p,
            GenParams.TOP_K: top_k,
            GenParams.RANDOM_SEED: random_seed,
            GenParams.STOP_SEQUENCES: stop_sequences
        }

        self.llm = WatsonxLLM(
            model_id=model_id,
            url=url,
            apikey=apikey,
            project_id=project_id,
            params=self.generate_params,
        )
