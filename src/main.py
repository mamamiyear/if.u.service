# -*- coding: utf-8 -*-
# created by mmmy on 2025-09-27
import logging
import os
import argparse
from venv import logger
import uvicorn
from app.api import api
from utils import obs, ocr, vsdb
from utils.config import get_instance as get_config, init as init_config
from utils.logger import init as init_logger
from storage import people_store

# 主函数
def main():
    main_path = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(description='IF.u 服务')
    parser.add_argument('--config', type=str, default=os.path.join(main_path, '../configuration/test_conf.ini'), help='配置文件路径')
    args = parser.parse_args()
    init_logger(log_level=logging.DEBUG)
    logger.info(f"args.config: {args.config}")
    init_config(args.config)
    config = get_config()
    print(config.sections())
    obs.init()
    ocr.init()
    vsdb.init()
    people_store.init()
    port = config.getint('web_service', 'server_port', fallback=8099)
    uvicorn.run(api, host="127.0.0.1", port=port)

if __name__ == "__main__":
    main()