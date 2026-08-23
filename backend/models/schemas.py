from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description="User's natural language query"
    )

    username: str = Field(
        ...,
        min_length=1,
        description="Authenticated ParcelPilot username"
    )


class ChatResponse(BaseModel):
    success: bool

    answer: Optional[str] = None
    error: Optional[str] = None

    data: Optional[Dict[str, Any]] = None
    order: Optional[Dict[str, Any]] = None
    account: Optional[Dict[str, Any]] = None
    ticket: Optional[Dict[str, Any]] = None
    action: Optional[Dict[str, Any]] = None

    sources: list = []
    tools_used: list = []

    confirmation_required: bool = False
    executed: bool = False