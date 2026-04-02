from fastapi import APIRouter, HTTPException, BackgroundTasks
from models.project import Project, ProjectCreate, PipelineStage
from lib.orchestrator.pipeline import PipelineOrchestrator
from lib.sandbox.e2b_manager import E2BSandboxManager
from lib.streaming.sse import sse_manager
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])

# Global instances
_orchestrator: PipelineOrchestrator = None
_sandbox_manager: E2BSandboxManager = None

def get_orchestrator() -> PipelineOrchestrator:
    """Get or create pipeline orchestrator instance"""
    global _orchestrator, _sandbox_manager
    
    if _orchestrator is None:
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise ValueError("EMERGENT_LLM_KEY not configured")
        
        # Initialize E2B sandbox manager
        e2b_key = os.environ.get('E2B_API_KEY')
        if not e2b_key:
            raise ValueError("E2B_API_KEY not configured")
        
        _sandbox_manager = E2BSandboxManager(e2b_key)
        _orchestrator = PipelineOrchestrator(api_key, _sandbox_manager)
    
    return _orchestrator

@router.post("/run", response_model=Dict[str, Any])
async def run_pipeline(
    input: ProjectCreate,
    background_tasks: BackgroundTasks
):
    """
    Start autonomous pipeline: goal → plan → build → test → deploy → monitor
    
    Returns project_id for SSE streaming of progress
    """
    try:
        # Create project
        project = Project(
            goal=input.goal,
            current_stage=PipelineStage.PLANNING
        )
        
        logger.info(f"Created project {project.id}: {project.goal}")
        
        # Create SSE stream for this project
        sse_manager.create_stream(project.id)
        
        # Run pipeline in background
        orchestrator = get_orchestrator()
        background_tasks.add_task(
            orchestrator.run_pipeline,
            project
        )
        
        return {
            "project_id": project.id,
            "status": "pipeline_started",
            "stream_url": f"/api/pipeline/{project.id}/stream"
        }
        
    except Exception as e:
        logger.error(f"Failed to start pipeline: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{project_id}/stream")
async def stream_pipeline(project_id: str):
    """Stream pipeline events via SSE"""
    try:
        async def event_generator():
            async for event in sse_manager.subscribe(project_id):
                yield event
        
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        logger.error(f"Stream error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{project_id}/cleanup")
async def cleanup_project(project_id: str):
    """Manually cleanup project sandbox"""
    try:
        orchestrator = get_orchestrator()
        success = await orchestrator.sandbox_manager.cleanup_sandbox(project_id)
        
        return {
            "project_id": project_id,
            "cleaned_up": success
        }
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
