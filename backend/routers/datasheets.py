"""
Datasheet Router - API endpoints for PDF upload and management

Implements requirements:
- PDF-001: PDF datasheet uploads
- PDF-008: Original PDF storage
- PDF-009: Processing status with progress
- PDF-011: Re-processing support
- DB-009: Archive instead of delete
- DB-011: Archive view
"""
import os
import shutil
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, BackgroundTasks
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Datasheet, DatasheetRevision, PartSchema, ProcessingStatus, get_session
from models.schemas import (
    DatasheetResponse, 
    DatasheetListResponse,
    ArchiveActionRequest,
    ArchiveResponse,
    ProgressUpdate,
    ProgressStage
)
from config import get_settings
from services.pdf_parser import process_datasheet_pdf


router = APIRouter()
settings = get_settings()


# ============ Upload Endpoint (PDF-001, PDF-008) ============

@router.post("/upload", response_model=DatasheetResponse)
async def upload_datasheet(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    name: str = Form(None),
    manufacturer: str = Form(None),
    part_family: str = Form(None),
    session: AsyncSession = Depends(get_session)
):
    """
    Upload a PDF datasheet for processing
    
    The file is saved and processing starts in the background.
    Connect to /api/progress/{datasheet_id} via SSE for real-time updates.
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    # Check file size (50MB limit per PDF-001)
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")
    
    # Generate unique ID and filename
    datasheet_id = str(uuid4())
    safe_filename = f"{datasheet_id}_{file.filename}"
    file_path = settings.datasheets_dir / safe_filename
    
    # Save file (PDF-008)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create database record
    datasheet = Datasheet(
        id=datasheet_id,
        name=name or file.filename.replace('.pdf', ''),
        manufacturer=manufacturer,
        part_family=part_family,
        filename=file.filename,
        file_path=str(file_path),
        file_size=file_size,
        status=ProcessingStatus.PENDING,
        progress_percent=0.0,
        progress_message="Queued for processing"
    )
    
    session.add(datasheet)
    await session.commit()
    await session.refresh(datasheet)
    
    # Start background processing
    background_tasks.add_task(process_datasheet_pdf, datasheet_id, str(file_path))
    
    return datasheet


# ============ List Datasheets ============

@router.get("/", response_model=DatasheetListResponse)
async def list_datasheets(
    page: int = 1,
    page_size: int = 20,
    include_archived: bool = False,
    session: AsyncSession = Depends(get_session)
):
    """
    List all uploaded datasheets with pagination
    """
    # Build query
    query = select(Datasheet).where(Datasheet.is_deleted == False)
    
    if not include_archived:
        query = query.where(Datasheet.is_archived == False)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_query)
    
    # Get paginated results
    query = query.order_by(Datasheet.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await session.execute(query)
    datasheets = result.scalars().all()
    
    return DatasheetListResponse(
        items=[DatasheetResponse.model_validate(d) for d in datasheets],
        total=total,
        page=page,
        page_size=page_size
    )


# ============ Get Single Datasheet ============

@router.get("/{datasheet_id}", response_model=DatasheetResponse)
async def get_datasheet(
    datasheet_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Get a specific datasheet by ID
    """
    result = await session.execute(
        select(Datasheet).where(Datasheet.id == datasheet_id)
    )
    datasheet = result.scalar_one_or_none()
    
    if not datasheet:
        raise HTTPException(status_code=404, detail="Datasheet not found")
    
    return datasheet


# ============ Re-process Datasheet (PDF-011) ============

@router.post("/{datasheet_id}/reprocess", response_model=DatasheetResponse)
async def reprocess_datasheet(
    datasheet_id: str,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session)
):
    """
    Trigger re-processing of an existing datasheet (PDF-011)
    """
    result = await session.execute(
        select(Datasheet).where(Datasheet.id == datasheet_id)
    )
    datasheet = result.scalar_one_or_none()
    
    if not datasheet:
        raise HTTPException(status_code=404, detail="Datasheet not found")
    
    # Create revision snapshot before re-processing (DB-010)
    revision = DatasheetRevision(
        datasheet_id=datasheet_id,
        version=datasheet.version,
        snapshot_data={
            "raw_extraction": datasheet.raw_extraction,
            "status": datasheet.status.value,
        },
        change_description="Snapshot before re-processing"
    )
    session.add(revision)
    
    # Reset status
    datasheet.status = ProcessingStatus.PENDING
    datasheet.progress_percent = 0.0
    datasheet.progress_message = "Queued for re-processing"
    datasheet.error_message = None
    datasheet.version += 1
    
    await session.commit()
    await session.refresh(datasheet)
    
    # Start background processing
    background_tasks.add_task(process_datasheet_pdf, datasheet_id, datasheet.file_path)
    
    return datasheet


# ============ Archive Actions (DB-009, DB-011) ============

@router.post("/{datasheet_id}/archive", response_model=ArchiveResponse)
async def archive_action(
    datasheet_id: str,
    request: ArchiveActionRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Archive, restore, or delete a datasheet (DB-009)
    
    - archive: Move to archive (hidden from main list)
    - restore: Restore from archive
    - delete: Soft-delete (never permanently deleted)
    """
    result = await session.execute(
        select(Datasheet).where(Datasheet.id == datasheet_id)
    )
    datasheet = result.scalar_one_or_none()
    
    if not datasheet:
        raise HTTPException(status_code=404, detail="Datasheet not found")
    
    action = request.action
    
    if action == "archive":
        datasheet.is_archived = True
        message = "Datasheet archived successfully"
    elif action == "restore":
        datasheet.is_archived = False
        datasheet.is_deleted = False
        datasheet.deleted_at = None
        message = "Datasheet restored successfully"
    elif action == "delete":
        datasheet.is_deleted = True
        datasheet.deleted_at = datetime.utcnow()
        message = "Datasheet deleted (can be restored from archive)"
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    await session.commit()
    
    return ArchiveResponse(
        id=datasheet_id,
        action=action,
        success=True,
        message=message
    )


# ============ Get Archived Datasheets (DB-011) ============

@router.get("/archive/list", response_model=DatasheetListResponse)
async def list_archived(
    page: int = 1,
    page_size: int = 20,
    session: AsyncSession = Depends(get_session)
):
    """
    List archived and soft-deleted datasheets (DB-011)
    """
    query = select(Datasheet).where(
        (Datasheet.is_archived == True) | (Datasheet.is_deleted == True)
    )
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_query)
    
    # Get paginated results
    query = query.order_by(Datasheet.updated_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await session.execute(query)
    datasheets = result.scalars().all()
    
    return DatasheetListResponse(
        items=[DatasheetResponse.model_validate(d) for d in datasheets],
        total=total,
        page=page,
        page_size=page_size
    )


# ============ Download Original PDF ============

@router.get("/{datasheet_id}/download")
async def download_pdf(
    datasheet_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Download the original PDF file
    """
    from fastapi.responses import FileResponse
    
    result = await session.execute(
        select(Datasheet).where(Datasheet.id == datasheet_id)
    )
    datasheet = result.scalar_one_or_none()
    
    if not datasheet:
        raise HTTPException(status_code=404, detail="Datasheet not found")
    
    if not os.path.exists(datasheet.file_path):
        raise HTTPException(status_code=404, detail="PDF file not found on disk")
    
    return FileResponse(
        path=datasheet.file_path,
        filename=datasheet.filename,
        media_type="application/pdf"
    )
