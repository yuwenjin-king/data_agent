from pydantic import BaseModel
from typing import Optional, Generic, TypeVar, List

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: Optional[T] = None


class PageResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class PageRequest(BaseModel):
    page: int = 1
    page_size: int = 20
