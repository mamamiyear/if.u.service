# -*- coding: utf-8 -*-
# created by mmmy on 2025-11-27

import json
import logging
from typing import Dict, List
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, func, Boolean
from utils.rldb import RLDBBaseModel
from utils.error import ErrorCode, error

class CustomRLDBModel(RLDBBaseModel):
    """
    客户数据的数据库模型 (SQLAlchemy Model) - 更新版
    """
    __tablename__ = 'customs'
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), index=True, nullable=False)
    
    # 基本信息
    name = Column(String(255), index=True, nullable=False)
    gender = Column(String(10), nullable=False)
    birth = Column(Integer, nullable=False) # 出生年份
    phone = Column(String(50), index=True)
    email = Column(String(255), index=True)
    
    # 外貌信息
    height = Column(Integer)
    weight = Column(Integer)
    images = Column(Text) # JSON string for list[str]
    scores = Column(Integer)
    
    # 学历职业
    degree = Column(String(255))
    academy = Column(String(255))
    occupation = Column(String(255))
    income = Column(Integer) # 单位：万
    assets = Column(Integer) # 单位：万
    current_assets = Column(Integer) # 单位：万
    house = Column(String(50))
    car = Column(String(50))
    
    # 户口家庭
    registered_city = Column(String(255))
    live_city = Column(String(255))
    native_place = Column(String(255))
    original_family = Column(Text)
    is_single_child = Column(Boolean, default=False)
    
    match_requirement = Column(Text)
    
    introductions = Column(Text) # JSON string for Dict[str, str]
    
    # 客户信息
    custom_level = Column(String(255))
    comments = Column(Text) # JSON string for Dict[str, str]
    is_public = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

