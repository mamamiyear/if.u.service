
from typing import Protocol


class error(Protocol):
    _error_code: int = 0
    _error_info: str = ""

    def __init__(self, error_code: int, error_info: str):
        self._error_code = error_code
        self._error_info = error_info
    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self._error_code}, {self._error_info})"
    
    @property
    def error_code(self) -> int:
        return self._error_code
    @property
    def error_info(self) -> str:
        return self._error_info
    @property
    def is_success(self) -> bool:
        return self._error_code == 0
