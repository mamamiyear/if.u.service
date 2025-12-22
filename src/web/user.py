import os
import time
import logging
from typing import Optional, Literal
from fastapi import APIRouter, Depends, Request, HTTPException, Response, UploadFile, File
from pydantic import BaseModel
from services.user import get_instance as get_user_service
from services.organization import get_instance as get_organization_service
from web.auth import require_auth
from utils import obs
from utils.config import get_instance as get_config
from web.schemas import BaseResponse

router = APIRouter(tags=["user"])

class SendCodeRequest(BaseModel):
    target_type: str
    target: str
    scene: Literal['register', 'update']
    # scene: Literal['register', 'login']


@router.post("/api/user/send_code")
async def send_user_code(request: SendCodeRequest):
    service = get_user_service()
    err = service.send_code(request.target_type, request.target, request.scene)
    if not err.success:
        raise HTTPException(status_code=400, detail=err.info)
    return BaseResponse(error_code=0, error_info="success")


class RegisterRequest(BaseModel):
    nickname: Optional[str] = None
    avatar_link: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    password: str
    code: str

@router.post("/api/user")
async def user_register(request: RegisterRequest):
    service = get_user_service()
    from models.user import User
    u = User(
        nickname=request.nickname or "",
        avatar_link=request.avatar_link or "",
        email=request.email or "",
        phone=request.phone or "",
        password_hash=request.password,
        # 以下为临时方案
        org_id="03387b86d58842e390823080d22fec38",
        org_role="staff",
    )
    uid, err = service.register(u, request.code)
    if not err.success:
        logging.error(f"register failed: {err}")
        raise HTTPException(status_code=400, detail=err.info)
    return BaseResponse(error_code=0, error_info="success", data=uid)


