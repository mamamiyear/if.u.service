# -*- coding: utf-8 -*-
# created by mmmy on 2025-09-30

import logging
from typing import Dict, List

from overrides import override

from utils.kwdb import KWDBBaseModel
from utils.rldb import RLDBBaseModel
from utils.vsdb import VSDBBaseModel

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
    pass

class PeopleVSDBModel(VSDBBaseModel):
    __collection__ = 'peoples'
    name: str
    gender: str
    age: int
    height: int
    marital_status: str
    document: str
    _distance: float = None
    
    @override
    def __meta__(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'gender': self.gender,
            'age': self.age,
            'height': self.height,
            'marital_status': self.marital_status,
            'created_at': self.created_at,
            'updaate_at': self.updated_at,
        }

    @override
    def __docs__(self) -> str:
        return self.document

    @override
    def set_document(self, document: str):
        self.document = document
    
    @override
    def set_metadata(self, metadata: dict):
        self.name = metadata.get('name', '')
        self.gender = metadata.get('gender', '')
        self.age = metadata.get('age', 0)
        self.height = metadata.get('height', 0)
        self.marital_status = metadata.get('marital_status', '')
    
    @override
    def set_distance(self, distance: float):
        self._distance = distance


class PeopleKWDBModel(KWDBBaseModel):
    __indexname__ = 'peoples'
    document: str
    tag_list: List[str]

    @override
    def content(self) -> str:
        return self.document

    @override
    def tags(self) -> List[str]:
        return self.tag_list



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

    def to_vs_meta(self) -> Dict[str, str]:
        # 返回对象的向量数据库元数据信息
        meta = {
            'id': self.id,
            'name': self.name,
            'gender': self.gender,
            'age': self.age,
            'height': self.height,
            'marital_status': self.marital_status,
        }
        logging.info(f"people meta for vsdb: {meta}")
        return meta

    def to_vs_text(self) -> str:
        # 将对象转换为向量数据库文档格式的字符串
        doc = []
        doc.append(f"姓名: {self.name}")
        doc.append(f"性别: {self.gender}")
        if self.age:
            doc.append(f"年龄: {self.age}")
        if self.height:
            doc.append(f"身高: {self.height}cm")
        if self.marital_status:
            doc.append(f"婚姻状况: {self.marital_status}")
        if self.match_requirement:
            doc.append(f"择偶要求: {self.match_requirement}")
        result = ', '.join(doc)
        result += '。个人介绍: '
        doc = []
        if self.introduction:
            for key, value in self.introduction.items():
                doc.append(f"**{key}: {value}**")
        result += ', '.join(doc)
        result += '。'
        return result

    def to_kw_text(self) -> str:
        # 将对象转换为关键词数据库文档格式的字符串
        doc = []
        doc.append(f"姓名: {self.name}")
        doc.append(f"性别: {self.gender}")
        if self.age:
            doc.append(f"年龄: {self.age}")
        if self.height:
            doc.append(f"身高: {self.height}cm")
        if self.marital_status:
            doc.append(f"婚姻状况: {self.marital_status}")
        if self.match_requirement:
            doc.append(f"择偶要求: {self.match_requirement}")
        if self.introduction:
            doc.append("个人介绍:")
            for key, value in self.introduction.items():
                doc.append(f" - {key}: {value}")
        tags = self.to_kw_tags()
        doc.append(f" {','.join(tags)}")
        return ' '.join(doc)
    
    def to_kw_tags(self) -> list[str]:
        # 将对象的标签转换为关键词数据库标签格式的列表
        tags = []
        if "男" in self.gender:
            tags.extend(["男", "男性", "男生", "男的"])
        if "女" in self.gender:
            tags.extend(["女", "女性", "女生", "女的"])
        return tags

    def to_rl_model(self) -> PeopleRLDBModel:
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
            introduction=self.introduction,
            comments=self.comments,
            cover=self.cover,
        )
    
    def from_rl_model(self, model: PeopleRLDBModel):
        # 从关系型数据库模型转换为对象
        self.id = model.id
        self.name = model.name
        self.contact = model.contact
        self.gender = model.gender
        self.age = model.age
        self.height = model.height
        self.marital_status = model.marital_status
        self.match_requirement = model.match_requirement
        self.introduction = model.introduction
        self.comments = model.comments
        self.cover = model.cover

    def to_vs_model(self) -> PeopleVSDBModel:
        # 将对象转换为向量数据库模型
        return PeopleVSDBModel(
            id=self.id,
            name=self.name,
            gender=self.gender,
            age=self.age,
            height=self.height,
            marital_status=self.marital_status,
            document=self.to_vs_text(),
        )

    def to_kw_model(self) -> PeopleKWDBModel:
        # 将对象转换为关键词数据库模型
        return PeopleKWDBModel(
            id=self.id,
            name=self.name,
            document=self.to_kw_text(),
            tag_list=self.to_kw_tags(),
        )

    def comment(self, comment: Dict[str, str]):
        # 添加总结评价
        self.comments.update(comment)

