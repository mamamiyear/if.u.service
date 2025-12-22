# -*- coding: utf-8 -*-
# created by mmmy on 2025-11-27

import logging
import uuid
from typing import List
from datetime import datetime
from models.custom import Custom, CustomRLDBModel
from models.comment import Comment
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

    def add_comment(self, custom_id: str, content: str, user_id: str) -> (Comment, error):
        """
        新增评论
        
        :param custom_id: 客户ID
        :param content: 评论内容
        :param user_id: 评论人ID
        :return: Comment对象 和 错误对象
        """
        custom, err = self.get(custom_id)
        if not err.success:
            return None, err
        
        comment = Comment(
            id=uuid.uuid4().hex,
            content=content,
            user_id=user_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        custom.comments.append(comment)
        
        _, err = self.save(custom)
        if not err.success:
            return None, err
            
        return comment, error(ErrorCode.SUCCESS, "")

    def update_comment(self, custom_id: str, comment_id: str, content: str, user_id: str) -> error:
        """
        更新评论
        
        :param custom_id: 客户ID
        :param comment_id: 评论ID
        :param content: 新的评论内容
        :param user_id: 操作人ID（必须是评论创建人）
        :return: 错误对象
        """
        custom, err = self.get(custom_id)
        if not err.success:
            return err
            
        target_comment = None
        for comment in custom.comments:
            if comment.id == comment_id:
                target_comment = comment
                break
        
        if not target_comment:
            return error(ErrorCode.MODEL_NOT_FOUND, f"Comment {comment_id} not found")
            
        if target_comment.user_id != user_id:
            return error(ErrorCode.PERMISSION_DENIED, "Permission denied: only author can update comment")
            
        target_comment.content = content
        target_comment.updated_at = datetime.now()
        
        _, err = self.save(custom)
        return err

    def delete_comment(self, custom_id: str, comment_id: str, user_id: str) -> error:
        """
        删除评论
        
        :param custom_id: 客户ID
        :param comment_id: 评论ID
        :param user_id: 操作人ID（必须是评论创建人）
        :return: 错误对象
        """
        custom, err = self.get(custom_id)
        if not err.success:
            return err
            
        target_index = -1
        for i, comment in enumerate(custom.comments):
            if comment.id == comment_id:
                if comment.user_id != user_id:
                    return error(ErrorCode.PERMISSION_DENIED, "Permission denied: only author can delete comment")
                target_index = i
                break
        
        if target_index == -1:
            return error(ErrorCode.MODEL_NOT_FOUND, f"Comment {comment_id} not found")
            
        custom.comments.pop(target_index)
        
        _, err = self.save(custom)
        return err

    def get_comments(self, custom_id: str) -> (List[Comment], error):
        """
        获取所有评论
        
        :param custom_id: 客户ID
        :return: 评论列表 和 错误对象
        """
        custom, err = self.get(custom_id)
        if not err.success:
            return [], err
            
        return custom.comments, error(ErrorCode.SUCCESS, "")

# --- Singleton Pattern ---
custom_service = None

def init():
    """初始化 CustomService 单例"""
    global custom_service
    custom_service = CustomService()

def get_instance() -> CustomService:
    """获取 CustomService 单例"""
    return custom_service
