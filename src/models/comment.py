# -*- coding: utf-8 -*-
# created by mmmy on 2025-12-23

from datetime import datetime
from typing import Optional
import uuid


class Comment:
    id: str
    user_id: str
    content: str
    created_at: datetime
    updated_at: datetime

    def __init__(self, **kwargs):
        # 兼容 author 字段，统一映射到 user_id
        self.id = kwargs.get('id', uuid.uuid4().hex)
        self.user_id = kwargs.get('user_id', kwargs.get('author', ''))
        self.content = kwargs.get('content', '')
        self.created_at = kwargs.get('created_at', datetime.now())
        self.updated_at = kwargs.get('updated_at', datetime.now())

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'content': self.content,
            'created_at': int(self.created_at.timestamp()) if self.created_at else None,
            'updated_at': int(self.updated_at.timestamp()) if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict):
        if 'created_at' in data and isinstance(data['created_at'], (int, float)):
            data['created_at'] = datetime.fromtimestamp(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], (int, float)):
            data['updated_at'] = datetime.fromtimestamp(data['updated_at'])
        return cls(**data)
