from lib.agents.base_agent import BaseAgent
from models.project import Project, PipelineStage
from lib.sandbox.e2b_manager import E2BSandboxManager
import logging
import httpx
import asyncio

logger = logging.getLogger(__name__)

class MonitorAgent(BaseAgent):
    """Monitors deployed application and handles retries"""
    
    def __init__(self, api_key: str, sandbox_manager: E2BSandboxManager):
        super().__init__(api_key, PipelineStage.MONITORING)
        self.sandbox_manager = sandbox_manager
    
    async def execute(self, project: Project, **kwargs) -> Project:
        """Monitor application health and complete pipeline"""
        try:
            await self.emit_event(
                project.id,
                "monitoring_started",
                {"preview_url": project.preview_url}
            )
            
            # Perform health check
            if project.preview_url:
                is_healthy = await self._health_check(project.preview_url)
                
                await self.emit_event(
                    project.id,
                    "health_check",
                    {"healthy": is_healthy, "url": project.preview_url}
                )
                
                if not is_healthy:
                    logger.warning(f"Health check failed for {project.preview_url}")
                    # Could trigger retry here if needed
            
            # Pipeline complete!
            project.current_stage = PipelineStage.COMPLETED
            
            await self.emit_event(
                project.id,
                "pipeline_complete",
                {
                    "status": "success",
                    "preview_url": project.preview_url,
                    "artifacts_count": len(project.artifacts),
                    "tasks_completed": len([t for t in project.execution_plan.tasks if t.status == "completed"])
                }
            )
            
            return project
            
        except Exception as e:
            logger.error(f"MonitorAgent failed: {str(e)}")
            return await self.on_error(project, e)
    
    async def _health_check(self, url: str, retries: int = 5) -> bool:
        """Check if the deployed app is responding"""
        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(url)
                    if response.status_code == 200:
                        logger.info(f"Health check passed: {url}")
                        return True
            except (httpx.ConnectError, httpx.TimeoutException):
                if attempt < retries - 1:
                    await asyncio.sleep(2)
                continue
        
        logger.error(f"Health check failed after {retries} attempts")
        return False
