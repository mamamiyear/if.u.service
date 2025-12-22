import logging
import os
import uuid
from fastapi import APIRouter, Depends, Request, Query, UploadFile, File
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from models.custom import Custom
from services.custom import get_instance as get_custom_service
from utils.error import ErrorCode
from utils import obs
from web.schemas import BaseResponse
from web.permission import check_permission, get_visible_user_ids

router = APIRouter(tags=["custom"])

class PostCustomRequest(BaseModel):
    custom: dict

@router.post("/api/custom")
def create_custom(request: Request, post_custom_request: PostCustomRequest):
    logging.debug(f"post_custom_request: {post_custom_request}")
    custom = Custom.from_dict(post_custom_request.custom)
    
    # Validate custom data
    err = custom.validate()
    if not err.success:
        return BaseResponse(error_code=err.code, error_info=err.info)
        
    custom.user_id = getattr(request.state, 'user_id', '')
    
    service = get_custom_service()
    custom.id, error = service.save(custom)
    
    if not error.success:
        return BaseResponse(error_code=error.code, error_info=error.info)
    return BaseResponse(error_code=0, error_info="success", data=custom.id)


@router.put("/api/custom/{custom_id}")
def update_custom(request: Request, custom_id: str, post_custom_request: PostCustomRequest):
    logging.debug(f"post_custom_request: {post_custom_request}")
    custom = Custom.from_dict(post_custom_request.custom)
    custom.id = custom_id
    
    # Validate custom data
    err = custom.validate()
    if not err.success:
        return BaseResponse(error_code=err.code, error_info=err.info)
    
    service = get_custom_service()
    # Check permission
    res, error = service.get(custom_id)
    if not error.success or not res:
        return BaseResponse(error_code=error.code, error_info=error.info)
    
    # Check permission
    is_allowed, err = check_permission(
        getattr(request.state, 'user_id', ''),
        getattr(request.state, 'user_org_id', ''),
        res.user_id
    )
    if not is_allowed:
        return BaseResponse(error_code=err.code, error_info=err.info)
        
    custom.user_id = res.user_id # Ensure user_id is not changed or is set correctly
    
    _, error = service.save(custom)
    if not error.success:
        return BaseResponse(error_code=error.code, error_info=error.info)
    return BaseResponse(error_code=0, error_info="success")


@router.delete("/api/custom/{custom_id}")
def delete_custom(request: Request, custom_id: str):
    service = get_custom_service()
    res, error = service.get(custom_id)
    if not error.success or not res:
        return BaseResponse(error_code=error.code, error_info=error.info)
    
    # Check if the user is the owner (strict ownership check for deletion)
    current_user_id = getattr(request.state, 'user_id', '')
    if current_user_id != res.user_id:
        return BaseResponse(error_code=ErrorCode.MODEL_ERROR.value, error_info="permission denied: only owner can delete")
        
    error = service.delete(custom_id)
    if not error.success:
        return BaseResponse(error_code=error.code, error_info=error.info)
    return BaseResponse(error_code=0, error_info="success", data=custom_id)


@router.get("/api/customs")
def get_customs(request: Request, limit: int = Query(10, ge=1, le=1000), offset: int = Query(0, ge=0)):
    service = get_custom_service()
    
    # Get visible user IDs (self + org members)
    visible_user_ids, err = get_visible_user_ids(
        getattr(request.state, 'user_id', ''),
        getattr(request.state, 'user_org_id', '')
    )
    if not err.success:
         return BaseResponse(error_code=err.code, error_info=err.info)
         
    res, error = service.list({'user_id': visible_user_ids}, limit=limit, offset=offset)
    if not error.success:
        return BaseResponse(error_code=error.code, error_info=error.info)
    # custom对象转换为字典
    customs = [custom.to_dict() for custom in res]
    return BaseResponse(error_code=0, error_info="success", data=customs)


@router.get("/api/custom/{custom_id}")
def get_custom(request: Request, custom_id: str):
    service = get_custom_service()
    res, error = service.get(custom_id)
    if not error.success or not res:
        return BaseResponse(error_code=error.code, error_info=error.info)
    if res.user_id != getattr(request.state, 'user_id', ''):
        return BaseResponse(error_code=ErrorCode.MODEL_ERROR.value, error_info="permission denied")
    return BaseResponse(error_code=0, error_info="success", data=res.to_dict())


