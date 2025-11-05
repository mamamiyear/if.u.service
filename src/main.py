# -*- coding: utf-8 -*-
# created by mmmy on 2025-09-27
import logging
import os
import argparse
from venv import logger
import uvicorn
from app.api import api
from utils import obs, ocr, vsdb, logger, config, kwdb
from storage import people_store

# 主函数
def main():
    main_path = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(description='IF.u 服务')
    parser.add_argument('--config', type=str, default=os.path.join(main_path, '../configuration/test_conf.ini'), help='配置文件路径')
    args = parser.parse_args()
    config.init(args.config)
    logger.init()
    obs.init()
    ocr.init()
    vsdb.init()
    kwdb.init()
    people_store.init()
    conf = config.get_instance()
    host = conf.get('web_service', 'server_host', fallback='127.0.0.1')
    port = conf.getint('web_service', 'server_port', fallback=8099)
    uvicorn.run(api, host=host, port=port)

if __name__ == "__main__":
    main()