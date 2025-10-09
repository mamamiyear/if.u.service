import logging
import os
from datetime import datetime

# 定义颜色代码
class Colors:
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    RESET = '\033[0m'  # 重置颜色

# 自定义控制台处理器，为不同日志级别添加颜色
class ColoredConsoleHandler(logging.StreamHandler):
    def emit(self, record):
        # 为不同日志级别设置颜色
        colors = {
            logging.DEBUG: Colors.CYAN,
            logging.INFO: Colors.GREEN,
            logging.WARNING: Colors.YELLOW,
            logging.ERROR: Colors.RED,
            logging.CRITICAL: Colors.MAGENTA
        }
        
        # 获取对应级别的颜色，默认为白色
        color = colors.get(record.levelno, Colors.WHITE)
        
        # 获取原始消息
        message = self.format(record)
        
        # 添加颜色并输出
        self.stream.write(f"{color}{message}{Colors.RESET}\n")
        self.flush()

def init(log_dir="logs", log_file="log", log_level=logging.INFO, console_log_level=logging.DEBUG):
    # 创建logs目录（如果不存在）
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 设置日志格式
    log_format = "[%(asctime)s.%(msecs)03d][%(filename)s:%(lineno)d][%(levelname)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # 创建格式化器
    formatter = logging.Formatter(log_format, datefmt=date_format)
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.NOTSET)
    
    # 清除现有的处理器
    root_logger.handlers.clear()
    
    # 创建控制台处理器并设置颜色
    console_handler = ColoredConsoleHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(console_log_level)
    root_logger.addHandler(console_handler)
    
    # 创建文件处理器
    log_filename = os.path.join(log_dir, f"{log_file}_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    root_logger.addHandler(file_handler)
    
    # 确保日志消息被正确处理
    logging.addLevelName(logging.DEBUG, "D")
    logging.addLevelName(logging.INFO, "I")
    logging.addLevelName(logging.WARNING, "W")
    logging.addLevelName(logging.ERROR, "E")
    logging.addLevelName(logging.CRITICAL, "C")


if __name__ == "__main__":
    init(log_dir="logs", log_file="test", log_level=logging.INFO, console_log_level=logging.DEBUG)
    logging.debug("debug log")
    logging.info("info log")
    logging.warning("warning log")
    logging.error("error log")
    logging.critical("critical log")