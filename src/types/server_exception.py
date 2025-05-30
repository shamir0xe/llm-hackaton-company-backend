from typing import Optional
from ..types.exception_types import ExceptionTypes


class ServerException(Exception):
    exception_type: ExceptionTypes
    detail: str

    def __init__(self, exception_type: ExceptionTypes, detail: Optional[str] = None):
        self.exception_type = exception_type
        self.detail = detail or exception_type.value
