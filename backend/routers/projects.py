import asyncio
import logging
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from sse_starlette.sse import EventSourceResponse

from models.session import Project, CreateProjectRequest, PipelineStage
from lib.streaming.sse import sse_manager
from lib.workflows.pipeline import get_pipeline_runner, PipelineRunner

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["projects"])

# In-memory project store
_projects: Dict[str, Project] = {}


def _get_project_or_404(project_id: str) -> Project:
    project = _projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id!r} not found")
    return project


@router.post("/", response_model=Dict[str, Any], status_code=202)
async def create_project(
    body: CreateProjectRequest,
    background_tasks: BackgroundTasks,
    runner: PipelineRunner = Depends(get_pipeline_runner),
) -> Dict[str, Any]:
    """Create a new project and start the build pipeline."""
    if not body.goal or not body.goal.strip():
        raise HTTPException(status_code=422, detail="goal must not be empty")
    project = Project(goal=body.goal.strip())
    _projects[project.id] = project
    logger.info(f"Created project {project.id}: {project.goal!r}")
    background_tasks.add_task(_run_pipeline, runner, project)
    created = project.created_at.isoformat() + "Z"
    return {
        "project_id": project.id,
        "goal": project.goal,
        "stage": project.stage,
        "stream_url": f"/projects/{project.id}/stream",
        "created_at": created,
        "message": "Pipeline started. Subscribe to stream_url for live updates.",
    }


async def _run_pipeline(runner: PipelineRunner, project: Project):
    """Background task: run pipeline and update in-memory store."""
    try:
        task = await runner.start(project)
        result = await task
        if result and isinstance(result, Project):
            _projects[project.id] = result
    except Exception as e:
        logger.error(f"Pipeline background task error for {project.id}: {e}")
        project.stage = PipelineStage.FAILED
        project.error = str(e)
        _projects[project.id] = project


@router.get("/", response_model=List[Dict[str, Any]])
async def list_projects(
    stage: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """List all projects, optionally filtered by pipeline stage."""
    projects = list(_projects.values())
    if stage:
        try:
            filter_stage = PipelineStage(stage)
            projects = [p for p in projects if p.stage == filter_stage]
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid stage: {stage!r}")
    projects.sort(key=lambda p: p.created_at, reverse=True)
    projects = projects[offset: offset + limit]
    return [_project_summary(p) for p in projects]


@router.get("/{project_id}", response_model=Dict[str, Any])
async def get_project(project_id: str) -> Dict[str, Any]:
    """Get full project details."""
    project = _get_project_or_404(project_id)
    return _project_detail(project)


@router.get("/{project_id}/stream")
async def stream_project_events(
    project_id: str,
    request: Request,
) -> EventSourceResponse:
    """SSE stream for real-time pipeline updates."""
    _get_project_or_404(project_id)
    queue = sse_manager.subscribe(project_id)

    async def event_generator():
        try:
            async for chunk in sse_manager.stream(project_id, queue):
                if await request.is_disconnected():
                    logger.info(f"SSE client disconnected for {project_id}")
                    break
                yield chunk
        except asyncio.CancelledError:
            pass
        finally:
            sse_manager.unsubscribe(project_id, queue)

    return EventSourceResponse(event_generator())


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    runner: PipelineRunner = Depends(get_pipeline_runner),
) -> None:
    """Delete a project. Cancels any running pipeline first."""
    _get_project_or_404(project_id)
    if runner.is_running(project_id):
        await runner.cancel(project_id)
    del _projects[project_id]
    logger.info(f"Project {project_id} deleted")


@router.post("/{project_id}/cancel", response_model=Dict[str, Any])
async def cancel_project(
    project_id: str,
    runner: PipelineRunner = Depends(get_pipeline_runner),
) -> Dict[str, Any]:
    """Cancel a running pipeline."""
    project = _get_project_or_404(project_id)
    if not runner.is_running(project_id):
        return {
            "project_id": project_id,
            "cancelled": False,
            "message": "Pipeline is not currently running",
            "stage": project.stage,
        }
    cancelled = await runner.cancel(project_id)
    if cancelled:
        project.stage = PipelineStage.FAILED
        project.error = "Cancelled by user"
        _projects[project_id] = project
    return {
        "project_id": project_id,
        "cancelled": cancelled,
        "message": "Pipeline cancelled" if cancelled else "Could not cancel",
        "stage": project.stage,
    }

