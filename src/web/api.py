import logging
from typing import Any, Optional
from fastapi import FastAPI, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from services.people import get_instance as get_people_service
from models.people import People

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

@api.delete("/people/{people_id}")
async def delete_people(people_id: str):
    service = get_people_service()
    error = service.delete(people_id)
    if not error.success:
        return BaseResponse(error_code=error.code, error_info=error.info)
    return BaseResponse(error_code=0, error_info="success")