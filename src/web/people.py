import os
import uuid
import logging
from typing import Optional
from fastapi import APIRouter, Request, UploadFile, File, Query
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from services.people import get_instance as get_people_service
from models.people import People
from utils import obs
from utils.error import ErrorCode
from web.schemas import BaseResponse

router = APIRouter(tags=["people"])


class PostPeopleRequest(BaseModel):
    people: dict

@router.post("/api/people")
async def post_people(request: Request, post_people_request: PostPeopleRequest):
    logging.debug(f"post_people_request: {post_people_request}")
    people = People.from_dict(post_people_request.people)
    people.user_id = getattr(request.state, 'user_id', '')
    service = get_people_service()
    people.id, error = service.save(people)
    if not error.success:
        return BaseResponse(error_code=error.code, error_info=error.info)
    return BaseResponse(error_code=0, error_info="success", data=people.id)

@router.put("/api/people/{people_id}")
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

@router.delete("/api/people/{people_id}")
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

@router.get("/api/peoples")
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


@router.post("/api/people/{people_id}/remark")
async def post_people_remark(request: Request, people_id: str, body: RemarkRequest):
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


@router.delete("/api/people/{people_id}/remark")
async def delete_people_remark(request: Request, people_id: str):
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


@router.post("/api/people/{people_id}/image")
async def post_people_image(request: Request, people_id: str, image: UploadFile = File(...)):

    # 检查 people id 是否存在
    service = get_people_service()
    people, err = service.get(people_id)
    if not err.success:
        return BaseResponse(error_code=err.code, error_info=err.info)
    
    if people.user_id != getattr(request.state, 'user_id', ''):
        return BaseResponse(error_code=ErrorCode.MODEL_ERROR.value, error_info="permission denied")

    # 实现上传图片的处理
    # 保存上传的图片文件
    # 生成唯一的文件名
    file_extension = os.path.splitext(image.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"

    # 保存文件到对象存储
    file_path = f"peoples/{people_id}/images/{unique_filename}"
    obs_util = obs.get_instance()
    await run_in_threadpool(obs_util.put, file_path, await image.read())

    # 获取对象存储外链
    obs_url = obs_util.get_link(file_path)
    logging.info(f"obs_url: {obs_url}")

    return BaseResponse(error_code=0, error_info="success", data=obs_url)


@router.delete("/api/people/{people_id}/image")
async def delete_people_image(request: Request, people_id: str, image_url: str):
    # 检查 people id 是否存在
    service = get_people_service()
    people, err = service.get(people_id)
    if not err.success:
        return BaseResponse(error_code=err.code, error_info=err.info)

    if people.user_id != getattr(request.state, 'user_id', ''):
        return BaseResponse(error_code=ErrorCode.MODEL_ERROR.value, error_info="permission denied")

    # 检查 image_url 是否是该 people 名下的图片链接
    obs_util = obs.get_instance()
    obs_path, err = obs_util.get_obs_path_by_link(image_url)
    if not err.success:
        return BaseResponse(error_code=err.code, error_info=err.info)
    if not obs_path.startswith(f"peoples/{people_id}/images/"):
        return BaseResponse(error_code=ErrorCode.OBS_INPUT_ERROR, error_info=f"文件 {image_url} 不是 {people_id} 名下的图片链接")

    # 实现删除图片的处理
    # 删除对象存储中的文件
    err = obs_util.delete_by_link(image_url)
    if not err.success:
        return BaseResponse(error_code=err.code, error_info=err.info)

    return BaseResponse(error_code=0, error_info="success")
