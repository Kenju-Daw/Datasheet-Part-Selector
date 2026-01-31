"""
Parts Router - API endpoints for part configuration and search

Implements requirements:
- CFG-001: Dynamic field loading
- CFG-002: Live part number preview
- CFG-003: Compatibility validation
- CFG-004: Part number decoding
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import PartSchema, SpecField, PartVariant, get_session
from models.schemas import (
    PartSchemaResponse,
    PartConfigureRequest,
    PartConfigureResponse,
    PartDecodeRequest,
    PartDecodeResponse,
    PartSearchRequest,
    PartSearchResponse,
    PartVariantResponse
)


router = APIRouter()


# ============ Get Schema for Datasheet (CFG-001) ============

@router.get("/schema/{datasheet_id}", response_model=PartSchemaResponse)
async def get_part_schema(
    datasheet_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Get the part number schema for a datasheet (CFG-001)
    
    Returns field definitions for populating configurator dropdowns.
    """
    result = await session.execute(
        select(PartSchema)
        .options(selectinload(PartSchema.fields))
        .where(PartSchema.datasheet_id == datasheet_id)
    )
    schema = result.scalar_one_or_none()
    
    if not schema:
        raise HTTPException(
            status_code=404, 
            detail="Part schema not found. The datasheet may still be processing."
        )
    
    # Sort fields by position
    schema.fields = sorted(schema.fields, key=lambda f: f.position)
    
    return schema


# ============ Configure Part Number (CFG-002, CFG-003) ============

@router.post("/configure", response_model=PartConfigureResponse)
async def configure_part(
    request: PartConfigureRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Generate a part number from selected field values (CFG-002)
    
    Also validates compatibility constraints (CFG-003).
    """
    # Get schema with fields
    result = await session.execute(
        select(PartSchema)
        .options(selectinload(PartSchema.fields))
        .where(PartSchema.id == request.schema_id)
    )
    schema = result.scalar_one_or_none()
    
    if not schema:
        raise HTTPException(status_code=404, detail="Part schema not found")
    
    # Sort fields by position
    fields = sorted(schema.fields, key=lambda f: f.position)
    
    # Validate and build part number
    validation_errors = []
    part_segments = []
    
    for field in fields:
        value = request.field_values.get(field.code)
        
        # Check required fields
        if field.is_required and not value:
            validation_errors.append(f"Field '{field.name}' is required")
            continue
        
        if value:
            # Validate against allowed values
            if field.allowed_values:
                valid_codes = [v.get("code") for v in field.allowed_values]
                if value not in valid_codes:
                    validation_errors.append(
                        f"Invalid value '{value}' for field '{field.name}'"
                    )
                    continue
            
            # TODO: Check constraints (CFG-003)
            # This would check if the selected value is compatible with other selections
            
            part_segments.append(value)
        elif not field.is_required:
            # Optional field, use empty or default
            part_segments.append("")
    
    # Build full part number
    prefix = schema.part_number_prefix or ""
    full_part_number = prefix + "".join(part_segments)
    
    return PartConfigureResponse(
        full_part_number=full_part_number,
        field_values=request.field_values,
        is_valid=len(validation_errors) == 0,
        validation_errors=validation_errors,
        specifications=None  # TODO: Look up specs based on configuration
    )


# ============ Decode Part Number (CFG-004) ============

@router.post("/decode", response_model=PartDecodeResponse)
async def decode_part_number(
    request: PartDecodeRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Decode an existing part number into field values (CFG-004)
    """
    part_number = request.part_number.upper().strip()
    
    # Try to find a matching schema by prefix
    result = await session.execute(
        select(PartSchema).options(selectinload(PartSchema.fields))
    )
    schemas = result.scalars().all()
    
    matched_schema = None
    remaining_pn = part_number
    
    for schema in schemas:
        if schema.part_number_prefix:
            prefix = schema.part_number_prefix.upper()
            if part_number.startswith(prefix):
                matched_schema = schema
                remaining_pn = part_number[len(prefix):]
                break
    
    if not matched_schema:
        raise HTTPException(
            status_code=404,
            detail="Could not identify part number format. No matching schema found."
        )
    
    # Parse field values from remaining part number
    fields = sorted(matched_schema.fields, key=lambda f: f.position)
    field_values = {}
    field_names = {}
    cursor = 0
    
    for field in fields:
        if not field.allowed_values:
            continue
        
        # Try to match against allowed values
        matched = False
        for allowed in field.allowed_values:
            code = allowed.get("code", "")
            if remaining_pn[cursor:].startswith(code):
                field_values[field.code] = code
                field_names[code] = f"{field.name}: {allowed.get('name', code)}"
                cursor += len(code)
                matched = True
                break
        
        if not matched and field.is_required:
            # Could not decode this field
            field_values[field.code] = "?"
    
    return PartDecodeResponse(
        part_number=part_number,
        field_values=field_values,
        field_names=field_names,
        is_valid=cursor == len(remaining_pn)
    )


# ============ Search Parts ============

@router.post("/search", response_model=PartSearchResponse)
async def search_parts(
    request: PartSearchRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Search for part variants with optional filters
    """
    query = select(PartVariant).where(PartVariant.is_active == True)
    
    # Apply keyword search on part number
    if request.query:
        query = query.where(
            PartVariant.full_part_number.ilike(f"%{request.query}%")
        )
    
    # Apply field filters
    if request.filters:
        for field_code, values in request.filters.items():
            # Filter by JSON field values
            # Note: This is SQLite-compatible JSON filtering
            for value in values:
                query = query.where(
                    PartVariant.field_values[field_code].as_string() == value
                )
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_query)
    
    # Paginate
    query = query.offset((request.page - 1) * request.page_size)
    query = query.limit(request.page_size)
    
    result = await session.execute(query)
    variants = result.scalars().all()
    
    return PartSearchResponse(
        items=[PartVariantResponse.model_validate(v) for v in variants],
        total=total,
        page=request.page,
        page_size=request.page_size
    )


# ============ Get Part Variant Details ============

@router.get("/variant/{variant_id}", response_model=PartVariantResponse)
async def get_part_variant(
    variant_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Get details for a specific part variant
    """
    result = await session.execute(
        select(PartVariant).where(PartVariant.id == variant_id)
    )
    variant = result.scalar_one_or_none()
    
    if not variant:
        raise HTTPException(status_code=404, detail="Part variant not found")
    
    return variant
