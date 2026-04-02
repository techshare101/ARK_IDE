from fastapi import Request
from fastapi.responses import StreamingResponse
import asyncio
import json
from typing import AsyncGenerator, Dict, Any

class SSEManager:
    def __init__(self):
        self.connections: Dict[str, asyncio.Queue] = {}
    
    def create_stream(self, session_id: str) -> asyncio.Queue:
        """Create a new event stream for a session"""
        queue = asyncio.Queue()
        self.connections[session_id] = queue
        return queue
    
    async def send_event(self, session_id: str, event_type: str, data: Dict[str, Any]):
        """Send an event to a specific session stream"""
        if session_id in self.connections:
            await self.connections[session_id].put({
                "event": event_type,
                "data": data
            })
    
    async def event_generator(self, session_id: str) -> AsyncGenerator[str, None]:
        """Generate SSE formatted events"""
        queue = self.connections.get(session_id)
        if not queue:
            return
        
        try:
            while True:
                # Wait for event with timeout
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    
                    # Format as SSE
                    event_type = event.get("event", "message")
                    data = json.dumps(event.get("data", {}))
                    
                    yield f"event: {event_type}\n"
                    yield f"data: {data}\n\n"
                    
                    # Check if this is a completion event
                    if event_type in ["done", "error", "failed"]:
                        break
                        
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield ": keepalive\n\n"
                    
        except asyncio.CancelledError:
            pass
        finally:
            # Cleanup
            if session_id in self.connections:
                del self.connections[session_id]
    
    def close_stream(self, session_id: str):
        """Close a stream"""
        if session_id in self.connections:
            del self.connections[session_id]

# Global SSE manager
sse_manager = SSEManager()
