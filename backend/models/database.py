"""
SQLAlchemy Models for Datasheet Part Selector

Implements requirements:
- DB-001: Datasheet-agnostic schema
- DB-002: Raw + normalized data storage
- DB-003: Datasheet versioning
- DB-008: Soft-delete support
- DB-009: Archive instead of delete
- DB-010: Full revision history
"""
from datetime import datetime
from typing import Optional, List
from uuid import uuid4
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float, 
    DateTime, ForeignKey, JSON, LargeBinary, Enum
)
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import enum


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class ProcessingStatus(enum.Enum):
    """Status of datasheet processing"""
    PENDING = "pending"
    UPLOADING = "uploading"
    PARSING = "parsing"
    EXTRACTING = "extracting"
    PROCESSING_LLM = "processing_llm"
    COMPLETE = "complete"
    ERROR = "error"


class Datasheet(Base):
    """
    Represents an uploaded PDF datasheet
    Supports versioning and soft-delete per DB-003, DB-008, DB-009
    """
    __tablename__ = "datasheets"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False)
    manufacturer = Column(String(255), nullable=True)
    part_family = Column(String(255), nullable=True)
    version = Column(Integer, default=1)
    
    # File storage
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=True)
    
    # Processing
    status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    progress_percent = Column(Float, default=0.0)
    progress_message = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Raw extraction data (DB-002)
    raw_extraction = Column(JSON, nullable=True)
    
    # Soft delete / Archive (DB-008, DB-009)
    is_deleted = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    schemas = relationship("PartSchema", back_populates="datasheet", cascade="all, delete-orphan")
    revisions = relationship("DatasheetRevision", back_populates="datasheet", cascade="all, delete-orphan")


class DatasheetRevision(Base):
    """
    Stores revision history for datasheets (DB-010)
    Every edit creates a versioned snapshot
    """
    __tablename__ = "datasheet_revisions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    datasheet_id = Column(String(36), ForeignKey("datasheets.id"), nullable=False)
    version = Column(Integer, nullable=False)
    
    # Snapshot of state at this version
    snapshot_data = Column(JSON, nullable=False)
    change_description = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    datasheet = relationship("Datasheet", back_populates="revisions")


class PartSchema(Base):
    """
    Defines the part number structure for a datasheet
    Supports configurable field definitions (DB-005)
    """
    __tablename__ = "part_schemas"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    datasheet_id = Column(String(36), ForeignKey("datasheets.id"), nullable=False)
    
    # Part number pattern (e.g., "D38999/{series}{class}{shell}{insert}{contact}{polar}")
    part_number_pattern = Column(String(255), nullable=False)
    part_number_prefix = Column(String(50), nullable=True)  # e.g., "D38999/"
    
    # Validation rules as JSON
    validation_rules = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    datasheet = relationship("Datasheet", back_populates="schemas")
    fields = relationship("SpecField", back_populates="schema", cascade="all, delete-orphan")
    variants = relationship("PartVariant", back_populates="schema", cascade="all, delete-orphan")


class SpecField(Base):
    """
    Defines a configurable field within a part number
    Examples: Shell Size, Contact Style, Polarization
    """
    __tablename__ = "spec_fields"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    schema_id = Column(String(36), ForeignKey("part_schemas.id"), nullable=False)
    
    name = Column(String(100), nullable=False)  # Human-readable name
    code = Column(String(50), nullable=False)   # Field identifier in pattern
    description = Column(Text, nullable=True)
    
    # Data type for this field
    data_type = Column(String(50), default="string")  # string, enum, number
    
    # Allowed values as JSON array
    # Each item: {"code": "W", "name": "Olive Drab Cadmium", "description": "..."}
    allowed_values = Column(JSON, nullable=True)
    
    # Position in part number (left to right)
    position = Column(Integer, nullable=False)
    
    # Is this field required?
    is_required = Column(Boolean, default=True)
    
    # Compatibility constraints (references other fields)
    constraints = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    schema = relationship("PartSchema", back_populates="fields")


class PartVariant(Base):
    """
    A specific valid part number configuration
    Generated from field combinations (DB-006)
    """
    __tablename__ = "part_variants"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    schema_id = Column(String(36), ForeignKey("part_schemas.id"), nullable=False)
    
    # The complete part number
    full_part_number = Column(String(100), nullable=False, index=True)
    
    # Field values as JSON: {"shell": "B", "contact": "S", ...}
    field_values = Column(JSON, nullable=False)
    
    # Derived specifications
    specifications = Column(JSON, nullable=True)  # temp range, pin count, etc.
    
    # Is this a valid/active variant?
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    schema = relationship("PartSchema", back_populates="variants")
    distributor_listings = relationship("DistributorListing", back_populates="variant", cascade="all, delete-orphan")


class DistributorListing(Base):
    """
    Stock/pricing information from distributors
    Placeholder for future DigiKey/Mouser integration
    """
    __tablename__ = "distributor_listings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    part_variant_id = Column(String(36), ForeignKey("part_variants.id"), nullable=False)
    
    distributor = Column(String(50), nullable=False)  # "digikey", "mouser"
    distributor_pn = Column(String(100), nullable=True)
    
    # Availability
    stock_qty = Column(Integer, nullable=True)
    lead_time_days = Column(Integer, nullable=True)
    
    # Pricing tiers as JSON: [{"qty": 1, "price": 45.00}, {"qty": 10, "price": 42.00}]
    pricing = Column(JSON, nullable=True)
    
    # Direct link to product page
    product_url = Column(String(512), nullable=True)
    datasheet_url = Column(String(512), nullable=True)
    
    # Cache management
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    variant = relationship("PartVariant", back_populates="distributor_listings")


# Database engine and session factory
async_engine = None
async_session_factory = None


async def init_db(database_url: str):
    """Initialize the async database engine"""
    global async_engine, async_session_factory
    
    async_engine = create_async_engine(database_url, echo=True)
    async_session_factory = async_sessionmaker(
        async_engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    # Create all tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Get an async database session"""
    async with async_session_factory() as session:
        yield session
