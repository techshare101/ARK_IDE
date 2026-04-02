from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from models.project import Project, AgentEvent, PipelineStage
from lib.streaming.sse import sse_manager
import logging

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all agents in the pipeline"""
    
    def __init__(self, api_key: str, stage: PipelineStage):
        self.api_key = api_key
        self.stage = stage
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def emit_event(
        self,
        project_id: str,
        event_type: str,
        data: Dict[str, Any]
    ) -> None:
        """Emit SSE event to frontend"""
        await sse_manager.send_event(
            project_id,
            event_type,
            {
                "stage": self.stage.value,
                "data": data
            }
        )
        
        self.logger.info(f"[{self.stage.value}] {event_type}: {data}")
    
    @abstractmethod
    async def execute(self, project: Project, **kwargs) -> Project:
        """Execute agent logic and return updated project"""
        pass
    
    async def on_error(self, project: Project, error: Exception) -> Project:
        """Handle errors during execution"""
        project.error = str(error)
        project.current_stage = PipelineStage.FAILED
        
        await self.emit_event(
            project.id,
            "agent_error",
            {
                "agent": self.__class__.__name__,
                "error": str(error),
                "stage": self.stage.value
            }
        )
        
        return project