@router.get("/{project_id}/files", response_model=List[Dict[str, Any]])
async def list_project_files(project_id: str) -> List[Dict[str, Any]]:
    """List all files generated for a project."""
    project = _get_project_or_404(project_id)
    result = []
    for f in project.file_manifest:
        result.append({
            "path": f.path,
            "size": f.size,
            "created_at": f.created_at.isoformat() + "Z",
        })
    return result


@router.get("/{project_id}/files/{file_path:path}", response_model=Dict[str, Any])
async def get_project_file(project_id: str, file_path: str) -> Dict[str, Any]:
    """Get the content of a specific generated file."""
    project = _get_project_or_404(project_id)
    for f in project.file_manifest:
        norm_stored = f.path.lstrip("/")
        norm_req = file_path.lstrip("/")
        if norm_stored == norm_req:
            return {
                "path": f.path,
                "content": f.content,
                "size": f.size,
                "created_at": f.created_at.isoformat() + "Z",
            }
    raise HTTPException(status_code=404, detail=f"File {file_path!r} not found")


# ------------------------------------------------------------------ #
#  Serialization helpers                                               #
# ------------------------------------------------------------------ #

def _project_summary(project: Project) -> Dict[str, Any]:
    """Compact project representation for list views."""
    deploy_url = None
    if project.deploy_info:
        deploy_url = project.deploy_info.deploy_url
    return {
        "id": project.id,
        "goal": project.goal,
        "name": project.name,
        "stage": project.stage,
        "file_count": len(project.file_manifest),
        "iterations": project.iterations,
        "created_at": project.created_at.isoformat() + "Z",
        "updated_at": project.updated_at.isoformat() + "Z",
        "error": project.error,
        "deploy_url": deploy_url,
    }


def _project_detail(project: Project) -> Dict[str, Any]:
    """Full project representation including task tree and results."""
    # Deploy info
    deploy = None
    if project.deploy_info:
        di = project.deploy_info
        deployed_at = di.deployed_at.isoformat() + "Z" if di.deployed_at else None
        deploy = {
            "sandbox_id": di.sandbox_id,
            "preview_url": di.preview_url,
            "deploy_url": di.deploy_url,
            "port": di.port,
            "status": di.status,
            "deployed_at": deployed_at,
        }

    # Test results
    test_results = None
    if project.test_results:
        tr = project.test_results
        test_results = {
            "passed": tr.passed,
            "failed": tr.failed,
            "errors": tr.errors,
            "coverage": tr.coverage,
            "success": tr.success,
            "output": tr.output[:2000],
        }

    # Task tree
    task_tree = None
    if project.task_tree:
        tt = project.task_tree
        tasks_out = []
        for t in tt.tasks:
            tasks_out.append({
                "id": t.id,
                "type": t.type,
                "description": t.description,
                "file_path": t.file_path,
                "status": t.status,
                "output": t.output,
                "error": t.error,
            })
        task_tree = {
            "project_name": tt.project_name,
            "tech_stack": tt.tech_stack,
            "test_command": tt.test_command,
            "run_command": tt.run_command,
            "estimated_files": tt.estimated_files,
            "tasks": tasks_out,
        }

    # File manifest
    files_out = []
    for f in project.file_manifest:
        files_out.append({
            "path": f.path,
            "size": f.size,
            "created_at": f.created_at.isoformat() + "Z",
        })

    # Agent runs
    runs_out = []
    for r in project.agent_runs:
        completed = r.completed_at.isoformat() + "Z" if r.completed_at else None
        runs_out.append({
            "agent": r.agent,
            "stage": r.stage,
            "status": r.status,
            "started_at": r.started_at.isoformat() + "Z",
            "completed_at": completed,
            "error": r.error,
        })

    return {
        "id": project.id,
        "goal": project.goal,
        "name": project.name,
        "stage": project.stage,
        "error": project.error,
        "iterations": project.iterations,
        "sandbox_id": project.sandbox_id,
        "task_tree": task_tree,
        "file_manifest": files_out,
        "test_results": test_results,
        "deploy_info": deploy,
        "agent_runs": runs_out,
        "created_at": project.created_at.isoformat() + "Z",
        "updated_at": project.updated_at.isoformat() + "Z",
    }
