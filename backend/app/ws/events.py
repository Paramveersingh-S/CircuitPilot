from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class BaseEvent(BaseModel):
    type: str
    ts: str

class ChatEvent(BaseEvent):
    type: str = "chat"
    role: str
    text: str

class ToolCallStartedEvent(BaseEvent):
    type: str = "tool_call_started"
    id: str
    tool: str
    args: Dict[str, Any]

class ToolCallCompletedEvent(BaseEvent):
    type: str = "tool_call_completed"
    id: str
    result: Dict[str, Any]

class FileChangedEvent(BaseEvent):
    type: str = "file_changed"
    path: str

class DRCResultEvent(BaseEvent):
    type: str = "drc_result"
    violations: List[Any]
    clean: bool

class ApprovalRequiredEvent(BaseEvent):
    type: str = "approval_required"
    id: str
    action: str
    detail: str

class UserCommandEvent(BaseModel):
    type: str = "user_command"
    text: str

class ApprovalResponseEvent(BaseModel):
    type: str = "approval_response"
    id: str
    approved: bool
