"""
PDF Parser Service - Docling integration for datasheet extraction

Implements requirements:
- PDF-002: Docling for PDF parsing
- PDF-003: Table extraction
- PDF-004: Multi-page handling
- PDF-012: Detailed progress bar during Docling parsing
- PDF-014: Real-time progress updates
- PDF-015: Estimated remaining time
"""
import asyncio
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, Any
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from config import get_settings
from models.schemas import ProgressStage

# Setup logger
logger = logging.getLogger(__name__)

settings = get_settings()


class ProgressCallback:
    """
    Manages progress updates for PDF processing (PDF-012, PDF-014, PDF-015)
    
    Sends real-time updates to the SSE endpoint and database.
    """
    
    def __init__(self, datasheet_id: str, total_pages: int = 0):
        self.datasheet_id = datasheet_id
        self.total_pages = total_pages
        self.pages_processed = 0
        self.tables_found = 0
        self.start_time = time.time()
        self.stage = ProgressStage.DOCLING_INIT
        
    def update(
        self, 
        stage: ProgressStage,
        percent: float,
        message: str,
        pages_processed: Optional[int] = None,
        tables_found: Optional[int] = None
    ) -> dict:
        """Create a progress update dict"""
        self.stage = stage
        
        if pages_processed is not None:
            self.pages_processed = pages_processed
        if tables_found is not None:
            self.tables_found = tables_found
        
        # Estimate remaining time (PDF-015)
        elapsed = time.time() - self.start_time
        estimated_remaining = None
        
        if percent > 0 and percent < 100:
            total_estimated = elapsed / (percent / 100)
            estimated_remaining = int(total_estimated - elapsed)
        
        return {
            "datasheet_id": self.datasheet_id,
            "stage": stage.value,
            "percent": round(percent, 1),
            "message": message,
            "pages_processed": self.pages_processed,
            "pages_total": self.total_pages,
            "tables_found": self.tables_found,
            "estimated_seconds_remaining": estimated_remaining
        }


