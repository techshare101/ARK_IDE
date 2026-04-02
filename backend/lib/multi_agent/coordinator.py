from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import uuid
from datetime import datetime, timezone

class AgentRole(str, Enum):
    ARCHITECT = "architect"
    CODER = "coder"
    REVIEWER = "reviewer"
    QA = "qa"
    DEBUGGER = "debugger"

class AgentProfile(BaseModel):
    role: AgentRole
    system_message: str
    capabilities: List[str]
    max_steps: int = 30

class MultiAgentTask(BaseModel):
    id: str = None
    parent_session_id: str
    assigned_role: AgentRole
    description: str
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[Dict[str, Any]] = None
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    
    def __init__(self, **data):
        if 'id' not in data or data['id'] is None:
            data['id'] = str(uuid.uuid4())
        if 'created_at' not in data or data['created_at'] is None:
            data['created_at'] = datetime.now(timezone.utc)
        super().__init__(**data)

class AgentCoordinator:
    """Coordinates multiple specialized agents"""
    
    AGENT_PROFILES = {
        AgentRole.ARCHITECT: AgentProfile(
            role=AgentRole.ARCHITECT,
            system_message="""You are an Architect agent. Your role is to:
- Analyze project structure and requirements
- Plan technical architecture
- Design system components
- Make high-level technical decisions
- Break down complex tasks into smaller pieces

Focus on planning, not implementation.""",
            capabilities=["analyze", "plan", "design", "decompose"]
        ),
        AgentRole.CODER: AgentProfile(
            role=AgentRole.CODER,
            system_message="""You are a Coder agent. Your role is to:
- Implement features and fixes
- Write clean, maintainable code
- Follow best practices
- Execute on architectural plans
- Make code changes efficiently

Focus on implementation, not planning.""",
            capabilities=["code", "implement", "write", "modify"]
        ),
        AgentRole.REVIEWER: AgentProfile(
            role=AgentRole.REVIEWER,
            system_message="""You are a Reviewer agent. Your role is to:
- Review code quality and correctness
- Identify bugs and issues
- Suggest improvements
- Ensure best practices are followed
- Validate implementations

Focus on quality assessment, not implementation.""",
            capabilities=["review", "validate", "assess", "critique"]
        ),
        AgentRole.QA: AgentProfile(
            role=AgentRole.QA,
            system_message="""You are a QA agent. Your role is to:
- Test functionality
- Verify requirements are met
- Find edge cases and bugs
- Validate user experience
- Ensure quality standards

Focus on testing and validation.""",
            capabilities=["test", "verify", "validate", "check"]
        ),
        AgentRole.DEBUGGER: AgentProfile(
            role=AgentRole.DEBUGGER,
            system_message="""You are a Debugger agent. Your role is to:
- Diagnose errors and bugs
- Trace issues to root causes
- Analyze error messages and logs
- Propose fixes for bugs
- Test solutions

Focus on problem diagnosis and debugging.""",
            capabilities=["debug", "diagnose", "trace", "fix"]
        )
    }
    
    @classmethod
    def get_profile(cls, role: AgentRole) -> AgentProfile:
        """Get agent profile for role"""
        return cls.AGENT_PROFILES[role]
    
    @classmethod
    def determine_best_agent(cls, task_description: str) -> AgentRole:
        """Determine which agent is best suited for a task"""
        task_lower = task_description.lower()
        
        # Simple keyword matching (could use LLM for better routing)
        if any(word in task_lower for word in ['plan', 'design', 'architect', 'structure']):
            return AgentRole.ARCHITECT
        elif any(word in task_lower for word in ['debug', 'error', 'fix bug', 'diagnose']):
            return AgentRole.DEBUGGER
        elif any(word in task_lower for word in ['review', 'check code', 'validate']):
            return AgentRole.REVIEWER
        elif any(word in task_lower for word in ['test', 'qa', 'verify']):
            return AgentRole.QA
        else:
            return AgentRole.CODER
    
    @classmethod
    def create_task(
        cls,
        parent_session_id: str,
        description: str,
        role: Optional[AgentRole] = None
    ) -> MultiAgentTask:
        """Create a new multi-agent task"""
        if role is None:
            role = cls.determine_best_agent(description)
        
        return MultiAgentTask(
            parent_session_id=parent_session_id,
            assigned_role=role,
            description=description
        )
