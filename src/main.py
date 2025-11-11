# -*- coding: utf-8 -*-
# created by mmmy on 2025-09-27
import uvicorn
from web.api import api

# 主函数
def main():
    uvicorn.run(api, host='0.0.0.0', port=8099)

if __name__ == "__main__":
    main()