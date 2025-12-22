# -*- coding: utf-8 -*-
import logging
import uuid
from typing import List, Tuple
from models.organization import Organization, OrganizationRLDBModel
from utils.error import ErrorCode, error
from utils import rldb

class OrganizationService:
    def __init__(self):
        self.rldb = rldb.get_instance()

    def save(self, org: Organization) -> Tuple[str, error]:
        """
        保存组织到数据库。
        如果 org.id 存在，则更新；否则，创建。
        """
        # Validate
        err = org.validate()
        if not err.success:
            return "", err

        # Generate ID if not present
        if not org.id:
            org.id = uuid.uuid4().hex
        
        try:
            org_orm = org.to_rldb_model()
            self.rldb.upsert(org_orm)
            return org.id, error(ErrorCode.SUCCESS, "")
        except Exception as e:
            logging.error(f"Failed to save organization {org.id}: {e}")
            return "", error(ErrorCode.RLDB_ERROR, f"Failed to save organization data: {str(e)}")

    def delete(self, org_id: str) -> error:
        try:
            org_orm = self.rldb.get(OrganizationRLDBModel, org_id)
            if not org_orm:
                return error(ErrorCode.RLDB_NOT_FOUND, f"Organization {org_id} not found.")
            self.rldb.delete(org_orm)
            return error(ErrorCode.SUCCESS, "")
        except Exception as e:
            logging.error(f"Failed to delete organization {org_id}: {e}")
            return error(ErrorCode.RLDB_ERROR, f"Failed to delete organization data: {str(e)}")

    def get(self, org_id: str) -> Tuple[Organization, error]:
        try:
            org_orm = self.rldb.get(OrganizationRLDBModel, org_id)
            if not org_orm:
                return None, error(ErrorCode.RLDB_NOT_FOUND, f"Organization {org_id} not found.")
            
            return Organization.from_rldb_model(org_orm), error(ErrorCode.SUCCESS, "")
        except Exception as e:
            logging.error(f"Failed to get organization {org_id}: {e}")
            return None, error(ErrorCode.RLDB_ERROR, f"Failed to retrieve organization data: {str(e)}")

    def list(self, conds: dict = None, limit: int = 10, offset: int = 0) -> Tuple[List[Organization], error]:
        if conds is None:
            conds = {}
        try:
            org_orms = self.rldb.query(OrganizationRLDBModel, limit=limit, offset=offset, **conds)
            orgs = [Organization.from_rldb_model(orm) for orm in org_orms]
            return orgs, error(ErrorCode.SUCCESS, "")
        except Exception as e:
            logging.error(f"Failed to list organizations with conds {conds}: {e}")
            return [], error(ErrorCode.RLDB_ERROR, f"Failed to list organization data: {str(e)}")

# --- Singleton Pattern ---
organization_service = None

def init():
    global organization_service
    organization_service = OrganizationService()

def get_instance() -> OrganizationService:
    return organization_service
