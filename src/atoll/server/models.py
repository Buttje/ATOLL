"""Pydantic models for REST API requests and responses."""

from typing import Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    """Chat message."""

    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")


class GenerateRequest(BaseModel):
    """Request model for /api/generate endpoint."""

    model: str = Field(..., description="Model name")
    prompt: str = Field(..., description="Prompt text")
    stream: bool = Field(default=False, description="Enable streaming response")
    context: Optional[list[int]] = Field(default=None, description="Conversation context")
    options: Optional[dict] = Field(default=None, description="Model options")


class GenerateResponse(BaseModel):
    """Response model for /api/generate endpoint."""

    model: str = Field(..., description="Model name")
    created_at: str = Field(..., description="Response timestamp")
    response: str = Field(..., description="Generated response text")
    done: bool = Field(default=True, description="Whether generation is complete")
    context: Optional[list[int]] = Field(default=None, description="Updated conversation context")


class ChatRequest(BaseModel):
    """Request model for /api/chat endpoint."""

    model: str = Field(..., description="Model name")
    messages: list[Message] = Field(..., description="Conversation messages")
    stream: bool = Field(default=False, description="Enable streaming response")
    options: Optional[dict] = Field(default=None, description="Model options")


class ChatResponse(BaseModel):
    """Response model for /api/chat endpoint."""

    model: str = Field(..., description="Model name")
    created_at: str = Field(..., description="Response timestamp")
    message: Message = Field(..., description="Assistant response message")
    done: bool = Field(default=True, description="Whether generation is complete")


class ModelInfo(BaseModel):
    """Model information."""

    name: str = Field(..., description="Model name")
    modified_at: str = Field(..., description="Last modification timestamp")
    size: int = Field(..., description="Model size in bytes")


class TagsResponse(BaseModel):
    """Response model for /api/tags endpoint."""

    models: list[ModelInfo] = Field(..., description="List of available models")
