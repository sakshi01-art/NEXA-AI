from pydantic import BaseModel, Field
from typing import Optional, List, Any, Literal
from enum import Enum
from datetime import datetime

class PermissionLevel(str, Enum):
    SAFE = "safe"
    SENSITIVE = "sensitive"
    DESTRUCTIVE = "destructive"

class ToolStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AgentState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    THINKING = "thinking"
    EXECUTING = "executing"
    SPEAKING = "speaking"
    ERROR = "error"
    WAITING_CONFIRMATION = "waiting_confirmation"

class Message(BaseModel):
    id: str
    type: Literal["user", "assistant", "system"]
    content: str
    timestamp: float
    language: Optional[str] = None

class ToolInput(BaseModel):
    tool: str
    parameters: dict

class ToolResult(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: dict = {}

class ToolCall(BaseModel):
    id: str
    tool: str
    input: dict
    status: ToolStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: float
    end_time: Optional[float] = None

class TaskStep(BaseModel):
    id: str
    description: str
    tool: str
    input: dict
    status: ToolStatus
    result: Optional[Any] = None

class Task(BaseModel):
    id: str
    command: str
    intent: str
    plan: List[TaskStep]
    status: ToolStatus
    timeline: List[dict]
    result: Optional[Any] = None
    error: Optional[str] = None

class ToolDefinition(BaseModel):
    name: str
    description: str
    category: str
    permission: PermissionLevel
    schema: dict
    enabled: bool = True

class VoiceCommand(BaseModel):
    text: str
    language: Optional[str] = None
    confidence: float = 1.0

class SystemStats(BaseModel):
    cpu: float
    memory: float
    disk: float
    network: dict
    battery: Optional[float] = None
    temperature: Optional[float] = None
