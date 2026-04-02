from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid

class PipelineStage(str, Enum):
    """Pipeline execution stages"""
    PLANNING = "planning"
    BUILDING = "building"
    TESTING = "testing"
    DEPLOYING = "deploying"
    MONITORING = "monitoring"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskStatus(str, Enum):
    """Individual task status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class Task(BaseModel):
    """Individual task in execution plan"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    task_type: str  # "create_file", "run_command", "install_package", etc.
    arguments: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)  # IDs of tasks that must complete first
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

class ExecutionPlan(BaseModel):
    """Complete execution plan from PlannerAgent"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal: str
    tasks: List[Task] = Field(default_factory=list)
    architecture_decisions: Dict[str, Any] = Field(default_factory=dict)
    estimated_duration_minutes: Optional[int] = None
    tech_stack: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Artifact(BaseModel):
    """Generated artifact (file, URL, test result, etc.)"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    artifact_type: str  # "file", "url", "test_result", "log"
    name: str
    content: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Project(BaseModel):
    """Complete project with pipeline state"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal: str
    current_stage: PipelineStage = PipelineStage.PLANNING
    execution_plan: Optional[ExecutionPlan] = None
    artifacts: List[Artifact] = Field(default_factory=list)
    sandbox_id: Optional[str] = None
    preview_url: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

class ProjectCreate(BaseModel):
    """Request to create new project"""
    goal: str
    workspace_path: Optional[str] = "/home/user/project"

class AgentEvent(BaseModel):
    """Event emitted by agents during execution"""
    project_id: str
    stage: PipelineStage
    event_type: str  # "plan_created", "file_created", "test_result", etc.
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
