from typing import Any, Optional
from pydantic import BaseModel

class BaseResponse(BaseModel):
    error_code: int
    error_info: str
    data: Optional[Any] = None
