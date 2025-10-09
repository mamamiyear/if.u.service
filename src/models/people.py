# -*- coding: utf-8 -*-
# created by mmmy on 2025-09-30

import logging
from typing import Dict


class People:
    # 数据库 ID
    id: str
    # 姓名
    name: str
    # 性别
    gender: str
    # 年龄
    age: int
    # 身高(cm)
    height: int
    # 体重(kg)
    # weight: int
    # 婚姻状况
    # [
    #   "未婚(single)",
    #   "已婚(married)",
    #   "离异(divorced)",
    #   "丧偶(widowed)"
    # ]
    marital_status: str
    # 择偶要求
    match_requirement: str
    # 个人介绍
    introduction: Dict[str, str]
    # 总结评价
    comments: Dict[str, str]
    

    def __init__(self, **kwargs):
        # 初始化所有属性，从kwargs中获取值，如果不存在则设置默认值
        self.id = kwargs.get('id', '') if kwargs.get('id', '') is not None else ''
        self.name = kwargs.get('name', '') if kwargs.get('name', '') is not None else ''
        self.gender = kwargs.get('gender', '') if kwargs.get('gender', '') is not None else ''
        self.age = kwargs.get('age', 0) if kwargs.get('age', 0) is not None else 0
        self.height = kwargs.get('height', 0) if kwargs.get('height', 0) is not None else 0
        # self.weight = kwargs.get('weight', 0) if kwargs.get('weight', 0) is not None else 0
        self.marital_status = kwargs.get('marital_status', '') if kwargs.get('marital_status', '') is not None else ''
        self.match_requirement = kwargs.get('match_requirement', '') if kwargs.get('match_requirement', '') is not None else ''
        self.introduction = kwargs.get('introduction', {}) if kwargs.get('introduction', {}) is not None else {}
        self.comments = kwargs.get('comments', {}) if kwargs.get('comments', {}) is not None else {}

    def __str__(self) -> str:
        return self.tonl()

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

    def to_dict(self) -> dict:
        # 将对象转换为字典格式
        return {
            'id': self.id,
            'name': self.name,
            'gender': self.gender,
            'age': self.age,
            'height': self.height,
            # 'weight': self.weight,
            'marital_status': self.marital_status,
            'match_requirement': self.match_requirement,
            'introduction': self.introduction,
            'comments': self.comments,
        }
    
    def meta(self) -> Dict[str, str]:
        # 返回对象的元数据信息
        meta = {
            'id': self.id,
            'name': self.name,
            'gender': self.gender,
            'age': self.age,
            'height': self.height,
            # 'weight': self.weight,
            'marital_status': self.marital_status,
            # 'match_requirement': self.match_requirement,
        }
        logging.info(f"people meta: {meta}")
        return meta

    def tonl(self) -> str:
        # 将对象转换为文档格式的字符串
        doc = []
        doc.append(f"姓名: {self.name}")
        doc.append(f"性别: {self.gender}")
        if self.age:
            doc.append(f"年龄: {self.age}")
        if self.height:
            doc.append(f"身高: {self.height}cm")
        # if self.weight:
            # doc.append(f"体重: {self.weight}kg")
        if self.marital_status:
            doc.append(f"婚姻状况: {self.marital_status}")
        if self.match_requirement:
            doc.append(f"择偶要求: {self.match_requirement}")
        if self.introduction:
            doc.append("个人介绍:")
            for key, value in self.introduction.items():
                doc.append(f" - {key}: {value}")
        if self.comments:
            doc.append("总结评价:")
            for key, value in self.comments.items():
                doc.append(f" - {key}: {value}")
        return '\n'.join(doc)

    def comment(self, comment: Dict[str, str]):
        # 添加总结评价
        self.comments.update(comment)
