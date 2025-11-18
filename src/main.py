# -*- coding: utf-8 -*-
# created by mmmy on 2025-09-27
import os
import argparse
import uvicorn
from services import people as people_service
from services import user as user_service
from utils import config, logger, obs, ocr, rldb, sms, mailer

from web.api import api

# 主函数
def main():
    main_path = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(description='IF.u 服务')
    parser.add_argument('--config', type=str, default=os.path.join(main_path, '../configuration/test_conf.ini'), help='配置文件路径')
    args = parser.parse_args()
    
    config.init(args.config)
    conf = config.get_instance()
    
    logger.init()
    rldb.init()
    ocr.init()
    obs.init()
    mailer.init(conf.get('mailer', 'type', fallback='real'))
    sms.init(conf.get('sms', 'type', fallback='real'))

    people_service.init()
    user_service.init()
    
    

    host = conf.get('web_service', 'server_host', fallback='0.0.0.0')
    port = conf.getint('web_service', 'server_port', fallback=8099)
    uvicorn.run(api, host=host, port=port)

if __name__ == "__main__":
    main()