import json
import logging
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from models.people import People

class BaseAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            openai_api_key="56d82040-85c7-4701-8f87-734985e27909",
            openai_api_base="https://ark.cn-beijing.volces.com/api/v3",
            model_name="ep-20250722161445-n9lfq"
        )
    pass

class ExtractPeopleAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "你是一个专业的婚姻、交友助手，善于从一段文字描述中，精确获取用户的以下信息：\n"
                "姓名 name\n"
                "性别 gender\n"
                "年龄 age\n"
                "身高(cm) height\n"
                # "体重(kg) weight\n"
                "婚姻状况 marital_status\n"
                "择偶要求 match_requirement\n"
                "以上信息需要严格按照 JSON 格式输出 字段名与条目中英文保持一致。\n"
                "除了上述基本信息，还有一个字段\n"
                "个人介绍 introduction\n"
                "其余的信息需要按照字典的方式进行提炼和总结，都放在个人介绍字段中\n"
                "个人介绍的字典的 key 需要使用提炼好的中文。\n"
            ),
            ("human", "{input}")
        ])
    
    def extract_people_info(self, text: str) -> People:
        """从文本中提取个人信息"""
        prompt = self.prompt.format_prompt(input=text)
        response = self.llm.invoke(prompt)
        logging.info(f"llm response: {response.content}")
        try:
            return People.from_dict(json.loads(response.content))
        except json.JSONDecodeError:
            logging.error(f"Failed to parse JSON from LLM response: {response.content}")
            return None
    pass

class SummaryPeopleAgent(BaseAgent):
    def __init__(self):
        super().__init__()
    pass