class Custom:
    """
    客户数据的业务逻辑模型 (Business Logic Model) - 更新版
    """
    id: str
    user_id: str
    
    # 基本信息
    name: str
    gender: str
    birth: int
    phone: str
    email: str
    
    # 外貌信息
    height: int
    weight: int
    images: List[str]
    scores: int
    
    # 学历职业
    degree: str
    academy: str
    occupation: str
    income: int
    assets: int
    current_assets: int
    house: str
    car: str
    
    # 户口家庭
    registered_city: str
    live_city: str
    native_place: str
    original_family: str
    is_single_child: bool
    
    match_requirement: str
    
    introductions: Dict[str, str]
    
    # 客户信息
    custom_level: str
    comments: Dict[str, str]
    is_public: bool
    created_at: datetime = None

    def __init__(self, **kwargs):
        # 初始化所有属性
        self.id = kwargs.get('id', '')
        self.user_id = kwargs.get('user_id', '')
        self.name = kwargs.get('name', '')
        self.gender = kwargs.get('gender', '未知')
        self.birth = kwargs.get('birth', 0)
        self.phone = kwargs.get('phone', '')
        self.email = kwargs.get('email', '')
        self.height = kwargs.get('height', 0)
        self.weight = kwargs.get('weight', 0)
        self.images = kwargs.get('images', [])
        self.scores = kwargs.get('scores', 0)
        self.degree = kwargs.get('degree', '')
        self.academy = kwargs.get('academy', '')
        self.occupation = kwargs.get('occupation', '')
        self.income = kwargs.get('income', 0)
        self.assets = kwargs.get('assets', 0)
        self.current_assets = kwargs.get('current_assets', 0)
        self.house = kwargs.get('house', '')
        self.car = kwargs.get('car', '')
        self.registered_city = kwargs.get('registered_city', '')
        self.live_city = kwargs.get('live_city', '')
        self.native_place = kwargs.get('native_place', '')
        self.original_family = kwargs.get('original_family', '')
        self.is_single_child = kwargs.get('is_single_child', False)
        self.match_requirement = kwargs.get('match_requirement', '')
        self.introductions = kwargs.get('introductions', {})
        self.custom_level = kwargs.get('custom_level', '')
        self.comments = kwargs.get('comments', {})
        self.is_public = kwargs.get('is_public', False)
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
            'birth': self.birth,
            'phone': self.phone,
            'email': self.email,
            'height': self.height,
            'weight': self.weight,
            'images': self.images,
            'scores': self.scores,
            'degree': self.degree,
            'academy': self.academy,
            'occupation': self.occupation,
            'income': self.income,
            'assets': self.assets,
            'current_assets': self.current_assets,
            'house': self.house,
            'car': self.car,
            'registered_city': self.registered_city,
            'live_city': self.live_city,
            'native_place': self.native_place,
            'original_family': self.original_family,
            'is_single_child': self.is_single_child,
            'match_requirement': self.match_requirement,
            'introductions': self.introductions,
            'custom_level': self.custom_level,
            'comments': self.comments,
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
            birth=data.birth,
            phone=data.phone,
            email=data.email,
            height=data.height,
            weight=data.weight,
            images=json.loads(data.images) if data.images else [],
            scores=data.scores,
            degree=data.degree,
            academy=data.academy,
            occupation=data.occupation,
            income=data.income,
            assets=data.assets,
            house=data.house,
            car=data.car,
            registered_city=data.registered_city,
            live_city=data.live_city,
            native_place=data.native_place,
            original_family=data.original_family,
            is_single_child=data.is_single_child,
            match_requirement=data.match_requirement,
            introductions=json.loads(data.introductions) if data.introductions else {},
            custom_level=data.custom_level,
            comments=json.loads(data.comments) if data.comments else {},
            is_public=data.is_public,
            created_at=data.created_at,
        )

    def to_rldb_model(self) -> CustomRLDBModel:
        # 转换为数据库模型
        return CustomRLDBModel(
            id=self.id,
            user_id=self.user_id,
            name=self.name,
            gender=self.gender,
            birth=self.birth,
            phone=self.phone,
            email=self.email,
            height=self.height,
            weight=self.weight,
            images=json.dumps(self.images, ensure_ascii=False),
            scores=self.scores,
            degree=self.degree,
            academy=self.academy,
            occupation=self.occupation,
            income=self.income,
            assets=self.assets,
            current_assets=self.current_assets,
            house=self.house,
            car=self.car,
            registered_city=self.registered_city,
            live_city=self.live_city,
            native_place=self.native_place,
            original_family=self.original_family,
            is_single_child=self.is_single_child,
            match_requirement=self.match_requirement,
            introductions=json.dumps(self.introductions, ensure_ascii=False),
            custom_level=self.custom_level,
            comments=json.dumps(self.comments, ensure_ascii=False),
            is_public=self.is_public,
        )

    def validate(self) -> error:
        # 数据校验逻辑
        if not self.name:
            return error(ErrorCode.INVALID_PARAMS, "Name cannot be empty.")
            
        if not self.gender:
            return error(ErrorCode.INVALID_PARAMS, "Gender cannot be empty.")
            
        if self.gender not in ['男', '女']:
            return error(ErrorCode.INVALID_PARAMS, "Gender must be '男' or '女'.")
            
        current_year = datetime.now().year
        min_birth_year = 1950
        max_birth_year = current_year - 18
        
        if not isinstance(self.birth, int):
             return error(ErrorCode.INVALID_PARAMS, "Birth year must be an integer.")
        
        if self.birth < min_birth_year or self.birth > max_birth_year:
             return error(ErrorCode.INVALID_PARAMS, f"Birth year must be between {min_birth_year} and {max_birth_year}.")

        valid_houses = ["", "有房无贷", "有房有贷", "无自有房"]
        if self.house not in valid_houses:
            return error(ErrorCode.INVALID_PARAMS, f"House must be one of {valid_houses}")

        valid_cars = ["", "有车无贷", "有车有贷", "无自有车"]
        if self.car not in valid_cars:
            return error(ErrorCode.INVALID_PARAMS, f"Car must be one of {valid_cars}")

        # ... 可根据需要添加更多校验 ...
        return error(ErrorCode.SUCCESS, "")
