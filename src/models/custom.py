# -*- coding: utf-8 -*-
# created by mmmy on 2025-11-27

import json
import logging
from typing import Dict
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from utils.rldb import RLDBBaseModel
from utils.error import ErrorCode, error

class CustomRLDBModel(RLDBBaseModel):
    """
    客户数据的数据库模型 (SQLAlchemy Model)
    """
    __tablename__ = 'customs'
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), index=True, nullable=False)
    name = Column(String(255), index=True)
    gender = Column(String(10))
    birth_year = Column(Integer)
    height = Column(Integer)
    annual_income = Column(Integer) # 单位：万
    net_worth = Column(Integer) # 单位：万
    introduction = Column(Text) # JSON string for map[string]string
    match_requirement = Column(Text)
    comments = Column(Text) # JSON string for map[string]string
    level = Column(String(255))
    portrait = Column(Text) # JSON string for map[string]string
    progress_details = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

class Custom:
    """
    客户数据的业务逻辑模型 (Business Logic Model)
    """
    id: str
    user_id: str
    name: str
    gender: str
    birth_year: int
    height: int
    annual_income: int
    net_worth: int
    introduction: Dict[str, str]
    match_requirement: str
    comments: Dict[str, str]
    level: str
    portrait: Dict[str, str]
    progress_details: str
    created_at: datetime = None

    def __init__(self, **kwargs):
        # 初始化所有属性
        self.id = kwargs.get('id', '')
        self.user_id = kwargs.get('user_id', '')
        self.name = kwargs.get('name', '')
        self.gender = kwargs.get('gender', '未知')
        self.birth_year = kwargs.get('birth_year', 0)
        self.height = kwargs.get('height', 0)
        self.annual_income = kwargs.get('annual_income', 0)
        self.net_worth = kwargs.get('net_worth', 0)
        self.introduction = kwargs.get('introduction', {})
        self.match_requirement = kwargs.get('match_requirement', '')
        self.comments = kwargs.get('comments', {})
        self.level = kwargs.get('level', '')
        self.portrait = kwargs.get('portrait', {})
        self.progress_details = kwargs.get('progress_details', '')
        self.created_at = kwargs.get('created_at')

    def __str__(self) -> str:
        # 返回对象的字符串表示
        attributes = ", ".join(f"{k}={v}" for k, v in self.to_dict().items())
        return f"Custom({attributes})"

    @classmethod
    def from_dict(cls, data: dict):
        # 从字典创建对象实例
        if 'created_at' in data and data['created_at'] is not None:
            data['created_at'] = datetime.fromtimestamp(data['created_at'])
        # 移除ORM特有的时间戳，避免初始化错误
        data.pop('updated_at', None)
        data.pop('deleted_at', None)
        return cls(**data)

    def to_dict(self) -> dict:
        # 将对象转换为字典
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'gender': self.gender,
            'birth_year': self.birth_year,
            'height': self.height,
            'annual_income': self.annual_income,
            'net_worth': self.net_worth,
            'introduction': self.introduction,
            'match_requirement': self.match_requirement,
            'comments': self.comments,
            'level': self.level,
            'portrait': self.portrait,
            'progress_details': self.progress_details,
            'created_at': int(self.created_at.timestamp()) if self.created_at else None,
        }

    @classmethod
    def from_rldb_model(cls, data: CustomRLDBModel):
        # 从数据库模型转换
        return cls(
            id=data.id,
            user_id=data.user_id,
            name=data.name,
            gender=data.gender,
            birth_year=data.birth_year,
            height=data.height,
            annual_income=data.annual_income,
            net_worth=data.net_worth,
            introduction=json.loads(data.introduction) if data.introduction else {},
            match_requirement=data.match_requirement,
            comments=json.loads(data.comments) if data.comments else {},
            level=data.level,
            portrait=json.loads(data.portrait) if data.portrait else {},
            progress_details=data.progress_details,
            created_at=data.created_at,
        )

    def to_rldb_model(self) -> CustomRLDBModel:
        # 转换为数据库模型
        return CustomRLDBModel(
            id=self.id,
            user_id=self.user_id,
            name=self.name,
            gender=self.gender,
            birth_year=self.birth_year,
            height=self.height,
            annual_income=self.annual_income,
            net_worth=self.net_worth,
            introduction=json.dumps(self.introduction, ensure_ascii=False),
            match_requirement=self.match_requirement,
            comments=json.dumps(self.comments, ensure_ascii=False),
            level=self.level,
            portrait=json.dumps(self.portrait, ensure_ascii=False),
            progress_details=self.progress_details,
        )

    def validate(self) -> error:
        # 数据校验逻辑
        if not self.name:
            logging.warning("Custom's name is missing, using default empty string.")
            self.name = ""
        if self.gender not in ['男', '女', '未知']:
            logging.warning(f"Invalid gender: {self.gender}. Defaulting to '未知'.")
            self.gender = "未知"
        if not isinstance(self.birth_year, int) or self.birth_year < 0:
            logging.warning(f"Invalid birth_year: {self.birth_year}. Defaulting to 0.")
            self.birth_year = 0
        # ... 可根据需要添加更多校验 ...
        return error(ErrorCode.SUCCESS, "")
