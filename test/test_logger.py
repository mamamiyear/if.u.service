import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from utils.logger import init
import logging

# 初始化日志
init()

# 测试不同级别的日志
logging.debug("这是一条调试信息")
logging.info("这是一条普通信息")
logging.warning("这是一条警告信息")
logging.error("这是一条错误信息")
logging.critical("这是一条严重错误信息")