
from langchain_openai import ChatOpenAI
from utils.config import get_instance as get_config

class BaseAgent:
    def __init__(self, api_url: str = None, api_key: str = None, model_name: str = None):
        config = get_config()
        llm_api_url = api_url or config.get("ai", "llm_api_url")
        llm_api_key = api_key or config.get("ai", "llm_api_key")
        llm_model_name = model_name or config.get("ai", "llm_model_name")
        self.llm = ChatOpenAI(
            openai_api_key=llm_api_key,
            openai_api_base=llm_api_url,
            model_name=llm_model_name,
        )
    pass


class SummaryPeopleAgent(BaseAgent):
    def __init__(self):
        super().__init__()
    pass