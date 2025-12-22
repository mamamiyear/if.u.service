from typing import Optional
from fastapi import Cookie, HTTPException, Request
from utils import rldb as rldb_util
from models.user import User, UserTokenRLDBModel, UserRLDBModel
from datetime import datetime


def require_auth(request: Request, token: Optional[str] = Cookie(None)):
    if not token:
        raise HTTPException(status_code=401, detail="unauthorized")
    db = rldb_util.get_instance()
    tokens = db.query(UserTokenRLDBModel, token=token, limit=1)
    if not tokens:
        raise HTTPException(status_code=401, detail="unauthorized")
    t = tokens[0]
    if getattr(t, 'revoked', False):
        raise HTTPException(status_code=401, detail="unauthorized")
    if getattr(t, 'expired_at', None) and t.expired_at < datetime.now():
        raise HTTPException(status_code=401, detail="unauthorized")
    user_orm = db.get(UserRLDBModel, t.user_id)
    if not user_orm:
        raise HTTPException(status_code=401, detail="unauthorized")
    user = User.from_rldb_model(user_orm)
    request.state.user_id = user.id
    request.state.user_nickname = user.nickname
    request.state.user_email = user.email
    request.state.user_phone = user.phone
    request.state.user_org_id = user.org_id
    request.state.user_org_role = user.org_role
    request.state.token = token