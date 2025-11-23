import os
import time
import uuid
import logging
from typing import Any, Optional, Literal
from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Response, APIRouter, Depends, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from services.people import get_instance as get_people_service
from services.user import get_instance as get_user_service
from web.auth import require_auth
from models.people import People
from agents.extract_people_agent import ExtractPeopleAgent
from utils import obs, ocr
from utils.config import get_instance as get_config
from utils.error import ErrorCode

api = FastAPI(title="Single People Management and Searching", version="0.1")
api.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost:5173", "https://ifu.mamamiyear.site"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

authorized_router = APIRouter(dependencies=[Depends(require_auth)])

class BaseResponse(BaseModel):
    error_code: int
    error_info: str
    data: Optional[Any] = None

@api.post("/api/ping")
async def ping():
    return BaseResponse(error_code=0, error_info="success")

class PostInputRequest(BaseModel):
    text: str

@api.post("/api/recognition/input")
async def post_input(request: PostInputRequest):
    people = extract_people(request.text)
    resp = BaseResponse(error_code=0, error_info="success")
    resp.data = people.to_dict()
    return resp

@api.post("/api/recognition/image")
async def post_input_image(image: UploadFile = File(...)):
    # 实现上传图片的处理
    # 保存上传的图片文件
    # 生成唯一的文件名
    file_extension = os.path.splitext(image.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # 确保uploads目录存在
    os.makedirs("uploads", exist_ok=True)
    
    # 保存文件到对象存储
    file_path = f"uploads/{unique_filename}"
    obs_util = obs.get_instance()
    obs_util.Put(file_path, await image.read())
    
    # 获取对象存储外链
    obs_url = obs_util.Link(file_path)
    logging.info(f"obs_url: {obs_url}")
    
    # 调用OCR处理图片
    ocr_util = ocr.get_instance()
    ocr_result = ocr_util.recognize_image_text(obs_url)
    logging.info(f"ocr_result: {ocr_result}")
    
    people = extract_people(ocr_result, obs_url)
    resp = BaseResponse(error_code=0, error_info="success")
    resp.data = people.to_dict()
    return resp

def extract_people(text: str, cover_link: str = None) -> People:
    extra_agent = ExtractPeopleAgent()
    people = extra_agent.extract_people_info(text)
    people.cover = cover_link
    logging.info(f"people: {people}")
    return people

class PostPeopleRequest(BaseModel):
    people: dict

@authorized_router.post("/api/people")
async def post_people(request: Request, post_people_request: PostPeopleRequest):
    logging.debug(f"post_people_request: {post_people_request}")
    people = People.from_dict(post_people_request.people)
    people.user_id = getattr(request.state, 'user_id', '')
    service = get_people_service()
    people.id, error = service.save(people)
    if not error.success:
        return BaseResponse(error_code=error.code, error_info=error.info)
    return BaseResponse(error_code=0, error_info="success", data=people.id)

@authorized_router.put("/api/people/{people_id}")
async def update_people(request: Request, people_id: str, post_people_request: PostPeopleRequest):
    logging.debug(f"post_people_request: {post_people_request}")
    people = People.from_dict(post_people_request.people)
    people.id = people_id
    service = get_people_service()
    res, error = service.get(people_id)
    if not error.success or not res:
        return BaseResponse(error_code=error.code, error_info=error.info)
    if res.user_id != getattr(request.state, 'user_id', ''):
        return BaseResponse(error_code=ErrorCode.MODEL_ERROR.value, error_info="permission denied")
    people.user_id = res.user_id
    _, error = service.save(people)
    if not error.success:
        return BaseResponse(error_code=error.code, error_info=error.info)
    return BaseResponse(error_code=0, error_info="success")

@authorized_router.delete("/api/people/{people_id}")
async def delete_people(request: Request, people_id: str):
    service = get_people_service()
    res, err = service.get(people_id)
    if not err.success or not res:
        return BaseResponse(error_code=err.code, error_info=err.info)
    if res.user_id != getattr(request.state, 'user_id', ''):
        return BaseResponse(error_code=ErrorCode.MODEL_ERROR.value, error_info="permission denied")
    error = service.delete(people_id)
    if not error.success:
        return BaseResponse(error_code=error.code, error_info=error.info)
    return BaseResponse(error_code=0, error_info="success")

class GetPeopleRequest(BaseModel):
    query: Optional[str] = None
    conds: Optional[dict] = None
    top_k: int = 5
    
@authorized_router.get("/api/peoples")
async def get_peoples(
    request: Request,
    name: Optional[str] = Query(None, description="姓名"),
    gender: Optional[str] = Query(None, description="性别"),
    age: Optional[int] = Query(None, description="年龄"),
    height: Optional[int] = Query(None, description="身高"),
    marital_status: Optional[str] = Query(None, description="婚姻状态"),
    limit: int = Query(10, description="分页大小"),
    offset: int = Query(0, description="分页偏移量"),
    ):
    
    # 解析查询参数为字典
    conds = {}
    conds["user_id"] = getattr(request.state, 'user_id', '')
    if name:
        conds["name"] = name
    if gender:
        conds["gender"] = gender
    if age:
        conds["age"] = age
    if height:
        conds["height"] = height
    if marital_status:
        conds["marital_status"] = marital_status
    
    logging.info(f"conds: , limit: {limit}, offset: {offset}")

    results = []
    service = get_people_service()
    results, error = service.list(conds, limit=limit, offset=offset)
    logging.info(f"query results: {results}")
    if not error.success:
        return BaseResponse(error_code=error.code, error_info=error.info)
    peoples = [people.to_dict() for people in results]
    return BaseResponse(error_code=0, error_info="success", data=peoples)


class RemarkRequest(BaseModel):
    content: str


@authorized_router.post("/api/people/{people_id}/remark")
async def post_remark(request: Request, people_id: str, body: RemarkRequest):
    service = get_people_service()
    res, err = service.get(people_id)
    if not err.success or not res:
        return BaseResponse(error_code=err.code, error_info=err.info)
    if res.user_id != getattr(request.state, 'user_id', ''):
        return BaseResponse(error_code=ErrorCode.MODEL_ERROR.value, error_info="permission denied")
    error = service.save_remark(people_id, body.content)
    if not error.success:
        return BaseResponse(error_code=error.code, error_info=error.info)
    return BaseResponse(error_code=0, error_info="success")


@authorized_router.delete("/api/people/{people_id}/remark")
async def delete_remark(request: Request, people_id: str):
    service = get_people_service()
    res, err = service.get(people_id)
    if not err.success or not res:
        return BaseResponse(error_code=err.code, error_info=err.info)
    if res.user_id != getattr(request.state, 'user_id', ''):
        return BaseResponse(error_code=ErrorCode.MODEL_ERROR.value, error_info="permission denied")
    error = service.delete_remark(people_id)
    if not error.success:
        return BaseResponse(error_code=error.code, error_info=error.info)
    return BaseResponse(error_code=0, error_info="success")


class SendCodeRequest(BaseModel):
    target_type: str
    target: str
    scene: Literal['register', 'update']
    # scene: Literal['register', 'login']


@api.post("/api/user/send_code")
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

@api.post("/api/user")
async def user_register(request: RegisterRequest):
    service = get_user_service()
    from models.user import User
    u = User(
        nickname=request.nickname or "",
        avatar_link=request.avatar_link or "",
        email=request.email or "",
        phone=request.phone or "",
        password_hash=request.password,
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

@api.post("/api/user/login")
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


@authorized_router.delete("/api/user/me/login")
async def user_logout(response: Response, request: Request):
    service = get_user_service()
    err = service.logout(getattr(request.state, 'token', None))
    if not err.success:
        raise HTTPException(status_code=400, detail=err.info)
    conf = get_config()
    cookie_domain = conf.get('auth', 'cookie_domain', fallback=None)
    response.delete_cookie(key="token", domain=cookie_domain, path="/")
    return BaseResponse(error_code=0, error_info="success")


@authorized_router.delete("/api/user/me")
async def user_delete(response: Response, request: Request):
    service = get_user_service()
    err = service.delete_user(getattr(request.state, 'user_id', None))
    if not err.success:
        raise HTTPException(status_code=400, detail=err.info)
    conf = get_config()
    cookie_domain = conf.get('auth', 'cookie_domain', fallback=None)
    response.delete_cookie(key="token", domain=cookie_domain, path="/")
    return BaseResponse(error_code=0, error_info="success")

@authorized_router.get("/api/user/me")
async def user_me(request: Request):
    service = get_user_service()
    user, err = service.get(getattr(request.state, 'user_id', None))
    if not err.success or not user:
        raise HTTPException(status_code=400, detail=err.info)
    data = {
        'nickname': user.nickname,
        'avatar_link': user.avatar_link,
        'phone': user.phone,
        'email': user.email,
    }
    return BaseResponse(error_code=0, error_info="success", data=data)


class UpdateMeRequest(BaseModel):
    nickname: Optional[str] = None
    avatar_link: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


@authorized_router.put("/api/user/me")
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


@authorized_router.put("/api/user/me/avatar")
async def upload_avatar(request: Request, avatar: UploadFile = File(...)):
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="unauthorized")

    file_extension = os.path.splitext(avatar.filename)[1]
    timestamp = int(time.time())
    avatar_path = f"users/{user_id}/avatar-{timestamp}{file_extension}"

    try:
        obs_util = obs.get_instance()
        obs_util.Put(avatar_path, await avatar.read())
        avatar_url = obs_util.Link(avatar_path)

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


@authorized_router.put("/api/user/me/phone")
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


@authorized_router.put("/api/user/me/email")
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

api.include_router(authorized_router)
