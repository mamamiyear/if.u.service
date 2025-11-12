import os
import uuid
import logging
from typing import Any, Optional
from fastapi import FastAPI, UploadFile, File, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from services.people import get_instance as get_people_service
from models.people import People
from agents.extract_people_agent import ExtractPeopleAgent
from utils import obs, ocr

api = FastAPI(title="Single People Management and Searching", version="0.1")
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BaseResponse(BaseModel):
    error_code: int
    error_info: str
    data: Optional[Any] = None

@api.post("/ping")
async def ping():
    return BaseResponse(error_code=0, error_info="success")

class PostInputRequest(BaseModel):
    text: str

@api.post("/recognition/input")
async def post_input(request: PostInputRequest):
    people = extract_people(request.text)
    resp = BaseResponse(error_code=0, error_info="success")
    resp.data = people.to_dict()
    return resp

@api.post("/recognition/image")
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

@api.post("/people")
async def post_people(post_people_request: PostPeopleRequest):
    logging.debug(f"post_people_request: {post_people_request}")
    people = People.from_dict(post_people_request.people)
    service = get_people_service()
    people.id, error = service.save(people)
    if not error.success:
        return BaseResponse(error_code=error.code, error_info=error.info)
    return BaseResponse(error_code=0, error_info="success", data=people.id)

@api.put("/people/{people_id}")
async def update_people(people_id: str, post_people_request: PostPeopleRequest):
    logging.debug(f"post_people_request: {post_people_request}")
    people = People.from_dict(post_people_request.people)
    people.id = people_id
    service = get_people_service()
    res, error = service.get(people_id)
    if not error.success or not res:
        return BaseResponse(error_code=error.code, error_info=error.info)
    _, error = service.save(people)
    if not error.success:
        return BaseResponse(error_code=error.code, error_info=error.info)
    return BaseResponse(error_code=0, error_info="success")

@api.delete("/people/{people_id}")
async def delete_people(people_id: str):
    service = get_people_service()
    error = service.delete(people_id)
    if not error.success:
        return BaseResponse(error_code=error.code, error_info=error.info)
    return BaseResponse(error_code=0, error_info="success")

class GetPeopleRequest(BaseModel):
    query: Optional[str] = None
    conds: Optional[dict] = None
    top_k: int = 5
    
@api.get("/peoples")
async def get_peoples(
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

