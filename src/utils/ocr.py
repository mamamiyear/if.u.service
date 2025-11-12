
import json
import logging
from typing import Protocol
from alibabacloud_ocr_api20210707.client import Client as OcrClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_ocr_api20210707 import models as ocr_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient
from .config import get_instance as get_config


class OCR(Protocol):
    def recognize_image_text(self, image_link: str) -> str:
        """
        从图片提取文本
        
        Args:
            image_link (str): 图片链接
        
        Returns:
            str: 提取到的文本
        """
        ...

class AliOCR:
    def __init__(self):
        config = get_config()
        self.access_key = config.get("ali_ocr", "access_key")
        self.secret_key = config.get("ali_ocr", "secret_key")
        self.endpoint = config.get("ali_ocr", "endpoint")
        self.client = self._create_client()

    def _create_client(self):
        config = open_api_models.Config(
            access_key_id=self.access_key,
            access_key_secret=self.secret_key,
        )
        config.endpoint = self.endpoint
        return OcrClient(config)

    def recognize_image_text(self, image_link: str) -> str:
        """
        使用阿里云OCR从图片链接提取文本
        
        Args:
            image_link (str): 图片链接
        
        Returns:
            str: 提取到的文本
        """
        # 创建OCR请求
        recognize_general_request = ocr_models.RecognizeGeneralRequest(url=image_link)
        runtime = util_models.RuntimeOptions()
        try:
            resp = self.client.recognize_general_with_options(recognize_general_request, runtime)
            logging.debug(resp.body.data)
        except Exception as error:
            # 此处仅做打印展示，请谨慎对待异常处理，在工程项目中切勿直接忽略异常。
            # 错误 message
            logging.error(error.message)
            # 诊断地址
            logging.error(error.data.get("Recommend"))
            UtilClient.assert_as_string(error.message)
        
        response = self.client.recognize_general_with_options(recognize_general_request, runtime)
        if response.status_code == 200 and response.body:
            result_data = response.body.data
            result_body = json.loads(result_data)
            if result_body and 'content' in result_body:
                return result_body['content']
        return ""

# 全局OCR实例
_ocr_instance = None


def init():
    """初始化OCR实例"""
    global _ocr_instance
    _ocr_instance = AliOCR()


def get_instance() -> OCR:
    """获取OCR实例"""
    global _ocr_instance
    if _ocr_instance is None:
        raise RuntimeError("OCR模块未初始化，请先调用init()函数")
    return _ocr_instance


if __name__ == "__main__":
    import os
    
    from logger import init as init_logger
    init_logger(console_log_level=logging.DEBUG)
    
    from config import init as init_config
    config_file = os.path.join(os.path.dirname(__file__), "../../configuration/test_conf.ini")
    init_config(config_file)
    
    init()
    ocr = get_instance()
    text = ocr.recognize_image_text(image_link="https://pic.mamamiyear.site/test.if.u/test111.PNG")
    print(text)