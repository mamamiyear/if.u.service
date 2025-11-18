from typing import Optional
import json
from datetime import datetime, timedelta
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, func, UniqueConstraint
from utils.rldb import RLDBBaseModel
from utils.error import ErrorCode, error


class UserRLDBModel(RLDBBaseModel):
    __tablename__ = 'users'
    id = Column(String(36), primary_key=True)
    nickname = Column(String(255))
    avatar_link = Column(String(255))
    email = Column(String(127), unique=True, index=True)
    phone = Column(String(32), unique=True, index=True)
    password_hash = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)


class VerificationCodeRLDBModel(RLDBBaseModel):
    __tablename__ = 'verification_codes'
    id = Column(String(36), primary_key=True)
    target_type = Column(String(16))
    target = Column(String(255), index=True)
    code = Column(String(16))
    scene = Column(String(32))
    expires_at = Column(DateTime(timezone=True))
    used_at = Column(DateTime(timezone=True), nullable=True)


class UserTokenRLDBModel(RLDBBaseModel):
    __tablename__ = 'user_tokens'
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), index=True)
    token = Column(Text)
    expired_at = Column(DateTime(timezone=True))
    revoked = Column(Boolean, default=False)


class User:
    id: str
    nickname: str
    avatar_link: str
    email: str
    phone: str
    password_hash: str
    created_at: datetime = None

    def __init__(self, **kwargs):
        self.id = kwargs.get('id', '') if kwargs.get('id', '') is not None else ''
        self.nickname = kwargs.get('nickname', '') if kwargs.get('nickname', '') is not None else ''
        self.avatar_link = kwargs.get('avatar_link', '') if kwargs.get('avatar_link', '') is not None else ''
        self.email = kwargs.get('email', '') if kwargs.get('email', '') is not None else ''
        self.phone = kwargs.get('phone', '') if kwargs.get('phone', '') is not None else ''
        self.password_hash = kwargs.get('password_hash', '') if kwargs.get('password_hash', '') is not None else ''
        self.created_at = kwargs.get('created_at', None)

    def __str__(self) -> str:
        return (f"User(id={self.id}, nickname={self.nickname}, avatar_link={self.avatar_link}, "
                f"email={self.email}, phone={self.phone}, created_at={self.created_at})")

    @classmethod
    def from_dict(cls, data: dict):
        if 'updated_at' in data:
            del data['updated_at']
        if 'deleted_at' in data:
            del data['deleted_at']
        return cls(**data)

    @classmethod
    def from_rldb_model(cls, data: UserRLDBModel):
        return cls(
            id=data.id,
            nickname=data.nickname,
            avatar_link=data.avatar_link,
            email=data.email,
            phone=data.phone,
            password_hash=data.password_hash,
            created_at=data.created_at,
        )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'nickname': self.nickname,
            'avatar_link': self.avatar_link,
            'email': self.email,
            'phone': self.phone,
            'created_at': int(self.created_at.timestamp()) if self.created_at else None,
        }

    def to_rldb_model(self) -> UserRLDBModel:
        return UserRLDBModel(
            id=self.id,
            nickname=self.nickname,
            avatar_link=self.avatar_link,
            email=self.email,
            phone=self.phone,
            password_hash=self.password_hash,
        )

    def validate(self) -> error:
        err = error(ErrorCode.SUCCESS, "")
        if not self.email and not self.phone:
            return error(ErrorCode.MODEL_ERROR, "email or phone required")
        return err


class VerificationCode:
    id: str
    target_type: str
    target: str
    code: str
    scene: str
    expires_at: datetime
    used_at: Optional[datetime] = None

    def __init__(self, **kwargs):
        self.id = kwargs.get('id', '') if kwargs.get('id', '') is not None else ''
        self.target_type = kwargs.get('target_type', '')
        self.target = kwargs.get('target', '')
        self.code = kwargs.get('code', '')
        self.scene = kwargs.get('scene', '')
        self.expires_at = kwargs.get('expires_at')
        self.used_at = kwargs.get('used_at', None)

    @classmethod
    def from_rldb_model(cls, data: VerificationCodeRLDBModel):
        return cls(
            id=data.id,
            target_type=data.target_type,
            target=data.target,
            code=data.code,
            scene=data.scene,
            expires_at=data.expires_at,
            used_at=data.used_at,
        )

    def to_rldb_model(self) -> VerificationCodeRLDBModel:
        return VerificationCodeRLDBModel(
            id=self.id,
            target_type=self.target_type,
            target=self.target,
            code=self.code,
            scene=self.scene,
            expires_at=self.expires_at,
            used_at=self.used_at,
        )


class UserToken:
    id: str
    user_id: str
    token: str
    expired_at: datetime
    revoked: bool

    def __init__(self, **kwargs):
        self.id = kwargs.get('id', '') if kwargs.get('id', '') is not None else ''
        self.user_id = kwargs.get('user_id', '')
        self.token = kwargs.get('token', '')
        self.expired_at = kwargs.get('expired_at')
        self.revoked = kwargs.get('revoked', False)

    @classmethod
    def from_rldb_model(cls, data: UserTokenRLDBModel):
        return cls(
            id=data.id,
            user_id=data.user_id,
            token=data.token,
            expired_at=data.expired_at,
            revoked=data.revoked,
        )

    def to_rldb_model(self) -> UserTokenRLDBModel:
        return UserTokenRLDBModel(
            id=self.id,
            user_id=self.user_id,
            token=self.token,
            expired_at=self.expired_at,
            revoked=self.revoked,
        )