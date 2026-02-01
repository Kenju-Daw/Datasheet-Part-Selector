"""
Pydantic Schemas for API Request/Response validation
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ProcessingStatusEnum(str, Enum):
    """Processing status enumeration"""
    PENDING = "pending"
    UPLOADING = "uploading"
    PARSING = "parsing"
    EXTRACTING = "extracting"
    PROCESSING_LLM = "processing_llm"
    COMPLETE = "complete"
    ERROR = "error"


# ============ Progress Tracking (PDF-012 to PDF-015) ============

class ProgressStage(str, Enum):
    """Stages for detailed progress tracking"""
    UPLOAD = "upload"
    DOCLING_INIT = "docling_init"
    DOCLING_PAGES = "docling_pages"
    DOCLING_TABLES = "docling_tables"
    LLM_ANALYZE = "llm_analyze"
    LLM_EXTRACT = "llm_extract"
    LLM_SCHEMA = "llm_schema"
    SAVING = "saving"
    COMPLETE = "complete"


class ProgressUpdate(BaseModel):
    """Real-time progress update for SSE/WebSocket (PDF-012, PDF-014)"""
    datasheet_id: str
    stage: ProgressStage
    percent: float = Field(ge=0, le=100)
    message: str
    
    # Detailed info (PDF-012)
    pages_processed: Optional[int] = None
    pages_total: Optional[int] = None
    tables_found: Optional[int] = None
    
    # Time estimation (PDF-015)
    estimated_seconds_remaining: Optional[int] = None
    
    # Error info
    error: Optional[str] = None


# ============ Datasheet Schemas ============

class DatasheetBase(BaseModel):
    """Base datasheet fields"""
    name: str
    manufacturer: Optional[str] = None
    part_family: Optional[str] = None


class DatasheetCreate(DatasheetBase):
    """Schema for creating a datasheet (upload)"""
    pass


class DatasheetResponse(DatasheetBase):
    """Schema for datasheet API response"""
    id: str
    version: int
    filename: str
    file_size: Optional[int]
    status: ProcessingStatusEnum
    progress_percent: float
    progress_message: Optional[str]
    error_message: Optional[str]
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DatasheetListResponse(BaseModel):
    """Paginated list of datasheets"""
    items: List[DatasheetResponse]
    total: int
    page: int
    page_size: int


# ============ Part Schema Schemas ============

class AllowedValue(BaseModel):
    """An allowed value for a spec field"""
    code: str
    name: str
    description: Optional[str] = None


class SpecFieldResponse(BaseModel):
    """Spec field for API response"""
    id: str
    name: str
    code: str
    description: Optional[str]
    data_type: str
    allowed_values: Optional[List[AllowedValue]]
    position: int
    is_required: bool
    constraints: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


class PartSchemaResponse(BaseModel):
    """Part schema for API response"""
    id: str
    datasheet_id: str
    part_number_pattern: str
    part_number_prefix: Optional[str]
    fields: List[SpecFieldResponse]
    
    class Config:
        from_attributes = True


# ============ Part Configuration Schemas ============

class PartConfigureRequest(BaseModel):
    """Request to configure/generate a part number"""
    schema_id: str
    field_values: Dict[str, str]  # {"shell": "B", "contact": "S", ...}


class PartConfigureResponse(BaseModel):
    """Response with generated part number"""
    full_part_number: str
    field_values: Dict[str, str]
    is_valid: bool
    validation_errors: List[str] = []
    specifications: Optional[Dict[str, Any]] = None


class PartDecodeRequest(BaseModel):
    """Request to decode an existing part number"""
    part_number: str


class PartDecodeResponse(BaseModel):
    """Response with decoded part number fields"""
    part_number: str
    field_values: Dict[str, str]
    field_names: Dict[str, str]  # {"B": "Shell Size 11 (0.688\")"}
    is_valid: bool


# ============ Search Schemas ============

class PartSearchRequest(BaseModel):
    """Part search request"""
    query: Optional[str] = None
    filters: Optional[Dict[str, List[str]]] = None  # {"shell": ["A", "B"], ...}
    page: int = 1
    page_size: int = 20


class PartVariantResponse(BaseModel):
    """Part variant for API response"""
    id: str
    full_part_number: str
    field_values: Dict[str, Any]
    specifications: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


class PartSearchResponse(BaseModel):
    """Paginated part search results"""
    items: List[PartVariantResponse]
    total: int
    page: int
    page_size: int


# ============ Archive Schemas (DB-009, DB-011) ============

class ArchiveActionRequest(BaseModel):
    """Request to archive/restore a datasheet"""
    action: str = Field(..., pattern="^(archive|restore|delete)$")


class ArchiveResponse(BaseModel):
    """Archive action response"""
    id: str
    action: str
    success: bool
    message: str
    success: bool
    message: str


# ============ Chat Schemas (GPS-001) ============

class ChatMessageRole(str, Enum):
    """Role of the message sender"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessageCreate(BaseModel):
    """Schema for creating a chat message"""
    role: ChatMessageRole
    content: str
    meta_data: Optional[Dict[str, Any]] = None


class ChatMessageResponse(ChatMessageCreate):
    """Schema for chat message response"""
    id: str
    session_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatSessionCreate(BaseModel):
    """Schema for creating a chat session"""
    title: Optional[str] = "New Chat"


class ChatSessionResponse(BaseModel):
    """Schema for chat session response"""
    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    messages: List[ChatMessageResponse] = []
    
    class Config:
        from_attributes = True
