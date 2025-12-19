
import os
import uuid
import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from models.people import People
from models.custom import Custom
from agents.extract_people_agent import ExtractPeopleAgent
from agents.extract_custom_agent import ExtractCustomAgent
from utils import obs, ocr
from web.schemas import BaseResponse
from utils.error import ErrorCode

router = APIRouter(tags=["recognition"])

def extract_people(text: str, cover_link: str = None) -> People:
    extra_agent = ExtractPeopleAgent()
    people = extra_agent.extract_people_info(text)
    if people:
        people.cover = cover_link
        logging.info(f"people: {people}")
    return people

def extract_custom(text: str, image_link: str = None) -> Custom:
    extra_agent = ExtractCustomAgent()
    custom = extra_agent.extract_custom_info(text)
    if custom:
        if image_link:
            custom.images = [image_link]
        logging.info(f"custom: {custom}")
    return custom

class PostInputRequest(BaseModel):
    text: str

@router.post("/api/recognition/{model}/input")
async def post_recognition_input(model: str, request: PostInputRequest):
    if model == "people":
        result = await run_in_threadpool(extract_people, request.text)
    elif model == "custom":
        result = await run_in_threadpool(extract_custom, request.text)
    else:
        return BaseResponse(error_code=ErrorCode.MODEL_FIELD_ERROR.value, error_info=f"Unknown model: {model}")
    
    if result is None:
         return BaseResponse(error_code=ErrorCode.MODEL_ERROR.value, error_info="Extraction failed")

    resp = BaseResponse(error_code=0, error_info="success")
    resp.data = result.to_dict()
    return resp

@router.post("/api/recognition/{model}/image")
async def post_recognition_image(model: str, image: UploadFile = File(...)):
    if model not in ["people", "custom"]:
        return BaseResponse(error_code=ErrorCode.MODEL_FIELD_ERROR.value, error_info=f"Unknown model: {model}")

    # 实现上传图片的处理
    # 保存上传的图片文件
    # 生成唯一的文件名
    file_extension = os.path.splitext(image.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"

    # 保存文件到对象存储
    file_path = f"uploads/{model}/{unique_filename}"
    obs_util = obs.get_instance()
    await run_in_threadpool(obs_util.put, file_path, await image.read())

    # 获取对象存储外链
    obs_url = obs_util.get_link(file_path)
    logging.info(f"obs_url: {obs_url}")

    # 调用OCR处理图片
    ocr_util = ocr.get_instance()
    ocr_result = await run_in_threadpool(ocr_util.recognize_image_text, obs_url)
    logging.info(f"ocr_result: {ocr_result}")

    if model == "people":
        result = await run_in_threadpool(extract_people, ocr_result, obs_url)
    elif model == "custom":
        result = await run_in_threadpool(extract_custom, ocr_result, obs_url)
    
    if result is None:
         return BaseResponse(error_code=ErrorCode.MODEL_ERROR.value, error_info="Extraction failed")

    resp = BaseResponse(error_code=0, error_info="success")
    resp.data = result.to_dict()
    return resp
