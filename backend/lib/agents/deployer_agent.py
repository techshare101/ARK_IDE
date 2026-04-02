from lib.agents.base_agent import BaseAgent
from models.project import Project, Artifact, PipelineStage
from lib.sandbox.e2b_manager import E2BSandboxManager
import logging
import asyncio

logger = logging.getLogger(__name__)

class DeployerAgent(BaseAgent):
    """Deploys the application and provides preview URL"""
    
    def __init__(self, api_key: str, sandbox_manager: E2BSandboxManager):
        super().__init__(api_key, PipelineStage.DEPLOYING)
        self.sandbox_manager = sandbox_manager
    
    async def execute(self, project: Project, **kwargs) -> Project:
        """Start server and get preview URL"""
        try:
            await self.emit_event(
                project.id,
                "deploy_started",
                {"sandbox_id": project.sandbox_id}
            )
            
            sandbox = await self.sandbox_manager.get_sandbox(project.id)
            if not sandbox:
                raise ValueError("Sandbox not found")
            
            # Determine how to start the server
            start_command, port = self._get_start_command(project)
            
            await self.emit_event(
                project.id,
                "starting_server",
                {"command": start_command, "port": port}
            )
            
            # Start server
            preview_url = await self.sandbox_manager.start_server(
                sandbox,
                port=port,
                command=start_command
            )
            
            project.preview_url = preview_url
            
            # Record deployment artifact
            artifact = Artifact(
                artifact_type="url",
                name="preview_url",
                content=preview_url,
                metadata={
                    "port": port,
                    "command": start_command
                }
            )
            project.artifacts.append(artifact)
            
            project.current_stage = PipelineStage.MONITORING
            
            await self.emit_event(
                project.id,
                "preview_url",
                {
                    "url": preview_url,
                    "port": port
                }
            )
            
            return project
            
        except Exception as e:
            logger.error(f"DeployerAgent failed: {str(e)}")
            return await self.on_error(project, e)
    
    def _get_start_command(self, project: Project) -> tuple[str, int]:
        """Determine server start command and port"""
        if not project.execution_plan:
            return ("python -m http.server 3000", 3000)
        
        tech_stack = project.execution_plan.tech_stack
        
        # React/Node.js
        if "React" in tech_stack:
            return ("cd /home/user/project && npm start", 3000)
        
        # FastAPI/Python
        elif "FastAPI" in tech_stack:
            return ("cd /home/user/project && uvicorn main:app --host 0.0.0.0 --port 8000", 8000)
        
        # Node.js/Express
        elif "Node.js" in tech_stack or "Express" in tech_stack:
            return ("cd /home/user/project && node server.js", 3000)
        
        # Python Flask
        elif "Flask" in tech_stack:
            return ("cd /home/user/project && python app.py", 5000)
        
        # Default: static file server
        else:
            return ("cd /home/user/project && python -m http.server 3000", 3000)
