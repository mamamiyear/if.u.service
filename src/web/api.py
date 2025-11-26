import os
import uuid
from fastapi import FastAPI, UploadFile, File, APIRouter, Depends
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from web.auth import require_auth
from utils import obs
from web.schemas import BaseResponse
from web.custom import router as custom_router
from web.people import router as people_router
from web.user import router as user_router
from web.recognition import router as recognition_router

api = FastAPI(title="Single People Management and Searching", version="0.1")
api.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost:5173", "https://ifu.mamamiyear.site"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

authorized_router = APIRouter(dependencies=[Depends(require_auth)])

@api.post("/api/ping")
async def ping():
    return BaseResponse(error_code=0, error_info="success")

@authorized_router.post("/api/upload/image")
async def post_upload_image(image: UploadFile = File(...)):
    # 实现上传图片的处理
    # 保存上传的图片文件
    # 生成唯一的文件名
    file_extension = os.path.splitext(image.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"

    # 保存文件到对象存储
    file_path = f"uploads/{unique_filename}"
    obs_util = obs.get_instance()
    await run_in_threadpool(obs_util.put, file_path, await image.read())

    # 获取对象存储外链
    obs_url = obs_util.get_link(file_path)
    return BaseResponse(error_code=0, error_info="success", data=obs_url)


api.include_router(authorized_router)

# Register custom router
api.include_router(custom_router, dependencies=[Depends(require_auth)])

# Register people router
api.include_router(people_router, dependencies=[Depends(require_auth)])

# Register user router
api.include_router(user_router)

# Register recognition router
api.include_router(recognition_router, dependencies=[Depends(require_auth)])

