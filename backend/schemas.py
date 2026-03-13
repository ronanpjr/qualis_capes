"""
Pydantic schemas for request validation and API response serialization.
"""

from typing import Optional
from pydantic import BaseModel, Field


class PeriodicoResponse(BaseModel):
    id: int
    issn: str
    titulo: str
    area: str
    estrato: str

    model_config = {"from_attributes": True}


class PaginatedResponse(BaseModel):
    items: list[PeriodicoResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class DistribuicaoItem(BaseModel):
    estrato: str
    count: int
    percentual: float


class DistribuicaoResponse(BaseModel):
    area: str
    total: int
    distribuicao: list[DistribuicaoItem]


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500, strip_whitespace=True)


class ChatResponse(BaseModel):
    response: str
    data: Optional[list[dict]] = None
    action_taken: Optional[str] = None
