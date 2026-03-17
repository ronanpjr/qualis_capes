"""
Pydantic schemas for request validation and API response serialization.

This module defines all request and response models used throughout the QUALIS CAPES API,
with comprehensive OpenAPI documentation for each field and model.
"""

from typing import Optional
from pydantic import BaseModel, Field


class PeriodicoResponse(BaseModel):
    """
    Periódico científico classification information.
    
    Represents a single journal entry in the QUALIS database with its
    classification level and associated metadata.
    
    Example:
        {
            "id": 1,
            "issn": "0100-3941",
            "titulo": "Acta Botanica Brasilica",
            "area": "Botânica",
            "estrato": "A2"
        }
    """
    id: int = Field(..., description="Unique identifier for the periódico (journal)")
    issn: str = Field(..., description="International Standard Serial Number (ISSN) - unique journal identifier")
    titulo: str = Field(..., description="Official title of the periódico (journal)")
    area: str = Field(..., description="Evaluation area (one of ~50 CAPES areas)")
    estrato: str = Field(..., description="QUALIS classification level (A1, A2, A3, A4, B1, B2, B3, B4, or C)")

    model_config = {"from_attributes": True}


class PaginatedResponse(BaseModel):
    """
    Paginated collection of periódicos.
    
    Returns a list of periódicos along with pagination metadata to facilitate
    browsing through large result sets.
    
    Example:
        {
            "items": [
                {
                    "id": 1,
                    "issn": "0100-3941",
                    "titulo": "Acta Botanica Brasilica",
                    "area": "Botânica",
                    "estrato": "A2"
                }
            ],
            "total": 150,
            "page": 1,
            "per_page": 30,
            "total_pages": 5
        }
    """
    items: list[PeriodicoResponse] = Field(..., description="List of periódicos for the current page")
    total: int = Field(..., description="Total number of periódicos matching the query across all pages", ge=0)
    page: int = Field(..., description="Current page number (1-indexed)", ge=1)
    per_page: int = Field(..., description="Number of items per page (between 1 and 100)", ge=1, le=100)
    total_pages: int = Field(..., description="Total number of pages available", ge=0)


class DistribuicaoItem(BaseModel):
    """
    Distribution count for a single estrato (classification level).
    
    Represents how many periódicos fall into each QUALIS classification
    level within a specific evaluation area.
    
    Example:
        {
            "estrato": "A1",
            "count": 12,
            "percentual": 8.5
        }
    """
    estrato: str = Field(..., description="QUALIS classification level (A1, A2, A3, A4, B1, B2, B3, B4, or C)")
    count: int = Field(..., description="Number of periódicos in this estrato", ge=0)
    percentual: float = Field(..., description="Percentage of periódicos in this estrato (0-100)", ge=0.0, le=100.0)


class DistribuicaoResponse(BaseModel):
    """
    Distribution statistics for periódicos in a specific evaluation area.
    
    Provides a breakdown of how periódicos are distributed across QUALIS
    classification levels, including both counts and percentages.
    
    Example:
        {
            "area": "Botânica",
            "total": 141,
            "distribuicao": [
                {
                    "estrato": "A1",
                    "count": 12,
                    "percentual": 8.51
                },
                {
                    "estrato": "A2",
                    "count": 18,
                    "percentual": 12.77
                }
            ]
        }
    """
    area: str = Field(..., description="The evaluation area name")
    total: int = Field(..., description="Total number of periódicos in this area", ge=0)
    distribuicao: list[DistribuicaoItem] = Field(
        ...,
        description="List of distribution items, one for each estrato, ordered from A1 to C"
    )


class ChatRequest(BaseModel):
    """
    Natural language query request for the AI chat endpoint.
    
    Allows users to query the QUALIS database using natural language instead of
    structured API calls. The AI model interprets the request and calls the
    appropriate endpoints (function calling).
    
    Example:
        {
            "message": "Quais são os periódicos da área de Botânica com estratificação A1 ou A2?"
        }
    """
    message: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Natural language question about QUALIS periódicos (1-500 characters)",
        strip_whitespace=True,
        examples=[
            "Quais periódicos de Botânica têm estrato A1?",
            "Procuro periódicos na área de Matemática",
            "Mostra a distribuição de estratos em Física"
        ]
    )


class ChatResponse(BaseModel):
    """
    Response from the AI chat endpoint.
    
    Contains the AI-generated response text, optionally with structured data
    from the queried endpoints, and information about which endpoint was invoked.
    
    Example:
        {
            "response": "Encontrei 12 periódicos com estrato A1 em Botânica.",
            "data": [
                {
                    "id": 1,
                    "issn": "0100-3941",
                    "titulo": "Acta Botanica Brasilica",
                    "area": "Botânica",
                    "estrato": "A1"
                }
            ],
            "action_taken": "search_periodicos"
        }
    """
    response: str = Field(..., description="Natural language response generated by the AI model")
    data: Optional[list[dict]] = Field(
        None,
        description="Structured data returned from the invoked endpoint (if applicable)"
    )
    action_taken: Optional[str] = Field(
        None,
        description="Name of the function/endpoint called by the AI (e.g., 'list_areas', 'search_periodicos', 'get_distribuicao')"
    )
