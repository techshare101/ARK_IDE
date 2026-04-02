from models.session import Session, Step, ToolCall
from lib.runtime.planner import Planner
from lib.tools.registry import tool_registry
from lib.streaming.sse import sse_manager
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

class AgentRunner:
    def __init__(self, api_key: str, db):
        self.planner = Planner(api_key)
        self.tool_registry = tool_registry
        self.db = db
        self.max_steps = 50  # Safety limit
    
    async def run(self, session: Session):
        """Main agent execution loop"""
        try:
            # Update session status
            session.status = "running"
            await self._update_session(session)
            
            # Send initial event
            await sse_manager.send_event(
                session.id,
                "started",
                {"session_id": session.id, "prompt": session.user_prompt}
            )
            
            # Main loop: think → act → observe → repeat
            while session.current_step < self.max_steps:
                session.current_step += 1
                
                # Get history for context
                history = [self._step_to_dict(s) for s in session.steps]
                
                # THINK: Get next decision from planner
                await sse_manager.send_event(
                    session.id,
                    "thinking",
                    {"step": session.current_step, "message": "Planning next action..."}
                )
                
                decision = await self.planner.plan_next_step(
                    session_id=session.id,
                    user_prompt=session.user_prompt,
                    history=history,
                    tool_schemas=self.tool_registry.get_tool_schemas()
                )
                
                # Log thought
                thought = decision.get("thought", "")
                await sse_manager.send_event(
                    session.id,
                    "thought",
                    {"step": session.current_step, "thought": thought}
                )
                
                # Create step record
                step = Step(
                    session_id=session.id,
                    step_number=session.current_step,
                    type=decision.get("action", "unknown"),
                    content=thought
                )
                
                action = decision.get("action")
                
                # ACT: Execute based on decision
                if action == "tool":
                    # Tool execution
                    tool_name = decision.get("tool_name")
                    tool_args = decision.get("tool_args", {})
                    
                    # Check if approval needed
                    if tool_name == "run_command":
                        # Request approval
                        step.type = "approval_required"
                        session.steps.append(step)
                        await self._update_session(session)
                        
                        await sse_manager.send_event(
                            session.id,
                            "approval_required",
                            {
                                "step": session.current_step,
                                "tool_name": tool_name,
                                "tool_args": tool_args,
                                "reason": decision.get("thought", "")
                            }
                        )
                        
                        # Pause execution - will resume when approved
                        session.status = "awaiting_approval"
                        await self._update_session(session)
                        return
                    
                    # Execute tool
                    await sse_manager.send_event(
                        session.id,
                        "tool_call",
                        {
                            "step": session.current_step,
                            "tool_name": tool_name,
                            "arguments": tool_args
                        }
                    )
                    
                    result = await self.tool_registry.execute(
                        tool_name=tool_name,
                        arguments=tool_args,
                        workspace_path=session.workspace_path
                    )
                    
                    # Create tool call record
                    tool_call = ToolCall(
                        session_id=session.id,
                        step_number=session.current_step,
                        tool_name=tool_name,
                        arguments=tool_args,
                        result=result,
                        status="completed" if result.get("success") else "failed"
                    )
                    
                    step.tool_call = tool_call
                    
                    # Send result
                    await sse_manager.send_event(
                        session.id,
                        "tool_result",
                        {
                            "step": session.current_step,
                            "tool_name": tool_name,
                            "result": result,
                            "success": result.get("success", False)
                        }
                    )
                    
                elif action == "done":
                    # Task completed
                    summary = decision.get("summary", "Task completed")
                    step.type = "done"
                    step.content = summary
                    session.steps.append(step)
                    
                    session.status = "completed"
                    session.completed_at = datetime.now(timezone.utc)
                    await self._update_session(session)
                    
                    await sse_manager.send_event(
                        session.id,
                        "done",
                        {
                            "step": session.current_step,
                            "summary": summary
                        }
                    )
                    break
                    
                elif action == "error":
                    # Error occurred
                    error = decision.get("error", "Unknown error")
                    step.type = "error"
                    step.content = error
                    session.steps.append(step)
                    
                    session.status = "failed"
                    session.error = error
                    await self._update_session(session)
                    
                    await sse_manager.send_event(
                        session.id,
                        "error",
                        {"step": session.current_step, "error": error}
                    )
                    break
                
                # Add step to session
                session.steps.append(step)
                await self._update_session(session)
                
                # Brief pause between steps
                await asyncio.sleep(0.5)
            
            # Max steps reached
            if session.current_step >= self.max_steps:
                session.status = "failed"
                session.error = "Maximum steps reached"
                await self._update_session(session)
                
                await sse_manager.send_event(
                    session.id,
                    "error",
                    {"error": "Maximum steps reached"}
                )
        
        except Exception as e:
            logger.error(f"Agent execution error: {str(e)}", exc_info=True)
            session.status = "failed"
            session.error = str(e)
            await self._update_session(session)
            
            await sse_manager.send_event(
                session.id,
                "error",
                {"error": str(e)}
            )
    
    async def resume_after_approval(self, session: Session, approved: bool, modified_args: Optional[dict] = None):
        """Resume execution after approval decision"""
        if not approved:
            # Rejected - mark as cancelled
            session.status = "cancelled"
            await self._update_session(session)
            
            await sse_manager.send_event(
                session.id,
                "done",
                {"summary": "Task cancelled by user"}
            )
            return
        
        # Approved - execute the command
        last_step = session.steps[-1]
        if last_step.type != "approval_required":
            return
        
        # Get the pending tool call details from the step content
        # This would be stored when approval was requested
        # For now, we'll need to store it in a temp collection or session state
        # Simplified: just resume the agent loop
        session.status = "running"
        await self._update_session(session)
        
        # Continue execution
        await self.run(session)
    
    async def _update_session(self, session: Session):
        """Update session in database"""
        session_dict = session.model_dump()
        # Convert datetime to ISO string
        session_dict['created_at'] = session_dict['created_at'].isoformat()
        if session_dict.get('completed_at'):
            session_dict['completed_at'] = session_dict['completed_at'].isoformat()
        
        # Convert steps
        for step in session_dict.get('steps', []):
            step['timestamp'] = step['timestamp'].isoformat()
            if step.get('tool_call'):
                step['tool_call']['timestamp'] = step['tool_call']['timestamp'].isoformat()
        
        await self.db.sessions.update_one(
            {"id": session.id},
            {"$set": session_dict},
            upsert=True
        )
    
    def _step_to_dict(self, step: Step) -> dict:
        """Convert Step to dict for context"""
        return {
            "type": step.type,
            "content": step.content,
            "tool_call": {
                "tool_name": step.tool_call.tool_name,
                "arguments": step.tool_call.arguments,
                "result": step.tool_call.result
            } if step.tool_call else None
        }
