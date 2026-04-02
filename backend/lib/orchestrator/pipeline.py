from models.project import Project, PipelineStage
from lib.agents.planner_agent import PlannerAgent
from lib.agents.builder_agent import BuilderAgent
from lib.agents.tester_agent import TesterAgent
from lib.agents.deployer_agent import DeployerAgent
from lib.agents.monitor_agent import MonitorAgent
from lib.sandbox.e2b_manager import E2BSandboxManager
from lib.streaming.sse import sse_manager
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class PipelineOrchestrator:
    """Orchestrates the 5-agent pipeline: Planner → Builder → Tester → Deployer → Monitor"""
    
    def __init__(self, api_key: str, sandbox_manager: E2BSandboxManager):
        self.api_key = api_key
        self.sandbox_manager = sandbox_manager
        
        # Initialize all agents
        self.planner = PlannerAgent(api_key)
        self.builder = BuilderAgent(api_key, sandbox_manager)
        self.tester = TesterAgent(api_key, sandbox_manager)
        self.deployer = DeployerAgent(api_key, sandbox_manager)
        self.monitor = MonitorAgent(api_key, sandbox_manager)
        
        self.agents = {
            PipelineStage.PLANNING: self.planner,
            PipelineStage.BUILDING: self.builder,
            PipelineStage.TESTING: self.tester,
            PipelineStage.DEPLOYING: self.deployer,
            PipelineStage.MONITORING: self.monitor,
        }
    
    async def run_pipeline(self, project: Project) -> Project:
        """Execute complete pipeline from goal to deployed app"""
        try:
            logger.info(f"Starting pipeline for project: {project.id}")
            logger.info(f"Goal: {project.goal}")
            
            # Emit pipeline start event
            await sse_manager.send_event(
                project.id,
                "pipeline_started",
                {
                    "project_id": project.id,
                    "goal": project.goal,
                    "stages": [
                        stage.value for stage in [
                            PipelineStage.PLANNING,
                            PipelineStage.BUILDING,
                            PipelineStage.TESTING,
                            PipelineStage.DEPLOYING,
                            PipelineStage.MONITORING
                        ]
                    ]
                }
            )
            
            # Run through each stage
            stages_in_order = [
                PipelineStage.PLANNING,
                PipelineStage.BUILDING,
                PipelineStage.TESTING,
                PipelineStage.DEPLOYING,
                PipelineStage.MONITORING,
            ]
            
            for stage in stages_in_order:
                if project.current_stage == PipelineStage.FAILED:
                    logger.error(f"Pipeline failed at stage: {stage.value}")
                    break
                
                if project.current_stage == stage:
                    logger.info(f"Executing stage: {stage.value}")
                    
                    # Execute agent for this stage
                    agent = self.agents[stage]
                    project = await agent.execute(project)
                    
                    # Update project timestamp
                    project.updated_at = datetime.now(timezone.utc)
            
            # Mark completion time
            if project.current_stage == PipelineStage.COMPLETED:
                project.completed_at = datetime.now(timezone.utc)
                logger.info(f"Pipeline completed successfully for project: {project.id}")
                logger.info(f"Preview URL: {project.preview_url}")
            
            elif project.current_stage == PipelineStage.FAILED:
                logger.error(f"Pipeline failed for project: {project.id}")
                logger.error(f"Error: {project.error}")
                
                # Check if we should retry
                if project.retry_count < project.max_retries:
                    logger.info(f"Retry {project.retry_count + 1}/{project.max_retries}")
                    project.retry_count += 1
                    project.current_stage = PipelineStage.PLANNING
                    project.error = None
                    
                    await sse_manager.send_event(
                        project.id,
                        "agent_retry",
                        {
                            "attempt": project.retry_count,
                            "max_retries": project.max_retries,
                            "reason": "Pipeline failed, retrying from planning stage"
                        }
                    )
                    
                    # Retry pipeline
                    return await self.run_pipeline(project)
            
            return project
            
        except Exception as e:
            logger.error(f"Pipeline orchestrator error: {str(e)}")
            project.current_stage = PipelineStage.FAILED
            project.error = str(e)
            
            await sse_manager.send_event(
                project.id,
                "pipeline_error",
                {"error": str(e)}
            )
            
            return project
