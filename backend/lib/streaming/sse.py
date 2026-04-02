import asyncio
import json
from datetime import datetime
from typing import Dict, List, AsyncGenerator, Optional, Any
import logging

logger = logging.getLogger(__name__)


class SSEManager:
    """Server-Sent Events manager for real-time pipeline updates."""

    def __init__(self):
        self._queues: Dict[str, List[asyncio.Queue]] = {}

    def subscribe(self, project_id: str) -> asyncio.Queue:
        """Subscribe to events for a project."""
        if project_id not in self._queues:
            self._queues[project_id] = []
        queue = asyncio.Queue(maxsize=100)
        self._queues[project_id].append(queue)
        logger.info(f"SSE subscriber added for project {project_id}. Total: {len(self._queues[project_id])}")
        return queue

    def unsubscribe(self, project_id: str, queue: asyncio.Queue):
        """Unsubscribe from project events."""
        if project_id in self._queues:
            try:
                self._queues[project_id].remove(queue)
                if not self._queues[project_id]:
                    del self._queues[project_id]
            except ValueError:
                pass

    async def emit(
        self,
        project_id: str,
        event_type: str,
        agent: str = "",
        stage: int = 0,
        message: str = "",
        data: Optional[Dict[str, Any]] = None,
    ):
        """Emit an SSE event to all subscribers of a project."""
        event = {
            "event_type": event_type,
            "agent": agent,
            "stage": stage,
            "message": message,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        if project_id not in self._queues:
            return

        dead_queues = []
        for queue in self._queues[project_id]:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning(f"SSE queue full for project {project_id}, dropping event")
            except Exception as e:
                logger.error(f"Error emitting SSE event: {e}")
                dead_queues.append(queue)

        for q in dead_queues:
            self.unsubscribe(project_id, q)

    async def stream(
        self, project_id: str, queue: asyncio.Queue
    ) -> AsyncGenerator[str, None]:
        """Stream SSE events from queue."""
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(event)}\n\n"

                    if event.get("event_type") in ["pipeline_complete", "error"]:
                        yield f"data: {json.dumps({'event_type': 'stream_end', 'timestamp': datetime.utcnow().isoformat() + 'Z'})}\n\n"
                        break
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'event_type': 'heartbeat', 'timestamp': datetime.utcnow().isoformat() + 'Z'})}\n\n"
        except asyncio.CancelledError:
            logger.info(f"SSE stream cancelled for project {project_id}")
        finally:
            self.unsubscribe(project_id, queue)


# Global SSE manager instance
sse_manager = SSEManager()
