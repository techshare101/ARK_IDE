from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid

class ToolCall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    step_number: int
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "pending"  # pending, completed, failed

class Step(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    step_number: int
    type: str  # think, tool, done, error, approval_required
    content: str
    tool_call: Optional[ToolCall] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Session(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_prompt: str
    workspace_path: str = "/app"
    status: str = "created"  # created, running, paused, completed, failed
    current_step: int = 0
    steps: List[Step] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    plan: Optional[str] = None

class SessionCreate(BaseModel):
    user_prompt: str
    workspace_path: Optional[str] = "/app"

class ApprovalRequest(BaseModel):
    approved: bool
    modified_args: Optional[Dict[str, Any]] = None
