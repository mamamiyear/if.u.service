
import datetime
import json
import logging
from langchain.prompts import ChatPromptTemplate

from .base_agent import BaseAgent
from models.custom import Custom

class ExtractCustomAgent(BaseAgent):
    def __init__(self, api_url: str = None, api_key: str = None, model_name: str = None):
        super().__init__(api_url, api_key, model_name)
        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                f"现在是{datetime.datetime.now().strftime('%Y-%m-%d')}，"
                "你是一个专业的客户信息录入助手，善于从一段文字描述中，精确获取客户的以下信息：\n"
                "姓名 name\n"
                "性别 gender (男/女/未知)\n"
                "出生年份 birth (整数年份，如 1990；若文本只提供了年龄，请根据当前日期计算出出生年份)\n"
                "手机号 phone\n"
                "邮箱 email\n"
                "身高(cm) height (整数)\n"
                "体重(kg) weight (整数)\n"
                "学历 degree\n"
                "毕业院校 academy\n"
                "职业 occupation\n"
                "年收入(万) income (整数)\n"
                "资产(万) assets (整数)\n"
                "流动资产(万) current_assets (整数)\n"
                "房产情况 house (必须为以下之一: '有房无贷', '有房有贷', '无自有房', 若未提及则不填)\n"
                "车辆情况 car (必须为以下之一: '有车无贷', '有车有贷', '无自有车', 若未提及则不填)\n"
                "户口城市 registered_city\n"
                "居住城市 live_city\n"
                "籍贯 native_place\n"
                "原生家庭情况 original_family\n"
                "是否独生子女 is_single_child (true/false)\n"
                "择偶要求 match_requirement\n"
                "\n"
                "以上信息需要严格按照 JSON 格式输出，字段名与条目中英文保持一致。\n"
                "若未识别到某项，则不返回该字段，不要自行填写“未知”、“未填写”等。\n"
                "\n"
                "除了上述基本信息，还有一个字段：\n"
                "其他介绍 introductions\n"
                "其余的信息需要按照字典的方式进行提炼和总结，都放在 introductions 字段中，key 使用提炼好的中文。\n"
            ),
            ("human", "{input}")
        ])
    
    def extract_custom_info(self, text: str) -> Custom:
        """从文本中提取客户信息"""
        prompt = self.prompt.format_prompt(input=text)
        response = self.llm.invoke(prompt)
        logging.info(f"llm response: {response.content}")
        try:
            custom_dict = json.loads(response.content)
            
            # 类型安全转换，防止LLM返回字符串类型的数字
            int_fields = ['birth', 'height', 'weight', 'income', 'assets', 'scores', 'current_assets']
            for field in int_fields:
                if field in custom_dict and isinstance(custom_dict[field], str):
                    try:
                        # 尝试提取数字，简单处理
                        import re
                        num = re.findall(r'\d+', custom_dict[field])
                        if num:
                            custom_dict[field] = int(num[0])
                        else:
                            del custom_dict[field] # 无法转换则移除
                    except:
                        del custom_dict[field]

            custom = Custom.from_dict(custom_dict)
            err = custom.validate()
            if not err.success:
                logging.warning(f"Validation warning: {err.info}")
                # 即使校验失败（如某些必填项缺失），也尽可能返回已提取的对象，
                # 让上层业务逻辑决定是否接受或需要补充
            return custom
        except json.JSONDecodeError:
            logging.error(f"Failed to parse JSON from LLM response: {response.content}")
            return None
        except Exception as e:
            logging.error(f"Failed to process custom info: {e}")
            return None