class LoginRequest(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    password: str

@router.post("/api/user/login")
async def user_login(request: LoginRequest, response: Response):
    service = get_user_service()
    data, err = service.login(request.email, request.phone, request.password)
    if not err.success:
        raise HTTPException(status_code=400, detail=err.info)
    conf = get_config()
    ttl_days = conf.getint('auth', 'token_ttl_days', fallback=30)
    cookie_domain = conf.get('auth', 'cookie_domain', fallback=None)
    cookie_secure = conf.getboolean('auth', 'cookie_secure', fallback=False)
    cookie_samesite = conf.get('auth', 'cookie_samesite', fallback=None)
    response.set_cookie(
        key="token",
        value=data.get('token', ''),
        max_age=ttl_days * 24 * 3600,
        httponly=True,
        secure=cookie_secure,
        samesite=cookie_samesite,
        domain=cookie_domain,
        path="/",
    )
    return BaseResponse(error_code=0, error_info="success", data={"expired_at": data.get('expired_at')})


@router.delete("/api/user/me/login", dependencies=[Depends(require_auth)])
async def user_logout(response: Response, request: Request):
    service = get_user_service()
    err = service.logout(getattr(request.state, 'token', None))
    if not err.success:
        raise HTTPException(status_code=400, detail=err.info)
    conf = get_config()
    cookie_domain = conf.get('auth', 'cookie_domain', fallback=None)
    response.delete_cookie(key="token", domain=cookie_domain, path="/")
    return BaseResponse(error_code=0, error_info="success")


@router.delete("/api/user/me", dependencies=[Depends(require_auth)])
async def user_delete(response: Response, request: Request):
    service = get_user_service()
    err = service.delete_user(getattr(request.state, 'user_id', None))
    if not err.success:
        raise HTTPException(status_code=400, detail=err.info)
    conf = get_config()
    cookie_domain = conf.get('auth', 'cookie_domain', fallback=None)
    response.delete_cookie(key="token", domain=cookie_domain, path="/")
    return BaseResponse(error_code=0, error_info="success")

@router.get("/api/user/me", dependencies=[Depends(require_auth)])
async def user_me(request: Request):
    service = get_user_service()
    user, err = service.get(getattr(request.state, 'user_id', None))
    if not err.success or not user:
        raise HTTPException(status_code=400, detail=err.info)
    data = {
        'id': user.id,
        'nickname': user.nickname,
        'avatar_link': user.avatar_link,
        'phone': user.phone,
        'email': user.email,
    }
    if user.org_id:
        # 查询组织信息
        org_service = get_organization_service()
        org, err = org_service.get(user.org_id)
        if not err.success or not org:
            raise HTTPException(status_code=400, detail=err.info)
        data['organization'] = {
            'id': org.id,
            'name': org.name,
            'logo': org.logo,
            'role': user.org_role,
        }
    return BaseResponse(error_code=0, error_info="success", data=data)


@router.get("/api/user/{user_id}", dependencies=[Depends(require_auth)])
async def get_other_user_info(user_id: str, request: Request):
    service = get_user_service()
    target_user, err = service.get(user_id)
    if not err.success or not target_user:
        raise HTTPException(status_code=404, detail="user not found")

    current_user_org_id = getattr(request.state, 'user_org_id', None)

    if target_user.org_id != current_user_org_id:
        raise HTTPException(status_code=403, detail="permission denied")

    data = {
        'nickname': target_user.nickname,
        'avatar_link': target_user.avatar_link,
    }
    return BaseResponse(error_code=0, error_info="success", data=data)


class UpdateMeRequest(BaseModel):
    nickname: Optional[str] = None
    avatar_link: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


@router.put("/api/user/me", dependencies=[Depends(require_auth)])
async def update_user_me(request: Request, body: UpdateMeRequest):
    service = get_user_service()
    user, err = service.update_profile(
        getattr(request.state, 'user_id', None),
        nickname=body.nickname,
        avatar_link=body.avatar_link,
        phone=body.phone,
        email=body.email,
    )
    if not err.success:
        raise HTTPException(status_code=400, detail=err.info)
    data = {
        'nickname': user.nickname,
        'avatar_link': user.avatar_link,
        'phone': user.phone,
        'email': user.email,
    }
    return BaseResponse(error_code=0, error_info="success", data=data)


@router.put("/api/user/me/avatar", dependencies=[Depends(require_auth)])
async def upload_avatar(request: Request, avatar: UploadFile = File(...)):
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="unauthorized")

    file_extension = os.path.splitext(avatar.filename)[1]
    timestamp = int(time.time())
    avatar_path = f"users/{user_id}/avatar-{timestamp}{file_extension}"

    try:
        obs_util = obs.get_instance()
        obs_util.put(avatar_path, await avatar.read())
        avatar_url = obs_util.get_link(avatar_path)

        user_service = get_user_service()
        _, err = user_service.update_profile(user_id, avatar_link=avatar_url)
        if not err.success:
            raise HTTPException(status_code=500, detail=err.info)

        return BaseResponse(error_code=0, error_info="success", data={"avatar_link": avatar_url})
    except Exception as e:
        logging.error(f"upload avatar failed: {e}")
        raise HTTPException(status_code=500, detail="upload avatar failed")


class UpdatePhoneRequest(BaseModel):
    phone: str
    code: str


@router.put("/api/user/me/phone", dependencies=[Depends(require_auth)])
async def update_user_phone(request: Request, body: UpdatePhoneRequest):
    service = get_user_service()
    user, err = service.update_phone_with_code(
        getattr(request.state, 'user_id', None),
        body.phone,
        body.code,
    )
    if not err.success:
        raise HTTPException(status_code=400, detail=err.info)
    data = {
        'nickname': user.nickname,
        'avatar_link': user.avatar_link,
        'phone': user.phone,
        'email': user.email,
    }
    return BaseResponse(error_code=0, error_info="success", data=data)


class UpdateEmailRequest(BaseModel):
    email: str
    code: str


@router.put("/api/user/me/email", dependencies=[Depends(require_auth)])
async def update_user_email(request: Request, body: UpdateEmailRequest):
    service = get_user_service()
    user, err = service.update_email_with_code(
        getattr(request.state, 'user_id', None),
        body.email,
        body.code,
    )
    if not err.success:
        raise HTTPException(status_code=400, detail=err.info)
    data = {
        'nickname': user.nickname,
        'avatar_link': user.avatar_link,
        'phone': user.phone,
        'email': user.email,
    }
    return BaseResponse(error_code=0, error_info="success", data=data)
