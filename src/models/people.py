# -*- coding: utf-8 -*-
# created by mmmy on 2025-09-30

import json
from typing import Dict
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from utils.rldb import RLDBBaseModel

class PeopleRLDBModel(RLDBBaseModel):
    __tablename__ = 'peoples'
    id = Column(String(36), primary_key=True)
    name = Column(String(255), index=True)
    contact = Column(String(255), index=True)
    gender = Column(String(10))
    age = Column(Integer)
    height = Column(Integer)
    marital_status = Column(String(20))
    match_requirement = Column(Text)
    introduction = Column(Text)
    comments = Column(Text)
    cover = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)


class People:
    # 数据库 ID
    id: str
    # 姓名
    name: str
    # 联系人
    contact: str
    # 性别
    gender: str
    # 年龄
    age: int
    # 身高(cm)
    height: int
    # 婚姻状况
    marital_status: str
    # 择偶要求
    match_requirement: str
    # 个人介绍
    introduction: Dict[str, str]
    # 总结评价
    comments: Dict[str, str]
    # 封面
    cover: str = None
    
    def __init__(self, **kwargs):
        # 初始化所有属性，从kwargs中获取值，如果不存在则设置默认值
        self.id = kwargs.get('id', '') if kwargs.get('id', '') is not None else ''
        self.name = kwargs.get('name', '') if kwargs.get('name', '') is not None else ''
        self.contact = kwargs.get('contact', '') if kwargs.get('contact', '') is not None else ''
        self.gender = kwargs.get('gender', '') if kwargs.get('gender', '') is not None else ''
        self.age = kwargs.get('age', 0) if kwargs.get('age', 0) is not None else 0
        self.height = kwargs.get('height', 0) if kwargs.get('height', 0) is not None else 0
        self.marital_status = kwargs.get('marital_status', '') if kwargs.get('marital_status', '') is not None else ''
        self.match_requirement = kwargs.get('match_requirement', '') if kwargs.get('match_requirement', '') is not None else ''
        self.introduction = kwargs.get('introduction', {}) if kwargs.get('introduction', {}) is not None else {}
        self.comments = kwargs.get('comments', {}) if kwargs.get('comments', {}) is not None else {}
        self.cover = kwargs.get('cover', None) if kwargs.get('cover', None) is not None else None

    def __str__(self) -> str:
        # 返回对象的字符串表示，包含所有属性
        return (f"People(id={self.id}, name={self.name}, contact={self.contact}, gender={self.gender}, "
                f"age={self.age}, height={self.height}, marital_status={self.marital_status}, "
                f"match_requirement={self.match_requirement}, introduction={self.introduction}, "
                f"comments={self.comments}, cover={self.cover})")

    @classmethod
    def from_dict(cls, data: dict):
        if 'created_at' in data:
            # 移除 created_at 字段，避免类型错误
            del data['created_at']
        if 'updated_at' in data:
            # 移除 updated_at 字段，避免类型错误
            del data['updated_at']
        if 'deleted_at' in data:
            # 移除 deleted_at 字段，避免类型错误
            del data['deleted_at']
        return cls(**data)

    @classmethod
    def from_rldb_model(cls, data: PeopleRLDBModel):
        # 将关系数据库模型转换为对象
        return cls(
            id=data.id,
            name=data.name,
            contact=data.contact,
            gender=data.gender,
            age=data.age,
            height=data.height,
            marital_status=data.marital_status,
            match_requirement=data.match_requirement,
            introduction=json.loads(data.introduction) if data.introduction else {},
            comments=json.loads(data.comments) if data.comments else {},
            cover=data.cover,
        )

    def to_dict(self) -> dict:
        # 将对象转换为字典格式
        return {
            'id': self.id,
            'name': self.name,
            'contact': self.contact,
            'gender': self.gender,
            'age': self.age,
            'height': self.height,
            'marital_status': self.marital_status,
            'match_requirement': self.match_requirement,
            'introduction': self.introduction,
            'comments': self.comments,
            'cover': self.cover,
        }      

    def to_rldb_model(self) -> PeopleRLDBModel:
        # 将对象转换为关系数据库模型
        return PeopleRLDBModel(
            id=self.id,
            name=self.name,
            contact=self.contact,
            gender=self.gender,
            age=self.age,
            height=self.height,
            marital_status=self.marital_status,
            match_requirement=self.match_requirement,
            introduction=json.dumps(self.introduction, ensure_ascii=False),
            comments=json.dumps(self.comments, ensure_ascii=False),
            cover=self.cover,
        )