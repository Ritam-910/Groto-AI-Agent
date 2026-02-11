from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class Message(BaseModel):
    """Represents a single message in the conversation"""
    role: str = Field(..., description="Role of the message sender (user/assistant/system)")
    content: str = Field(..., description="Content of the message")
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(..., min_length=1, description="User message")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for context")
    stream: bool = Field(default=False, description="Whether to stream the response")


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str = Field(..., description="Agent's response")
    conversation_id: str = Field(..., description="Conversation ID")
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class ToolCall(BaseModel):
    """Represents a tool call made by the agent"""
    tool_name: str = Field(..., description="Name of the tool")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    result: Optional[Any] = Field(None, description="Tool execution result")


class AgentState(BaseModel):
    """Represents the current state of the agent"""
    conversation_id: str
    messages: List[Message] = Field(default_factory=list)
    tool_calls: List[ToolCall] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    ollama_connected: bool
    model: str
    timestamp: datetime = Field(default_factory=datetime.now)
