
import datetime
import json
import logging
from langchain.prompts import ChatPromptTemplate

from .base_agent import BaseAgent
from models.people import People

class ExtractPeopleAgent(BaseAgent):
    def __init__(self, api_url: str = None, api_key: str = None, model_name: str = None):
        super().__init__(api_url, api_key, model_name)
        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                f"现在是{datetime.datetime.now().strftime('%Y-%m-%d')}，"
                "你是一个专业的婚姻、交友助手，善于从一段文字描述中，精确获取用户的以下信息：\n"
                "姓名 name\n"
                "性别 gender\n"
                "年龄 age\n"
                "身高(cm) height\n"
                "婚姻状况 marital_status\n"
                "择偶要求 match_requirement\n"
                "以上信息需要严格按照 JSON 格式输出 字段名与条目中英文保持一致。\n"
                "其中，'年龄 age' 和 '身高(cm) height' 必须是一个整数，不能是一个字符串；\n"
                "并且，'性别 gender' 根据识别结果，必须从 男,女,未知 三选一填写。\n"
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
            people = People.from_dict(json.loads(response.content))
            err = people.validate()
            if not err.success:
                raise ValueError(f"Failed to validate people info: {err.info}")
            return people
        except json.JSONDecodeError:
            logging.error(f"Failed to parse JSON from LLM response: {response.content}")
            return None
        except ValueError as e:
            logging.error(f"Failed to validate people info: {e}")
            return None
    pass
