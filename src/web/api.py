from typing import Any, Optional
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

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
