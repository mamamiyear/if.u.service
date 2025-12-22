from typing import Optional
from datetime import datetime
from sqlalchemy import Column, String, DateTime, func
from utils.rldb import RLDBBaseModel
from utils.error import ErrorCode, error


class OrganizationRLDBModel(RLDBBaseModel):
    __tablename__ = 'organizations'
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    logo = Column(String(255))
    plan = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)


class Organization:
    id: str
    name: str
    logo: str
    plan: str
    created_at: datetime = None

    def __init__(self, **kwargs):
        self.id = kwargs.get('id', '') if kwargs.get('id', '') is not None else ''
        self.name = kwargs.get('name', '') if kwargs.get('name', '') is not None else ''
        self.logo = kwargs.get('logo', '') if kwargs.get('logo', '') is not None else ''
        self.plan = kwargs.get('plan', '') if kwargs.get('plan', '') is not None else ''
        self.created_at = kwargs.get('created_at', None)

    def __str__(self) -> str:
        return (f"Organization(id={self.id}, name={self.name}, logo={self.logo}, "
                f"plan={self.plan}, created_at={self.created_at})")

    @classmethod
    def from_dict(cls, data: dict):
        if 'updated_at' in data:
            del data['updated_at']
        if 'deleted_at' in data:
            del data['deleted_at']
        return cls(**data)

    @classmethod
    def from_rldb_model(cls, data: OrganizationRLDBModel):
        return cls(
            id=data.id,
            name=data.name,
            logo=data.logo,
            plan=data.plan,
            created_at=data.created_at,
        )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'logo': self.logo,
            'plan': self.plan,
            'created_at': int(self.created_at.timestamp()) if self.created_at else None,
        }

    def to_rldb_model(self) -> OrganizationRLDBModel:
        return OrganizationRLDBModel(
            id=self.id,
            name=self.name,
            logo=self.logo,
            plan=self.plan,
        )

    def validate(self) -> error:
        err = error(ErrorCode.SUCCESS, "")
        if not self.name:
            return error(ErrorCode.MODEL_ERROR, "name required")
        return err
