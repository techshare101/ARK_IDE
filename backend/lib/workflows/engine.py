from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class WorkflowType(str, Enum):
    FIX_BUILD = "fix_build"
    DEBUG_ERROR = "debug_error"
    EXPLAIN_CODE = "explain_code"
    SCAN_PROJECT = "scan_project"
    ADD_FEATURE = "add_feature"
    REFACTOR_CODE = "refactor_code"
    WRITE_TESTS = "write_tests"

class WorkflowStep(BaseModel):
    action: str  # tool name or "think"
    description: str
    args: Optional[Dict[str, Any]] = None
    expected_outcome: str

class Workflow(BaseModel):
    type: WorkflowType
    name: str
    description: str
    steps: List[WorkflowStep]
    estimated_duration: str

class WorkflowEngine:
    """Pre-built workflows for common tasks"""
    
    WORKFLOWS = {
        WorkflowType.FIX_BUILD: Workflow(
            type=WorkflowType.FIX_BUILD,
            name="Fix Build",
            description="Diagnose and fix build errors",
            estimated_duration="2-5 minutes",
            steps=[
                WorkflowStep(
                    action="run_command",
                    description="Run build command",
                    args={"command": "npm run build"},
                    expected_outcome="Capture build errors"
                ),
                WorkflowStep(
                    action="think",
                    description="Analyze error messages",
                    expected_outcome="Identify root cause of errors"
                ),
                WorkflowStep(
                    action="read_file",
                    description="Read files with errors",
                    expected_outcome="Understand current code"
                ),
                WorkflowStep(
                    action="write_file",
                    description="Fix code issues",
                    expected_outcome="Code errors resolved"
                ),
                WorkflowStep(
                    action="run_command",
                    description="Verify build passes",
                    args={"command": "npm run build"},
                    expected_outcome="Build succeeds"
                )
            ]
        ),
        WorkflowType.DEBUG_ERROR: Workflow(
            type=WorkflowType.DEBUG_ERROR,
            name="Debug Error",
            description="Investigate and fix runtime errors",
            estimated_duration="3-7 minutes",
            steps=[
                WorkflowStep(
                    action="read_file",
                    description="Read error logs",
                    expected_outcome="Understand error context"
                ),
                WorkflowStep(
                    action="think",
                    description="Trace error to source",
                    expected_outcome="Identify problematic code"
                ),
                WorkflowStep(
                    action="read_file",
                    description="Examine source code",
                    expected_outcome="Find bug location"
                ),
                WorkflowStep(
                    action="write_file",
                    description="Apply fix",
                    expected_outcome="Bug resolved"
                ),
                WorkflowStep(
                    action="run_command",
                    description="Test fix",
                    expected_outcome="Error no longer occurs"
                )
            ]
        ),
        WorkflowType.EXPLAIN_CODE: Workflow(
            type=WorkflowType.EXPLAIN_CODE,
            name="Explain Code",
            description="Analyze and explain codebase",
            estimated_duration="1-3 minutes",
            steps=[
                WorkflowStep(
                    action="list_files",
                    description="Survey project structure",
                    expected_outcome="Understand project layout"
                ),
                WorkflowStep(
                    action="read_file",
                    description="Read key files",
                    expected_outcome="Analyze code patterns"
                ),
                WorkflowStep(
                    action="think",
                    description="Generate explanation",
                    expected_outcome="Clear code documentation"
                )
            ]
        ),
        WorkflowType.SCAN_PROJECT: Workflow(
            type=WorkflowType.SCAN_PROJECT,
            name="Scan Project",
            description="Comprehensive project analysis",
            estimated_duration="2-4 minutes",
            steps=[
                WorkflowStep(
                    action="list_files",
                    description="List all files",
                    args={"path": ".", "recursive": True},
                    expected_outcome="Complete file inventory"
                ),
                WorkflowStep(
                    action="read_file",
                    description="Read package.json",
                    args={"path": "package.json"},
                    expected_outcome="Understand dependencies"
                ),
                WorkflowStep(
                    action="git_status",
                    description="Check git status",
                    expected_outcome="Know uncommitted changes"
                ),
                WorkflowStep(
                    action="think",
                    description="Generate project report",
                    expected_outcome="Comprehensive project overview"
                )
            ]
        )
    }
    
    @classmethod
    def get_workflow(cls, workflow_type: WorkflowType) -> Workflow:
        """Get workflow by type"""
        return cls.WORKFLOWS.get(workflow_type)
    
    @classmethod
    def list_workflows(cls) -> List[Workflow]:
        """List all available workflows"""
        return list(cls.WORKFLOWS.values())
    
    @classmethod
    def workflow_to_prompt(cls, workflow_type: WorkflowType, context: str = "") -> str:
        """Convert workflow to natural language prompt"""
        workflow = cls.get_workflow(workflow_type)
        if not workflow:
            return context
        
        prompt_parts = [
            f"Task: {workflow.description}",
            f"Context: {context}" if context else "",
            "",
            "Follow these steps:"
        ]
        
        for i, step in enumerate(workflow.steps, 1):
            prompt_parts.append(f"{i}. {step.description}")
            prompt_parts.append(f"   Expected: {step.expected_outcome}")
        
        return "\n".join(prompt_parts)