@router.post("/api/custom/{custom_id}/image")
async def post_custom_image(request: Request, custom_id: str, image: UploadFile = File(...)):
    # 检查 custom id 是否存在
    service = get_custom_service()
    custom, err = service.get(custom_id)
    if not err.success:
        return BaseResponse(error_code=err.code, error_info=err.info)
    
    is_allowed, perm_err = check_permission(
        getattr(request.state, 'user_id', ''),
        getattr(request.state, 'user_org_id', ''),
        custom.user_id
    )
    if not is_allowed:
        return BaseResponse(error_code=perm_err.code, error_info=perm_err.info)

    # 实现上传图片的处理
    # 保存上传的图片文件
    # 生成唯一的文件名
    file_extension = os.path.splitext(image.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"

    # 保存文件到对象存储
    file_path = f"customs/{custom_id}/images/{unique_filename}"
    obs_util = obs.get_instance()
    await run_in_threadpool(obs_util.put, file_path, await image.read())

    # 获取对象存储外链
    obs_url = obs_util.get_link(file_path)
    logging.info(f"obs_url: {obs_url}")

    return BaseResponse(error_code=0, error_info="success", data=obs_url)


@router.delete("/api/custom/{custom_id}/image")
async def delete_custom_image(request: Request, custom_id: str, image_url: str):
    # 检查 custom id 是否存在
    service = get_custom_service()
    custom, err = service.get(custom_id)
    if not err.success:
        return BaseResponse(error_code=err.code, error_info=err.info)

    is_allowed, perm_err = check_permission(
        getattr(request.state, 'user_id', ''),
        getattr(request.state, 'user_org_id', ''),
        custom.user_id
    )
    if not is_allowed:
        return BaseResponse(error_code=perm_err.code, error_info=perm_err.info)

    # 检查 image_url 是否是该 custom 名下的图片链接
    obs_util = obs.get_instance()
    obs_path, err = obs_util.get_obs_path_by_link(image_url)
    if not err.success:
        return BaseResponse(error_code=err.code, error_info=err.info)
    if not obs_path.startswith(f"customs/{custom_id}/images/"):
        return BaseResponse(error_code=ErrorCode.OBS_INPUT_ERROR, error_info=f"文件 {image_url} 不是 {custom_id} 名下的图片链接")

    # 实现删除图片的处理
    # 删除对象存储中的文件
    err = obs_util.delete_by_link(image_url)
    if not err.success:
        return BaseResponse(error_code=err.code, error_info=err.info)

    return BaseResponse(error_code=0, error_info="success")


class PostCommentRequest(BaseModel):
    content: str

@router.post("/api/custom/{custom_id}/comment")
def add_comment(request: Request, custom_id: str, post_comment_request: PostCommentRequest):
    service = get_custom_service()
    custom, err = service.get(custom_id)
    if not err.success:
        return BaseResponse(error_code=err.code, error_info=err.info)
    
    # Check permission for custom
    is_allowed, perm_err = check_permission(
        getattr(request.state, 'user_id', ''),
        getattr(request.state, 'user_org_id', ''),
        custom.user_id
    )
    if not is_allowed:
        return BaseResponse(error_code=perm_err.code, error_info=perm_err.info)
        
    comment, err = service.add_comment(
        custom_id, 
        post_comment_request.content, 
        getattr(request.state, 'user_id', '')
    )
    if not err.success:
        return BaseResponse(error_code=err.code, error_info=err.info)
        
    return BaseResponse(error_code=0, error_info="success", data=comment.to_dict())


@router.put("/api/custom/{custom_id}/comment/{comment_id}")
def update_comment(request: Request, custom_id: str, comment_id: str, post_comment_request: PostCommentRequest):
    service = get_custom_service()
    custom, err = service.get(custom_id)
    if not err.success:
        return BaseResponse(error_code=err.code, error_info=err.info)
    
    # Check permission for custom
    is_allowed, perm_err = check_permission(
        getattr(request.state, 'user_id', ''),
        getattr(request.state, 'user_org_id', ''),
        custom.user_id
    )
    if not is_allowed:
        return BaseResponse(error_code=perm_err.code, error_info=perm_err.info)
        
    err = service.update_comment(
        custom_id, 
        comment_id, 
        post_comment_request.content, 
        getattr(request.state, 'user_id', '')
    )
    if not err.success:
        return BaseResponse(error_code=err.code, error_info=err.info)
        
    return BaseResponse(error_code=0, error_info="success")


@router.delete("/api/custom/{custom_id}/comment/{comment_id}")
def delete_comment(request: Request, custom_id: str, comment_id: str):
    service = get_custom_service()
    custom, err = service.get(custom_id)
    if not err.success:
        return BaseResponse(error_code=err.code, error_info=err.info)
    
    # Check permission for custom
    is_allowed, perm_err = check_permission(
        getattr(request.state, 'user_id', ''),
        getattr(request.state, 'user_org_id', ''),
        custom.user_id
    )
    if not is_allowed:
        return BaseResponse(error_code=perm_err.code, error_info=perm_err.info)
        
    err = service.delete_comment(
        custom_id, 
        comment_id, 
        getattr(request.state, 'user_id', '')
    )
    if not err.success:
        return BaseResponse(error_code=err.code, error_info=err.info)
        
    return BaseResponse(error_code=0, error_info="success")


@router.get("/api/custom/{custom_id}/comments")
def get_comments(request: Request, custom_id: str):
    service = get_custom_service()
    custom, err = service.get(custom_id)
    if not err.success:
        return BaseResponse(error_code=err.code, error_info=err.info)
    
    # Check permission for custom
    is_allowed, perm_err = check_permission(
        getattr(request.state, 'user_id', ''),
        getattr(request.state, 'user_org_id', ''),
        custom.user_id
    )
    if not is_allowed:
        return BaseResponse(error_code=perm_err.code, error_info=perm_err.info)
        
    comments, err = service.get_comments(custom_id)
    if not err.success:
        return BaseResponse(error_code=err.code, error_info=err.info)
        
    return BaseResponse(error_code=0, error_info="success", data=[c.to_dict() for c in comments])
