from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List
from datetime import datetime, timezone

# Import Ark IDE components
from models.session import Session, SessionCreate, ApprovalRequest
from models.todo import Todo, TodoCreate, TodoUpdate
from lib.runtime.agent_runner import AgentRunner
from lib.streaming.sse import sse_manager
from lib.tools.registry import tool_registry
from lib.tools.enhanced_registry import enhanced_tool_registry
from lib.workflows.engine import WorkflowEngine, WorkflowType
from lib.multi_agent.coordinator import AgentCoordinator, AgentRole
from lib.diff.engine import diff_engine
from lib.summary.generator import ExecutionSummaryGenerator

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI()

# Create API router
api_router = APIRouter(prefix="/api")

# Initialize agent runner and enhanced registry
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
agent_runner = AgentRunner(api_key=EMERGENT_LLM_KEY, db=db)
summary_generator = ExecutionSummaryGenerator(api_key=EMERGENT_LLM_KEY)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============ ARK IDE API ENDPOINTS ============

@api_router.get("/")
async def root():
    return {"message": "Ark IDE API", "version": "1.0.0"}


@api_router.post("/sessions", response_model=dict)
async def create_session(input: SessionCreate):
    """Create a new agent session"""
    try:
        session = Session(
            user_prompt=input.user_prompt,
            workspace_path=input.workspace_path or "/app",
            status="created"
        )

        # Save to database
        session_dict = session.model_dump()
        session_dict['created_at'] = session_dict['created_at'].isoformat()
        session_dict['completed_at'] = None
        session_dict['steps'] = []

        await db.sessions.insert_one(session_dict)

        logger.info(f"Created session: {session.id}")

        return {
            "session_id": session.id,
            "status": session.status,
            "user_prompt": session.user_prompt
        }
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/sessions")
async def list_sessions(limit: int = 50):
    """List all sessions"""
    try:
        sessions = await db.sessions.find({}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
        return {"sessions": sessions, "count": len(sessions)}
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session details"""
    try:
        session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/sessions/{session_id}/execute")
async def execute_session(session_id: str, background_tasks: BackgroundTasks):
    """Start executing an agent session"""
    try:
        # Get session from database
        session_data = await db.sessions.find_one({"id": session_id}, {"_id": 0})
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        # Convert to Session object
        session = Session(**session_data)

        if session.status not in ["created", "paused"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot execute session in status: {session.status}"
            )

        # Create SSE stream
        sse_manager.create_stream(session_id)

        # Start execution in background
        background_tasks.add_task(agent_runner.run, session)

        logger.info(f"Started execution for session: {session_id}")

        return {"message": "Execution started", "session_id": session_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/sessions/{session_id}/stream")
async def stream_session(session_id: str):
    """Stream session execution events via SSE"""
    try:
        # Verify session exists
        session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return StreamingResponse(
            sse_manager.event_generator(session_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/sessions/{session_id}/approve")
async def approve_action(session_id: str, approval: ApprovalRequest, background_tasks: BackgroundTasks):
    """Approve or reject a pending action"""
    try:
        # Get session
        session_data = await db.sessions.find_one({"id": session_id}, {"_id": 0})
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        session = Session(**session_data)

        if session.status != "awaiting_approval":
            raise HTTPException(
                status_code=400,
                detail=f"Session is not awaiting approval. Status: {session.status}"
            )

        # Resume execution with approval decision
        background_tasks.add_task(
            agent_runner.resume_after_approval,
            session,
            approval.approved,
            approval.modified_args
        )

        logger.info(f"Approval processed for session {session_id}: approved={approval.approved}")

        return {
            "message": "Approval processed",
            "approved": approval.approved,
            "session_id": session_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing approval: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/tools")
async def list_tools():
    """List available tools"""
    return {
        "tools": enhanced_tool_registry.get_tool_schemas(),
        "count": len(enhanced_tool_registry.tools)
    }


# ============ TODO APP ENDPOINTS ============

@api_router.get("/todos")
async def list_todos(limit: int = 200):
    """List todos"""
    try:
        todos = await db.todos.find({}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
        return {"todos": todos, "count": len(todos)}
    except Exception as e:
        logger.error(f"Error listing todos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/todos", response_model=dict)
async def create_todo(input: TodoCreate):
    """Create a todo"""
    try:
        todo = Todo(title=input.title, description=input.description)
        todo_dict = todo.model_dump()
        todo_dict["created_at"] = todo_dict["created_at"].isoformat()
        todo_dict["updated_at"] = todo_dict["updated_at"].isoformat()

        await db.todos.insert_one(todo_dict)

        return {"todo": todo_dict}
    except Exception as e:
        logger.error(f"Error creating todo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/todos/{todo_id}")
async def get_todo(todo_id: str):
    """Get a todo"""
    try:
        todo = await db.todos.find_one({"id": todo_id}, {"_id": 0})
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
        return {"todo": todo}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting todo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.patch("/todos/{todo_id}")
async def update_todo(todo_id: str, input: TodoUpdate):
    """Update a todo"""
    try:
        existing = await db.todos.find_one({"id": todo_id}, {"_id": 0})
        if not existing:
            raise HTTPException(status_code=404, detail="Todo not found")

        update_doc = {k: v for k, v in input.model_dump().items() if v is not None}
        update_doc["updated_at"] = datetime.now(timezone.utc).isoformat()

        await db.todos.update_one({"id": todo_id}, {"$set": update_doc})
        todo = await db.todos.find_one({"id": todo_id}, {"_id": 0})
        return {"todo": todo}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating todo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/todos/{todo_id}")
async def delete_todo(todo_id: str):
    """Delete a todo"""
    try:
        result = await db.todos.delete_one({"id": todo_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Todo not found")
        return {"deleted": True, "todo_id": todo_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting todo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ WORKFLOW ENDPOINTS ============

@api_router.get("/workflows")
async def list_workflows():
    """List available workflows"""
    workflows = WorkflowEngine.list_workflows()
    return {
        "workflows": [w.dict() for w in workflows],
        "count": len(workflows)
    }


@api_router.post("/workflows/{workflow_type}/execute")
async def execute_workflow(
    workflow_type: str,
    context: str = "",
    background_tasks: BackgroundTasks = None
):
    """Execute a predefined workflow"""
    try:
        wf_type = WorkflowType(workflow_type)
        workflow = WorkflowEngine.get_workflow(wf_type)

        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        # Convert workflow to prompt
        prompt = WorkflowEngine.workflow_to_prompt(wf_type, context)

        # Create session with workflow prompt
        session = Session(
            user_prompt=prompt,
            workspace_path="/app",
            status="created"
        )

        session_dict = session.model_dump()
        session_dict['created_at'] = session_dict['created_at'].isoformat()
        session_dict['completed_at'] = None
        session_dict['steps'] = []
        session_dict['plan'] = workflow.description

        await db.sessions.insert_one(session_dict)

        return {
            "session_id": session.id,
            "workflow": workflow.dict(),
            "status": "created"
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid workflow type")
    except Exception as e:
        logger.error(f"Error executing workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ MULTI-AGENT ENDPOINTS ============

@api_router.get("/agents")
async def list_agents():
    """List available agent roles"""
    profiles = []
    for role in AgentRole:
        profile = AgentCoordinator.get_profile(role)
        profiles.append({
            "role": role.value,
            "description": profile.system_message.split('\n')[0],
            "capabilities": profile.capabilities
        })
    return {"agents": profiles, "count": len(profiles)}


@api_router.post("/sessions/{session_id}/assign-agent")
async def assign_agent_to_session(session_id: str, role: str):
    """Assign a specific agent role to a session"""
    try:
        agent_role = AgentRole(role)

        # Update session with agent role
        await db.sessions.update_one(
            {"id": session_id},
            {"$set": {"agent_role": agent_role.value}}
        )

        return {
            "session_id": session_id,
            "agent_role": agent_role.value,
            "message": f"Session assigned to {agent_role.value} agent"
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid agent role")
    except Exception as e:
        logger.error(f"Error assigning agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ DIFF & SUMMARY ENDPOINTS ============

@api_router.post("/diff")
async def generate_diff(
    original_content: str,
    new_content: str,
    filename: str = "file"
):
    """Generate diff between two file versions"""
    try:
        unified_diff = diff_engine.generate_unified_diff(
            original_content,
            new_content,
            filename
        )

        side_by_side = diff_engine.generate_side_by_side_diff(
            original_content,
            new_content
        )

        summary = diff_engine.get_file_change_summary(side_by_side)

        return {
            "unified_diff": unified_diff,
            "side_by_side_diff": side_by_side,
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error generating diff: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/sessions/{session_id}/summary")
async def get_execution_summary(session_id: str):
    """Get AI-generated execution summary for a session"""
    try:
        session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if session['status'] not in ["completed", "failed", "cancelled"]:
            return {
                "session_id": session_id,
                "summary": f"Session is {session['status']}. Summary will be generated when complete.",
                "status": session['status']
            }

        summary = await summary_generator.generate_summary(
            session_id=session_id,
            user_prompt=session['user_prompt'],
            steps=session.get('steps', []),
            final_status=session['status']
        )

        return {
            "session_id": session_id,
            "summary": summary,
            "status": session['status']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/sessions/{session_id}/file-changes")
async def get_file_changes(session_id: str):
    """Get list of files changed during session"""
    try:
        session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        file_changes = []
        for step in session.get('steps', []):
            tool_call = step.get('tool_call')
            if tool_call and tool_call.get('tool_name') == 'write_file':
                args = tool_call.get('arguments', {})
                result = tool_call.get('result', {}).get('result', {})

                file_changes.append({
                    "path": args.get('path'),
                    "timestamp": step.get('timestamp'),
                    "step_number": step.get('step_number'),
                    "original_content": result.get('original_content'),
                    "bytes_written": result.get('bytes_written')
                })

        return {
            "session_id": session_id,
            "file_changes": file_changes,
            "count": len(file_changes)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file changes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
