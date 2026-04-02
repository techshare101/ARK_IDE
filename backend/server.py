import os
import logging
import sys
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from database import connect_db, disconnect_db
from lib.streaming.sse import sse_manager
from lib.workflows.pipeline import PipelineRunner
import lib.workflows.pipeline as pipeline_module
from routers import projects, health

# ------------------------------------------------------------------ #
#  Logging configuration                                               #
# ------------------------------------------------------------------ #

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
#  Application lifespan                                                #
# ------------------------------------------------------------------ #

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle manager."""
    logger.info("ARK IDE Backend v3.0.0 starting up...")

    # Connect to MongoDB (optional — degrades gracefully)
    db = await connect_db()
    if db is None:
        logger.warning("Running without MongoDB persistence")

    # Initialize pipeline runner
    pipeline_module.pipeline_runner = PipelineRunner(
        sse_manager=sse_manager,
        db=db,
    )
    logger.info("PipelineRunner initialized")

    logger.info("ARK IDE Backend ready to accept requests")
    yield

    # Shutdown
    logger.info("ARK IDE Backend shutting down...")
    runner = pipeline_module.pipeline_runner
    if runner:
        active = runner.active_project_ids()
        if active:
            logger.info(f"Cancelling {len(active)} active pipelines...")
            for pid in active:
                await runner.cancel(pid)

    await disconnect_db()
    logger.info("Shutdown complete")


# ------------------------------------------------------------------ #
#  FastAPI application                                                 #
# ------------------------------------------------------------------ #

app = FastAPI(
    title="ARK IDE Backend",
    description="Autonomous multi-agent software development pipeline",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ------------------------------------------------------------------ #
#  CORS middleware                                                      #
# ------------------------------------------------------------------ #

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "Cache-Control", "X-Accel-Buffering"],
)


# ------------------------------------------------------------------ #
#  Routers                                                             #
# ------------------------------------------------------------------ #

# Include routers
app.include_router(health.router, prefix="/api")
app.include_router(projects.router, prefix="/api")


# ------------------------------------------------------------------ #
#  Root endpoint                                                       #
# ------------------------------------------------------------------ #

@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": "ARK IDE Backend",
        "version": "3.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


# ------------------------------------------------------------------ #
#  Global exception handler                                            #
# ------------------------------------------------------------------ #

@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "detail": str(exc) if os.getenv("DEBUG") else "Contact support",
        },
    )


# ------------------------------------------------------------------ #
#  Entry point                                                         #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    reload = os.getenv("RELOAD", "false").lower() == "true"
    logger.info(f"Starting ARK IDE Backend on {host}:{port}")
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=reload,
        log_level=LOG_LEVEL.lower(),
        access_log=True,
    )