async def process_datasheet_pdf(datasheet_id: str, file_path: str):
    """
    Main PDF processing pipeline
    
    This runs in the background after upload.
    Sends progress updates via the main app's send_progress function.
    """
    from main import send_progress
    
    # Create a new database session for this background task
    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    progress = ProgressCallback(datasheet_id)
    
    try:
        async with async_session() as session:
            from models import Datasheet, PartSchema, SpecField, ProcessingStatus
            
            # Get datasheet record
            result = await session.execute(
                select(Datasheet).where(Datasheet.id == datasheet_id)
            )
            datasheet = result.scalar_one()
            
            # ============ Stage 1: Initialize Docling (5%) ============
            datasheet.status = ProcessingStatus.PARSING
            datasheet.progress_percent = 5.0
            datasheet.progress_message = "Initializing PDF parser..."
            await session.commit()
            
            send_progress(datasheet_id, progress.update(
                ProgressStage.DOCLING_INIT, 5.0, "Initializing Docling PDF parser..."
            ))
            
            # Import Docling (this can take a moment on first run)
            try:
                from docling.document_converter import DocumentConverter
                print(f"[{datasheet_id[:8]}] ✓ Docling import successful")
                logger.info("Docling import successful")
            except ImportError as e:
                print(f"[{datasheet_id[:8]}] ✗ Docling import failed: {e}")
                logger.error(f"Docling import failed: {e}")
                raise RuntimeError(f"Docling not installed correctly: {e}")
            
            # ============ Stage 2: Parse PDF Pages (5-40%) ============
            send_progress(datasheet_id, progress.update(
                ProgressStage.DOCLING_PAGES, 10.0, "Loading PDF document..."
            ))
            
            # Use default Docling converter - it handles most PDFs well
            print(f"[{datasheet_id[:8]}] Creating DocumentConverter...")
            logger.info("Creating DocumentConverter with defaults")
            converter = DocumentConverter()
            
            # Convert PDF
            datasheet.progress_percent = 15.0
            datasheet.progress_message = "Parsing PDF structure (this may take 5-15 min for large PDFs)..."
            await session.commit()
            
            send_progress(datasheet_id, progress.update(
                ProgressStage.DOCLING_PAGES, 15.0, "Parsing PDF structure (this may take 5-15 min)..."
            ))
            
            # Run conversion in a thread to not block async event loop
            print(f"[{datasheet_id[:8]}] Starting PDF conversion (this takes several minutes)...")
            import asyncio
            result_doc = await asyncio.to_thread(converter.convert, file_path)
            doc = result_doc.document
            print(f"[{datasheet_id[:8]}] ✓ PDF conversion complete!")
            
            # Get page count
            page_count = len(doc.pages) if hasattr(doc, 'pages') else 0
            progress.total_pages = page_count
            
            send_progress(datasheet_id, progress.update(
                ProgressStage.DOCLING_PAGES, 30.0, 
                f"Parsed {page_count} pages",
                pages_processed=page_count
            ))
            
            # ============ Stage 3: Extract Tables (40-60%) ============
            datasheet.status = ProcessingStatus.EXTRACTING
            datasheet.progress_percent = 40.0
            datasheet.progress_message = "Extracting tables..."
            await session.commit()
            
            send_progress(datasheet_id, progress.update(
                ProgressStage.DOCLING_TABLES, 40.0, "Extracting tables from document..."
            ))
            
            # Extract tables - convert iterator to list first
            tables = []
            table_list = list(doc.tables) if hasattr(doc, 'tables') else []
            table_count = len(table_list)
            
            for i, table in enumerate(table_list):
                try:
                    # Export table data safely
                    table_data = {}
                    if hasattr(table, 'export_to_dataframe'):
                        df = table.export_to_dataframe()
                        table_data = df.to_dict()
                    
                    tables.append({
                        "index": i,
                        "data": table_data
                    })
                except Exception as table_err:
                    logger.warning(f"Failed to export table {i}: {table_err}")
                    tables.append({"index": i, "data": {}, "error": str(table_err)})
                
                percent = 40 + (20 * (i + 1) / max(table_count, 1))
                send_progress(datasheet_id, progress.update(
                    ProgressStage.DOCLING_TABLES, percent,
                    f"Extracted table {i + 1} of {table_count}",
                    tables_found=i + 1
                ))
            
            # Store raw extraction
            raw_extraction = {
                "page_count": page_count,
                "table_count": len(tables),
                "tables": tables,
                "text": doc.export_to_markdown() if hasattr(doc, 'export_to_markdown') else "",
                "metadata": {
                    "processed_at": datetime.utcnow().isoformat(),
                    "docling_version": "2.0"
                }
            }
            
            datasheet.raw_extraction = raw_extraction
            datasheet.progress_percent = 60.0
            datasheet.progress_message = f"Extracted {len(tables)} tables"
            await session.commit()
            
            send_progress(datasheet_id, progress.update(
                ProgressStage.DOCLING_TABLES, 60.0,
                f"Extracted {len(tables)} tables from {page_count} pages",
                tables_found=len(tables)
            ))
            
            # ============ Stage 4: LLM Processing (60-90%) ============
            datasheet.status = ProcessingStatus.PROCESSING_LLM
            datasheet.progress_percent = 65.0
            datasheet.progress_message = "Analyzing with LLM..."
            await session.commit()
            
            send_progress(datasheet_id, progress.update(
                ProgressStage.LLM_ANALYZE, 65.0, "Starting LLM analysis..."
            ))
            
            # Process with LLM
            from services.llm_processor import process_extraction_with_llm
            
            schema_data = await process_extraction_with_llm(
                datasheet_id,
                raw_extraction,
                progress_callback=lambda stage, pct, msg: send_progress(
                    datasheet_id, progress.update(stage, pct, msg)
                )
            )
            
            # ============ Stage 5: Save Schema (90-100%) ============
            send_progress(datasheet_id, progress.update(
                ProgressStage.SAVING, 90.0, "Saving extracted schema..."
            ))
            
            if schema_data:
                # Create PartSchema
                part_schema = PartSchema(
                    datasheet_id=datasheet_id,
                    part_number_pattern=schema_data.get("pattern", ""),
                    part_number_prefix=schema_data.get("prefix", ""),
                    validation_rules=schema_data.get("validation_rules")
                )
                session.add(part_schema)
                await session.flush()
                
                # Create SpecFields
                for i, field_data in enumerate(schema_data.get("fields", [])):
                    field = SpecField(
                        schema_id=part_schema.id,
                        name=field_data.get("name", f"Field {i}"),
                        code=field_data.get("code", f"f{i}"),
                        description=field_data.get("description"),
                        data_type=field_data.get("type", "string"),
                        allowed_values=field_data.get("values"),
                        position=i,
                        is_required=field_data.get("required", True),
                        constraints=field_data.get("constraints")
                    )
                    session.add(field)
            
            # Mark complete
            datasheet.status = ProcessingStatus.COMPLETE
            datasheet.progress_percent = 100.0
            datasheet.progress_message = "Processing complete"
            await session.commit()
            
            send_progress(datasheet_id, progress.update(
                ProgressStage.COMPLETE, 100.0, "Processing complete!"
            ))
            
    except Exception as e:
        # Handle errors with detailed logging
        logger.error(f"PDF processing failed for {datasheet_id}: {str(e)}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        
        async with async_session() as session:
            from models import Datasheet, ProcessingStatus
            
            result = await session.execute(
                select(Datasheet).where(Datasheet.id == datasheet_id)
            )
            datasheet = result.scalar_one_or_none()
            
            if datasheet:
                datasheet.status = ProcessingStatus.ERROR
                datasheet.error_message = str(e)
                datasheet.progress_message = "Processing failed"
                await session.commit()
                logger.info(f"Updated datasheet {datasheet_id} status to ERROR")
        
        send_progress(datasheet_id, {
            "datasheet_id": datasheet_id,
            "stage": "error",
            "percent": progress.stage.value if hasattr(progress, 'stage') else 0,
            "message": f"Error: {str(e)}",
            "error": str(e)
        })
        
        raise
    
    finally:
        await engine.dispose()
        logger.info(f"Disposed database engine for {datasheet_id}")
