from typing import Tuple, List, Optional
from utils.error import ErrorCode, error
from models.user import User, UserRLDBModel
from utils import rldb as rldb_util

def check_permission(request_user_id: str, request_user_org_id: str, resource_owner_id: str) -> Tuple[bool, error]:
    """
    Check if the user has permission to access the resource.
    
    Args:
        request_user_id: The ID of the user making the request
        request_user_org_id: The organization ID of the user making the request (can be empty)
        resource_owner_id: The ID of the user who owns the resource
        
    Returns:
        Tuple[bool, error]: (is_allowed, error_object)
    """
    # 1. Check if the user is the owner
    if request_user_id == resource_owner_id:
        return True, error(ErrorCode.SUCCESS, "success")
        
    # 2. Check organization membership if resource is not owned by user
    if request_user_org_id:
        # We need to fetch the resource owner to check their organization
        # Optimization: We could pass the resource owner's org_id if available, 
        # but typically we only have the owner_id from the resource itself.
        # Since this helper is called after fetching the resource, we might want to 
        # consider passing the owner object or owner's org_id if performance is critical.
        # For now, we'll query the owner's details.
        
        db = rldb_util.get_instance()
        owner_orm = db.get(UserRLDBModel, resource_owner_id)
        if not owner_orm:
            # If owner doesn't exist (shouldn't happen for valid resources), deny access
            return False, error(ErrorCode.MODEL_ERROR, "resource owner not found")
            
        owner_org_id = getattr(owner_orm, 'org_id', '')
        
        # If both users belong to the same organization, allow access
        if owner_org_id and owner_org_id == request_user_org_id:
            return True, error(ErrorCode.SUCCESS, "success")
            
    return False, error(ErrorCode.MODEL_ERROR, "permission denied")

def get_visible_user_ids(user_id: str, org_id: str) -> Tuple[List[str], error]:
    """
    Get a list of user IDs whose resources are visible to the current user.
    
    Args:
        user_id: The current user's ID
        org_id: The current user's organization ID
        
    Returns:
        Tuple[List[str], error]: (list_of_user_ids, error_object)
    """
    # Always include the user themselves
    user_ids = [user_id]
    
    # If user belongs to an organization, include all other members of that organization
    if org_id:
        db = rldb_util.get_instance()
        # Query all users with the same org_id
        org_members = db.query(UserRLDBModel, org_id=org_id)
        for member in org_members:
            if member.id != user_id:
                user_ids.append(member.id)
                
    return user_ids, error(ErrorCode.SUCCESS, "success")
