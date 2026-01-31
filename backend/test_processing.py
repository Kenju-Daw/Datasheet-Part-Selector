"""
Test script for PDF processing pipeline

Run this script to test the complete processing flow with detailed logs.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Initialize logging FIRST
import logging_config

from config import get_settings
from models import init_db

logger = logging_config.get_logger(__name__)


async def test_pdf_processing():
    """Test the PDF processing pipeline"""
    settings = get_settings()
    
    logger.info("=" * 60)
    logger.info("STARTING PDF PROCESSING TEST")
    logger.info("=" * 60)
    
    # Initialize database
    logger.info("Initializing database...")
    await init_db(settings.database_url)
    logger.info("Database initialized")
    
    # Find a test PDF
    datasheets_dir = settings.datasheets_dir
    pdf_files = list(datasheets_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.error(f"No PDF files found in {datasheets_dir}")
        print(f"❌ No PDF files found in {datasheets_dir}")
        return
    
    test_pdf = pdf_files[0]
    logger.info(f"Testing with PDF: {test_pdf.name}")
    print(f"📄 Testing with: {test_pdf.name}")
    
    # Import after init to avoid circular imports
    from services.pdf_parser import process_datasheet_pdf
    
    # Get the datasheet ID from the filename (UUID prefix)
    datasheet_id = test_pdf.name.split("_")[0]
    logger.info(f"Datasheet ID: {datasheet_id}")
    
    try:
        print("🔄 Starting processing...")
        await process_datasheet_pdf(datasheet_id, str(test_pdf))
        print("✅ Processing completed successfully!")
        logger.info("Processing completed successfully")
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        logger.exception("Processing failed")
        
    logger.info("=" * 60)
    logger.info("TEST COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    print("🧪 Running PDF Processing Test")
    print("-" * 40)
    asyncio.run(test_pdf_processing())
