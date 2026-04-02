import asyncio
import logging
from typing import Optional, Dict
from datetime import datetime

from models.session import Project, PipelineStage
from lib.multi_agent.orchestrator import PipelineOrchestrator
from lib.streaming.sse import SSEManager

logger = logging.getLogger(__name__)


class PipelineRunner:
    """Manages concurrent pipeline executions with lifecycle tracking."""

    def __init__(self, sse_manager: SSEManager, db=None):
        self._sse = sse_manager
        self._db = db
        self._active: Dict[str, asyncio.Task] = {}

    async def start(self, project: Project) -> asyncio.Task:
        """Start a pipeline run for a project in the background."""
        if project.id in self._active:
            existing = self._active[project.id]
            if not existing.done():
                logger.warning(f"Pipeline already running for {project.id}")
                return existing

        orchestrator = PipelineOrchestrator(
            sse_manager=self._sse,
            db=self._db,
        )

        task = asyncio.create_task(
            self._run_with_cleanup(orchestrator, project),
            name=f"pipeline-{project.id}",
        )
        self._active[project.id] = task
        logger.info(f"Pipeline task created for project {project.id}")
        return task

    async def _run_with_cleanup(self, orchestrator: PipelineOrchestrator, project: Project) -> Project:
        """Run pipeline and clean up active task registry on completion."""
        try:
            result = await orchestrator.run(project)
            return result
        except asyncio.CancelledError:
            logger.info(f"Pipeline cancelled for project {project.id}")
            project.stage = PipelineStage.FAILED
            project.error = "Pipeline cancelled"
            raise
        except Exception as e:
            logger.exception(f"Pipeline error for project {project.id}: {e}")
            project.stage = PipelineStage.FAILED
            project.error = str(e)
            return project
        finally:
            self._active.pop(project.id, None)

    def is_running(self, project_id: str) -> bool:
        """Check if a pipeline is currently running for a project."""
        task = self._active.get(project_id)
        return task is not None and not task.done()

    async def cancel(self, project_id: str) -> bool:
        """Cancel a running pipeline."""
        task = self._active.get(project_id)
        if task and not task.done():
            task.cancel()
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=5.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            logger.info(f"Pipeline cancelled for project {project_id}")
            return True
        return False

    def active_count(self) -> int:
        """Return number of currently running pipelines."""
        return sum(1 for t in self._active.values() if not t.done())

    def active_project_ids(self) -> list:
        """Return list of project IDs with active pipelines."""
        return [pid for pid, t in self._active.items() if not t.done()]


# Module-level singleton — initialized in server.py lifespan
pipeline_runner: Optional[PipelineRunner] = None


def get_pipeline_runner() -> PipelineRunner:
    """FastAPI dependency to get the pipeline runner."""
    if pipeline_runner is None:
        raise RuntimeError("PipelineRunner not initialized. Check server lifespan.")
    return pipeline_runner
