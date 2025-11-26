# -*- coding: utf-8 -*-
# created by mmmy on 2025-11-27

import logging
import uuid
from models.custom import Custom, CustomRLDBModel
from utils.error import ErrorCode, error
from utils import rldb

class CustomService:
    def __init__(self):
        self.rldb = rldb.get_instance()

    def save(self, custom: Custom) -> (str, error):
        """
        保存客户到数据库。
        如果 custom.id 存在，则更新；否则，创建。
        
        :param custom: 客户对象
        :return: 客户ID 和 错误对象
        """
        # 0. 生成 custom id
        custom.id = custom.id if custom.id else uuid.uuid4().hex
        
        # 1. 转换模型，并保存到 SQL 数据库
        try:
            custom_orm = custom.to_rldb_model()
            self.rldb.upsert(custom_orm)
            return custom.id, error(ErrorCode.SUCCESS, "")
        except Exception as e:
            logging.error(f"Failed to save custom {custom.id}: {e}")
            return "", error(ErrorCode.RLDB_ERROR, f"Failed to save custom data: {str(e)}")
    
    def delete(self, custom_id: str) -> error:
        """
        从数据库删除客户。
        
        :param custom_id: 客户ID
        :return: 错误对象
        """
        try:
            custom_orm = self.rldb.get(CustomRLDBModel, custom_id)
            if not custom_orm:
                return error(ErrorCode.RLDB_NOT_FOUND, f"Custom {custom_id} not found.")
            self.rldb.delete(custom_orm)
            return error(ErrorCode.SUCCESS, "")
        except Exception as e:
            logging.error(f"Failed to delete custom {custom_id}: {e}")
            return error(ErrorCode.RLDB_ERROR, f"Failed to delete custom data: {str(e)}")
    
    def get(self, custom_id: str) -> (Custom, error):
        """
        从数据库获取单个客户。
        
        :param custom_id: 客户ID
        :return: 客户对象 和 错误对象
        """
        try:
            custom_orm = self.rldb.get(CustomRLDBModel, custom_id)
            if not custom_orm:
                return None, error(ErrorCode.RLDB_NOT_FOUND, f"Custom {custom_id} not found.")
            
            custom = Custom.from_rldb_model(custom_orm)
            return custom, error(ErrorCode.SUCCESS, "")
        except Exception as e:
            logging.error(f"Failed to get custom {custom_id}: {e}")
            return None, error(ErrorCode.RLDB_ERROR, f"Failed to retrieve custom data: {str(e)}")
    
    def list(self, conds: dict = None, limit: int = 10, offset: int = 0) -> (list[Custom], error):
        """
        根据条件从数据库列出客户（支持分页）。
        
        :param conds: 查询条件字典
        :param limit: 每页数量
        :param offset: 偏移量
        :return: 客户对象列表 和 错误对象
        """
        if conds is None:
            conds = {}
        try:
            custom_orms = self.rldb.query(CustomRLDBModel, limit=limit, offset=offset, **conds)
            customs = [Custom.from_rldb_model(orm) for orm in custom_orms]
            return customs, error(ErrorCode.SUCCESS, "")
        except Exception as e:
            logging.error(f"Failed to list customs with conds {conds}: {e}")
            return [], error(ErrorCode.RLDB_ERROR, f"Failed to list custom data: {str(e)}")

# --- Singleton Pattern ---
custom_service = None

def init():
    """初始化 CustomService 单例"""
    global custom_service
    custom_service = CustomService()

def get_instance() -> CustomService:
    """获取 CustomService 单例"""
    return custom_service
