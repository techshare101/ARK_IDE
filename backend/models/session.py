from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class PipelineStage(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    BUILDING = "building"
    TESTING = "testing"
    DEPLOYING = "deploying"
    MONITORING = "monitoring"
    COMPLETE = "complete"
    FAILED = "failed"


class TaskType(str, Enum):
    CREATE_FILE = "create_file"
    RUN_COMMAND = "run_command"
    INSTALL_DEPS = "install_deps"
    WRITE_TESTS = "write_tests"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class Task(BaseModel):
    id: str
    type: TaskType
    description: str
    file_path: Optional[str] = None
    command: Optional[str] = None
    depends_on: List[str] = []
    status: TaskStatus = TaskStatus.PENDING
    output: Optional[str] = None
    error: Optional[str] = None


class TaskTree(BaseModel):
    project_name: str
    tech_stack: List[str]
    tasks: List[Task]
    test_command: str
    run_command: str
    estimated_files: int


class FileManifest(BaseModel):
    path: str
    content: str
    size: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TestResult(BaseModel):
    passed: int = 0
    failed: int = 0
    errors: int = 0
    coverage: float = 0.0
    output: str = ""
    success: bool = False


class DeployInfo(BaseModel):
    sandbox_id: Optional[str] = None
    preview_url: Optional[str] = None
    deploy_url: Optional[str] = None
    port: int = 3000
    status: str = "pending"
    deployed_at: Optional[datetime] = None


class AgentRun(BaseModel):
    agent: str
    stage: int
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    status: str = "running"
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal: str
    name: Optional[str] = None
    stage: PipelineStage = PipelineStage.IDLE
    task_tree: Optional[TaskTree] = None
    file_manifest: List[FileManifest] = []
    test_results: Optional[TestResult] = None
    deploy_info: Optional[DeployInfo] = None
    agent_runs: List[AgentRun] = []
    iterations: int = 0
    max_iterations: int = 3
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None
    sandbox_id: Optional[str] = None


class CreateProjectRequest(BaseModel):
    goal: str


class ApproveActionRequest(BaseModel):
    action_id: str
    approved: bool
