
from enum import Enum
import logging
from typing import Protocol

class ErrorCode(Enum):
    SUCCESS = 0
    MODEL_ERROR = 1000
    MODEL_FIELD_ERROR = 1001
    MODEL_NOT_FOUND = 1002
    PERMISSION_DENIED = 1403
    RLDB_ERROR = 2100
    RLDB_NOT_FOUND = 2101
    OBS_ERROR = 3100
    OBS_INPUT_ERROR = 3102
    OBS_SERVICE_ERROR = 3103

class error(Protocol):
    _error_code: int = 0
    _error_info: str = ""

    def __init__(self, error_code: ErrorCode, error_info: str):
        self._error_code = int(error_code.value)
        self._error_info = error_info
    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self._error_code}, {self._error_info})"
    
    @property
    def code(self) -> int:
        return self._error_code
    @property
    def info(self) -> str:
        return self._error_info
    @property
    def success(self) -> bool:
        return self._error_code == 0
