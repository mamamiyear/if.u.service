
import json
import logging
import os
import uuid

from typing import Any, Optional
from fastapi import FastAPI, File, UploadFile, Query
from pydantic import BaseModel

from ai.agent import ExtractPeopleAgent
from models.people import People
from utils import obs, ocr, vsdb
from storage.people_store import get_instance as get_people_store
from fastapi.middleware.cors import CORSMiddleware

api = FastAPI(title="Single People Management and Searching", version="1.0.0")
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

class PostInputRequest(BaseModel):
    text: str

@api.post("/input")
async def post_input(request: PostInputRequest):
    extra_agent = ExtractPeopleAgent()
    people = extra_agent.extract_people_info(request.text)
    logging.info(f"people: {people}")
    resp = BaseResponse(error_code=0, error_info="success")
    resp.data = people.to_dict()
    return resp

@api.post("/input_image")
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
    
    post_input_request = PostInputRequest(text=ocr_result)
    return await post_input(post_input_request)

class PostPeopleRequest(BaseModel):
    people: dict

@api.post("/peoples")
async def post_people(post_people_request: PostPeopleRequest):
    logging.debug(f"post_people_request: {post_people_request}")
    people = People.from_dict(post_people_request.people)
    store = get_people_store()
    people.id = store.save(people)    
    return BaseResponse(error_code=0, error_info="success", data=people.id)

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
    search: Optional[str] = Query(None, description="搜索内容"),
    top_k: int = Query(5, description="搜索结果数量"),
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
    
    logging.info(f"conds: , limit: {limit}, offset: {offset}, search: {search}, top_k: {top_k}")

    results = []
    store = get_people_store()
    if search:
        results = store.search(search, conds, ids=None, top_k=top_k)
        logging.info(f"search results: {results}")
    else:
        results = store.query(conds, limit=limit, offset=offset)
        logging.info(f"query results: {results}")
    peoples = [people.to_dict() for people in results]
    return BaseResponse(error_code=0, error_info="success", data=peoples)

@api.delete("/peoples/{people_id}")
async def delete_people(people_id: str):
    store = get_people_store()
    store.delete(people_id)
    return BaseResponse(error_code=0, error_info="success")