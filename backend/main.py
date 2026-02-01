"""
Datasheet Part Selector - FastAPI Backend

Main application entry point with:
- CORS configuration
- Routing setup
- Database initialization
- SSE endpoint for progress updates (PDF-014)
"""
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from config import get_settings
from models import init_db
from routers import datasheets, parts, chat
from routers import settings as settings_router
from routers.part_builder import router as part_builder_router


app_settings = get_settings()

# Progress update queues for SSE (PDF-014)
progress_queues: dict[str, asyncio.Queue] = {}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan - startup and shutdown"""
    # Startup
    print("🚀 Starting Datasheet Part Selector API...")
    await init_db(app_settings.database_url)
    print("✅ Database initialized")
    
    # Ensure datasheets directory exists
    app_settings.datasheets_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Datasheets directory: {app_settings.datasheets_dir}")
    
    yield
    
    # Shutdown
    print("👋 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Datasheet Part Selector API",
    description="Transform dense PDF datasheets into interactive part configurators",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(datasheets.router, prefix="/api/datasheets", tags=["Datasheets"])
app.include_router(parts.router, prefix="/api/parts", tags=["Parts"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["Settings"])
app.include_router(part_builder_router, tags=["Part Builder"])


# ============ SSE Progress Endpoint (PDF-014) ============

async def progress_event_generator(datasheet_id: str):
    """Generate progress events for SSE stream"""
    queue = asyncio.Queue()
    progress_queues[datasheet_id] = queue
    
    try:
        while True:
            # Wait for progress updates
            data = await asyncio.wait_for(queue.get(), timeout=300)  # 5 min timeout
            
            if data.get("stage") == "complete" or data.get("error"):
                yield {"event": "complete", "data": data}
                break
            
            yield {"event": "progress", "data": data}
    except asyncio.TimeoutError:
        yield {"event": "timeout", "data": {"message": "Connection timed out"}}
    finally:
        progress_queues.pop(datasheet_id, None)


@app.get("/api/progress/{datasheet_id}")
async def progress_stream(datasheet_id: str):
    """
    SSE endpoint for real-time progress updates (PDF-014)
    
    Clients connect here to receive live progress during PDF processing.
    """
    return EventSourceResponse(progress_event_generator(datasheet_id))


def send_progress(datasheet_id: str, progress_data: dict):
    """Send progress update to connected clients"""
    if datasheet_id in progress_queues:
        try:
            progress_queues[datasheet_id].put_nowait(progress_data)
        except asyncio.QueueFull:
            pass  # Skip if queue is full


# ============ Health & Info Endpoints ============

@app.get("/")
async def root():
    """API root - health check"""
    return {
        "name": "Datasheet Part Selector API",
        "version": "1.0.0",
        "status": "healthy",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


# ============ Error Handlers ============

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc) if app_settings.debug else "An unexpected error occurred"
        }
    )


# ============ Run Server ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=app_settings.api_host,
        port=app_settings.api_port,
        reload=app_settings.debug
    )
