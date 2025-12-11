"""Refresh API endpoints for re-indexing Notion data."""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
import structlog

from app.services.notion_service import NotionService
from app.services.indexing_service import IndexingService
from app.api.auth import verify_api_key

router = APIRouter()
logger = structlog.get_logger(__name__)


class RefreshRequest(BaseModel):
    """Request model for refresh endpoint."""
    page_ids: Optional[list[str]] = Field(None,
                                          description="Specific page IDs to refresh. If not provided, refreshes all.")
    force: bool = Field(False,
                       description="Force refresh even if content hasn't changed")


class RefreshResponse(BaseModel):
    """Response model for refresh endpoint."""
    status: str
    message: str
    task_id: Optional[str] = None
    started_at: datetime


class RefreshStatusResponse(BaseModel):
    """Response model for refresh status endpoint."""
    task_id: str
    status: str  # pending, running, completed, failed
    progress: Dict[str, Any]
    started_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


# In-memory task tracking (should be replaced with Redis or database in production)
refresh_tasks = {}


async def refresh_notion_data(task_id: str, page_ids: Optional[list[str]] = None, force: bool = False):
    """Background task to refresh Notion data."""
    try:
        logger.info("Starting refresh task", task_id=task_id, page_ids=page_ids)
        refresh_tasks[task_id]["status"] = "running"
        refresh_tasks[task_id]["progress"]["current_step"] = "Connecting to Notion"

        # Initialize services
        notion_service = NotionService()
        indexing_service = IndexingService()

        # Fetch Notion data
        refresh_tasks[task_id]["progress"]["current_step"] = "Fetching Notion pages"
        pages = await notion_service.fetch_pages(page_ids)
        refresh_tasks[task_id]["progress"]["total_pages"] = len(pages)

        # Process each page
        for i, page in enumerate(pages):
            refresh_tasks[task_id]["progress"]["current_page"] = i + 1
            refresh_tasks[task_id]["progress"]["current_step"] = f"Processing page {i+1}/{len(pages)}"

            # Extract text from page
            text_chunks = await notion_service.extract_text(page)

            # Index the chunks
            await indexing_service.index_chunks(text_chunks, page["id"])

        # Mark as completed
        refresh_tasks[task_id]["status"] = "completed"
        refresh_tasks[task_id]["completed_at"] = datetime.utcnow()
        refresh_tasks[task_id]["progress"]["current_step"] = "Completed"

        logger.info("Refresh task completed", task_id=task_id, pages_processed=len(pages))

    except Exception as e:
        logger.error("Refresh task failed", task_id=task_id, error=str(e))
        refresh_tasks[task_id]["status"] = "failed"
        refresh_tasks[task_id]["error"] = str(e)
        refresh_tasks[task_id]["completed_at"] = datetime.utcnow()


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_index(
    request: Request,
    background_tasks: BackgroundTasks,
    refresh_request: RefreshRequest = RefreshRequest(),
    api_key: str = Depends(verify_api_key)
) -> RefreshResponse:
    """
    Refresh the Notion data index.

    This endpoint triggers a background task to:
    1. Fetch latest data from Notion
    2. Process and chunk the text
    3. Generate embeddings
    4. Update the vector database

    The refresh happens asynchronously and you can check the status
    using the /refresh/status/{task_id} endpoint.
    """
    try:
        # Generate task ID
        task_id = f"refresh_{datetime.utcnow().timestamp()}"

        # Initialize task tracking
        refresh_tasks[task_id] = {
            "task_id": task_id,
            "status": "pending",
            "progress": {
                "current_step": "Initializing",
                "total_pages": 0,
                "current_page": 0
            },
            "started_at": datetime.utcnow(),
            "completed_at": None,
            "error": None
        }

        # Start background task
        background_tasks.add_task(
            refresh_notion_data,
            task_id,
            refresh_request.page_ids,
            refresh_request.force
        )

        logger.info("Refresh task created", task_id=task_id)

        return RefreshResponse(
            status="accepted",
            message="Refresh task has been queued",
            task_id=task_id,
            started_at=datetime.utcnow()
        )

    except Exception as e:
        logger.error("Failed to start refresh task", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start refresh task: {str(e)}"
        )


@router.get("/refresh/status/{task_id}", response_model=RefreshStatusResponse)
async def get_refresh_status(
    task_id: str,
    api_key: str = Depends(verify_api_key)
) -> RefreshStatusResponse:
    """
    Get the status of a refresh task.

    Returns the current status and progress of the refresh operation.
    """
    if task_id not in refresh_tasks:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )

    task = refresh_tasks[task_id]
    return RefreshStatusResponse(**task)


@router.post("/refresh/cancel/{task_id}")
async def cancel_refresh(
    task_id: str,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, str]:
    """
    Cancel a running refresh task.

    Note: This is a placeholder. Actual cancellation requires
    more sophisticated task management.
    """
    if task_id not in refresh_tasks:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )

    if refresh_tasks[task_id]["status"] != "running":
        raise HTTPException(
            status_code=400,
            detail=f"Task {task_id} is not running"
        )

    # In a real implementation, we would signal the task to stop
    refresh_tasks[task_id]["status"] = "cancelled"
    refresh_tasks[task_id]["completed_at"] = datetime.utcnow()

    return {"message": f"Task {task_id} has been cancelled"}


@router.get("/refresh/history")
async def get_refresh_history(
    limit: int = 10,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Get refresh task history.

    Returns a list of recent refresh tasks and their status.
    """
    # Sort tasks by started_at descending
    sorted_tasks = sorted(
        refresh_tasks.values(),
        key=lambda x: x["started_at"],
        reverse=True
    )[:limit]

    return {
        "tasks": sorted_tasks,
        "total": len(refresh_tasks)
    }