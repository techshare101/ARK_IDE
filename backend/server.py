from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List

# Import Ark IDE components
from models.session import Session, SessionCreate, ApprovalRequest
from lib.runtime.agent_runner import AgentRunner
from lib.streaming.sse import sse_manager
from lib.tools.registry import tool_registry

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

# Initialize agent runner
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
agent_runner = AgentRunner(api_key=EMERGENT_LLM_KEY, db=db)

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
        "tools": tool_registry.get_tool_schemas(),
        "count": len(tool_registry.tools)
    }


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
