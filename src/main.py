# -*- coding: utf-8 -*-
# created by mmmy on 2025-09-27
import os
import sys

# Add src directory to sys.path to ensure modules can be imported correctly when running with uvicorn
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse
import uvicorn
from services import people as people_service
from services import user as user_service
from services import custom as custom_service
from utils import config, logger, obs, ocr, rldb, sms, mailer

from web.api import api

def initialize_app(config_path):
    """Initialize application components with the given config path."""
    config.init(config_path)
    conf = config.get_instance()
    
    logger.init()
    rldb.init()
    ocr.init()
    obs.init()
    mailer.init(conf.get('mailer', 'type', fallback='real'))
    sms.init(conf.get('sms', 'type', fallback='real'))

    people_service.init()
    user_service.init()
    custom_service.init()

# 主函数
def main():
    main_path = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(description='IF.u 服务')
    parser.add_argument('--config', type=str, default=os.path.join(main_path, '../configuration/test_conf.ini'), help='配置文件路径')
    args = parser.parse_args()
    
    initialize_app(args.config)
    
    conf = config.get_instance()
    host = conf.get('web_service', 'server_host', fallback='0.0.0.0')
    port = conf.getint('web_service', 'server_port', fallback=8099)
    uvicorn.run("src.main:api", host=host, port=port, reload=True) # Modified to string import for reload support in main too, though api object also works

if __name__ == "__main__":
    main()
else:
    # Support for running via 'uvicorn src.main:api'
    # Use environment variable for config path or default
    main_path = os.path.dirname(os.path.abspath(__file__))
    default_config_path = os.path.join(main_path, '../configuration/test_conf.ini')
    config_path = os.environ.get('IFU_CONFIG_PATH', default_config_path)
    initialize_app(config_path)
