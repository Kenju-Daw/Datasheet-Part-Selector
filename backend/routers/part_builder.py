"""
Part Builder API Router

Provides endpoints for:
- Insert arrangement search by contact requirements (with fallback and multi-connector suggestions)
- Part number generation
- Contact ordering info
- Availability checking
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Optional
from datetime import datetime
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)
import json

from models import Datasheet, PartSchema, SpecField, get_session
from services.knowledge_base import (
    get_insert_arrangements,
    get_connector_types,
    get_shell_finishes,
    get_contact_part_numbers,
    get_contact_sizes
)

router = APIRouter(prefix="/api/parts", tags=["parts"])


# ============ Request/Response Schemas ============

class ContactRequirement(BaseModel):
    """Single contact requirement"""
    size: str  # "22D", "16", "20", etc.
    quantity: int
    contact_type: str = "pin"  # "pin" or "socket"


class InsertSearchRequest(BaseModel):
    """Search for compatible insert arrangements"""
    datasheet_id: str
    requirements: List[ContactRequirement]


class InsertMatch(BaseModel):
    """A matching insert arrangement"""
    shell_size: str
    insert_arrangement: str
    code: str  # e.g., "19-35"
    total_contacts: int
    contact_breakdown: Dict[str, int]  # {"22D": 66, "16": 3}
    service_rating: str
    match_type: str  # "exact", "close", "over", "partial", "suggestion"
    extra_positions: Dict[str, int]  # unused positions
    is_standard: bool  # True = MIL-standard, False = Amphenol-specific
    missing_contacts: Optional[Dict[str, int]] = None  # for partial matches


class MultiConnectorSuggestion(BaseModel):
    """Suggestion for using multiple connectors"""
    connector_1: InsertMatch
    connector_2: InsertMatch
    total_capacity: int
    covers_requirements: bool
    note: str


class InsertSearchResponse(BaseModel):
    """Search results"""
    matches: List[InsertMatch]
    total_requirements: int
    suggestion: Optional[str] = None  # Helpful hint when no exact match
    multi_connector: Optional[MultiConnectorSuggestion] = None  # For high pin counts


class ConnectorType(BaseModel):
    """Connector type option"""
    code: str
    name: str
    description: str
    is_standard: bool


class FinishOption(BaseModel):
    """Shell finish option"""
    code: str
    name: str
    description: str
    rohs_compliant: bool


class PartBuilderData(BaseModel):
    """All data needed for the Part Builder UI"""
    connector_types: List[ConnectorType]
    finishes: List[FinishOption]
    key_positions: List[str]
    contact_sizes: List[Dict]


class ContactOrderInfo(BaseModel):
    """Contact ordering information"""
    size: str
    contact_type: str
    quantity: int
    military_pn: Optional[str]
    commercial_pn: Optional[str]
    seal_plug_pn: Optional[str]


# ============ Data Loaded from Knowledge Base ============
# Single source of truth - prevents drift between Part Builder and Chat Engine

def _get_insert_arrangements():
    """Get insert arrangements from KB, adapting keys for backward compatibility."""
    return [
        {
            "code": ins["code"],
            "shell": ins["shell"],
            "insert": ins["code"].split("-")[1],  # Extract insert from code
            "total": ins["total"],
            "contacts": ins["contacts"],
            "rating": ins["rating"],
            "is_standard": ins["is_mil_standard"]  # Adapt key name
        }
        for ins in get_insert_arrangements()
    ]

def _get_connector_types():
    """Get connector types from KB."""
    return [
        {
            "code": ct["code"],
            "name": ct["name"],
            "desc": ct["description"],
            "standard": ct["is_mil_standard"]
        }
        for ct in get_connector_types()
    ]

def _get_shell_finishes():
    """Get shell finishes from KB."""
    return [
        {
            "code": sf["code"],
            "name": sf["name"],
            "desc": sf["description"],
            "rohs": sf["rohs_compliant"]
        }
        for sf in get_shell_finishes()
    ]

# Lazy-loaded data accessors
INSERT_ARRANGEMENTS = None
CONNECTOR_TYPES = None
SHELL_FINISHES = None
CONTACT_PART_NUMBERS = None

def _ensure_loaded():
    """Ensure data is loaded from KB (lazy initialization)."""
    global INSERT_ARRANGEMENTS, CONNECTOR_TYPES, SHELL_FINISHES, CONTACT_PART_NUMBERS
    if INSERT_ARRANGEMENTS is None:
        INSERT_ARRANGEMENTS = _get_insert_arrangements()
        CONNECTOR_TYPES = _get_connector_types()
        SHELL_FINISHES = _get_shell_finishes()
        CONTACT_PART_NUMBERS = get_contact_part_numbers()

# Maximum single connector capacity (for multi-connector suggestions)
MAX_SINGLE_CONNECTOR = 128


# ============ Helper Functions ============

def calculate_match_score(insert: dict, req_by_size: dict) -> tuple:
    """
    Calculate how well an insert matches requirements.
    Returns (can_fit: bool, extra: dict, missing: dict, score: float)
    """
    extra = {}
    missing = {}
    
    for size, qty_needed in req_by_size.items():
        available = insert["contacts"].get(size, 0)
        if available >= qty_needed:
            extra[size] = available - qty_needed
        else:
            missing[size] = qty_needed - available
    
    can_fit = len(missing) == 0
    
    # Score: lower is better. 0 = exact fit
    # Penalize extra positions and missing positions differently
    extra_penalty = sum(extra.values())
    missing_penalty = sum(missing.values()) * 10  # Missing is worse
    score = extra_penalty + missing_penalty
    
    return can_fit, extra, missing, score


def find_multi_connector_solution(req_by_size: dict, total_required: int):
    """
    Find a combination of two connectors that can cover the requirements.
    """
    best_combo = None
    best_score = float('inf')
    
    # Sort inserts by capacity (largest first for primary)
    sorted_inserts = sorted(INSERT_ARRANGEMENTS, key=lambda x: x["total"], reverse=True)
    
    logger.info(f"DEBUG: Multi-connector search for {total_required} pins. Req: {req_by_size}")
    
    for i, insert1 in enumerate(sorted_inserts):
        remaining = {}
        for size, qty in req_by_size.items():
            avail1 = insert1["contacts"].get(size, 0)
            if avail1 < qty:
                remaining[size] = qty - avail1
        
        if not remaining:
            continue  # Single connector works
        
        # logger.info(f"DEBUG: Trying {insert1['code']} (Has {insert1['contacts']}). Remaining: {remaining}")

        # Find second connector to cover remaining
        for insert2 in sorted_inserts:
            # ALLOW same connector (e.g. 2x 23-55 to get 110 pins)
            # if insert2["code"] == insert1["code"]:
            #     continue
            
            can_cover = True
            for size, qty in remaining.items():
                if insert2["contacts"].get(size, 0) < qty:
                    can_cover = False
                    break
            
            if can_cover:
                total_capacity = insert1["total"] + insert2["total"]
                waste = total_capacity - total_required
                
                # logger.info(f"DEBUG: Found match! {insert1['code']} + {insert2['code']}. Waste: {waste}")

                if waste < best_score:
                    best_score = waste
                    best_combo = (insert1, insert2, remaining)
                    
                    # Optimization: If waste is 0 (perfect fit), stop searching
                    if waste == 0:
                        logger.info(f"DEBUG: Perfect match found: {insert1['code']} + {insert2['code']}")
                        return best_combo
    
    if best_combo:
        logger.info(f"DEBUG: Best match found: {best_combo[0]['code']} + {best_combo[1]['code']}")
    else:
        logger.info("DEBUG: No multi-connector solution found.")
        
    return best_combo


# ============ API Endpoints ============

@router.get("/builder-data/{datasheet_id}")
async def get_part_builder_data(datasheet_id: str) -> PartBuilderData:
    """Get all data needed for the Part Builder UI"""
    _ensure_loaded()
    return PartBuilderData(
        connector_types=[
            ConnectorType(code=c["code"], name=c["name"], description=c["desc"], is_standard=c["standard"])
            for c in CONNECTOR_TYPES
        ],
        finishes=[
            FinishOption(code=f["code"], name=f["name"], description=f["desc"], rohs_compliant=f["rohs"])
            for f in SHELL_FINISHES
        ],
        key_positions=["N", "A", "B", "C", "D", "E"],
        contact_sizes=[
            {"code": "22D", "amps": 5, "awg": "22-26"},
            {"code": "22", "amps": 5, "awg": "22-26"},
            {"code": "20", "amps": 7.5, "awg": "20-24"},
            {"code": "16", "amps": 13, "awg": "16-20"},
            {"code": "12", "amps": 23, "awg": "12-16"},
            {"code": "10", "amps": 33, "awg": "10-14"},
            {"code": "8", "amps": 46, "awg": "8-12"},
        ]
    )


@router.post("/search-inserts")
async def search_insert_arrangements(request: InsertSearchRequest) -> InsertSearchResponse:
    """
    Search for insert arrangements matching contact requirements.
    
    Features:
    - Always returns matches (exact, close, or closest available)
    - Suggests multi-connector solutions for high pin counts
    - Correctly marks MIL-standard vs Amphenol-specific inserts
    """
    _ensure_loaded()
    
    # Build requirement summary
    total_required = sum(r.quantity for r in request.requirements)
    req_by_size = {r.size: r.quantity for r in request.requirements}
    
    exact_matches = []
    close_matches = []
    over_matches = []
    partial_matches = []  # For fallback when nothing fits perfectly
    
    for insert in INSERT_ARRANGEMENTS:
        can_fit, extra, missing, score = calculate_match_score(insert, req_by_size)
        
        if can_fit:
            # Determine match type
            total_extra = sum(extra.values())
            if total_extra == 0:
                match_type = "exact"
            elif total_extra <= 5:
                match_type = "close"
            else:
                match_type = "over"
            
            match = InsertMatch(
                shell_size=insert["shell"],
                insert_arrangement=insert["insert"],
                code=insert["code"],
                total_contacts=insert["total"],
                contact_breakdown=insert["contacts"],
                service_rating=insert["rating"],
                match_type=match_type,
                extra_positions=extra,
                is_standard=insert.get("is_standard", True),
                missing_contacts=None
            )
            
            if match_type == "exact":
                exact_matches.append(match)
            elif match_type == "close":
                close_matches.append(match)
            else:
                over_matches.append(match)
        else:
            # Track partial matches for fallback
            partial_matches.append({
                "insert": insert,
                "extra": extra,
                "missing": missing,
                "score": score
            })
    
    # Combine matches in priority order
    matches = exact_matches + close_matches + over_matches
    
    suggestion = None
    multi_connector = None
    
    # If no perfect matches, find closest alternatives
    if len(matches) == 0:
        # Sort partial matches by score (best first)
        partial_matches.sort(key=lambda x: x["score"])
        
        if partial_matches:
            # Add top 5 partial matches as suggestions
            for pm in partial_matches[:5]:
                insert = pm["insert"]
                match = InsertMatch(
                    shell_size=insert["shell"],
                    insert_arrangement=insert["insert"],
                    code=insert["code"],
                    total_contacts=insert["total"],
                    contact_breakdown=insert["contacts"],
                    service_rating=insert["rating"],
                    match_type="partial",
                    extra_positions=pm["extra"],
                    is_standard=insert.get("is_standard", True),
                    missing_contacts=pm["missing"]
                )
                matches.append(match)
            
            # Generate suggestion
            best = partial_matches[0]
            missing_str = ", ".join(f"{qty}× {size}" for size, qty in best["missing"].items())
            suggestion = f"No exact fit found. Closest option needs {missing_str} more positions or different sizes."
    
    # Check if multi-connector solution is needed
    # If total > 128 OR we only found partial matches (no exact/close/over)
    has_good_match = any(m.match_type in ["exact", "close", "over"] for m in matches)
    
    if total_required > MAX_SINGLE_CONNECTOR or not has_good_match:
        combo = find_multi_connector_solution(req_by_size, total_required)
        
        if combo:
            insert1, insert2, remaining = combo
            
            mc1 = InsertMatch(
                shell_size=insert1["shell"],
                insert_arrangement=insert1["insert"],
                code=insert1["code"],
                total_contacts=insert1["total"],
                contact_breakdown=insert1["contacts"],
                service_rating=insert1["rating"],
                match_type="suggestion",
                extra_positions={},
                is_standard=insert1.get("is_standard", True)
            )
            
            mc2 = InsertMatch(
                shell_size=insert2["shell"],
                insert_arrangement=insert2["insert"],
                code=insert2["code"],
                total_contacts=insert2["total"],
                contact_breakdown=insert2["contacts"],
                service_rating=insert2["rating"],
                match_type="suggestion",
                extra_positions={},
                is_standard=insert2.get("is_standard", True)
            )
            
            multi_connector = MultiConnectorSuggestion(
                connector_1=mc1,
                connector_2=mc2,
                total_capacity=insert1["total"] + insert2["total"],
                covers_requirements=True,
                note=f"Use two connectors: {insert1['code']} + {insert2['code']} for {total_required} contacts"
            )
            
            if not suggestion:
                suggestion = f"💡 Consider using two connectors for {total_required} contacts"
    
    # Sort by preference: standard first, then by match quality
    match_order = {"exact": 0, "close": 1, "over": 2, "partial": 3, "suggestion": 4}
    matches.sort(key=lambda m: (0 if m.is_standard else 1, match_order.get(m.match_type, 5), m.total_contacts))
    
    return InsertSearchResponse(
        matches=matches[:10],
        total_requirements=total_required,
        suggestion=suggestion,
        multi_connector=multi_connector
    )


@router.get("/contact-info/{size}/{contact_type}/{quantity}")
async def get_contact_ordering_info(size: str, contact_type: str, quantity: int) -> ContactOrderInfo:
    """Get ordering information for contacts"""
    _ensure_loaded()
    
    info = (CONTACT_PART_NUMBERS or {}).get(size, {})
    
    return ContactOrderInfo(
        size=size,
        contact_type=contact_type,
        quantity=quantity,
        military_pn=info.get(contact_type),
        commercial_pn=None,  # Would be looked up from DB
        seal_plug_pn=info.get("seal")
    )


class GeneratePartNumberRequest(BaseModel):
    """Request to generate a full MIL part number"""
    insert_code: str  # e.g., "19-35"
    connector_type: str  # e.g., "24"
    finish_code: str  # e.g., "W"
    contact_type: str  # "P" or "S"
    key_position: str  # "N", "A", etc.
    shell_class: str = "E"  # Default to E


class GeneratedPartNumber(BaseModel):
    """Generated part number with breakdown"""
    full_part_number: str
    breakdown: Dict[str, str]
    is_standard: bool
    availability_note: str


@router.post("/generate-part-number")
async def generate_part_number(request: GeneratePartNumberRequest) -> GeneratedPartNumber:
    """Generate a complete D38999 MIL part number"""
    _ensure_loaded()
    
    # Parse shell size and insert from selection (e.g., "21-39" -> shell="21", insert="39")
    shell_size_num, insert_code_short = request.insert_code.split("-")
    
    # 1. Look up the correct Shell Letter (e.g., "21" -> "G")
    from services.knowledge_base import get_shell_sizes
    shell_map = get_shell_sizes()
    if shell_size_num not in shell_map:
        # Fallback if somehow not found (shouldn't happen with valid data)
        shell_letter = request.shell_class 
    else:
        shell_letter = shell_map[shell_size_num]["letter"]
        
    # 2. Check Mil-Standard Status
    insert_data = next((i for i in INSERT_ARRANGEMENTS if i["code"] == request.insert_code), None)
    insert_is_standard = insert_data.get("is_standard", True) if insert_data else True
    
    # Build the part number: D38999/[Type][Finish][ShellLetter][Insert][Contact][Key]
    # Example: D38999/24 + W + G + 39 + P + N -> D38999/24WG39PN
    full_pn = f"D38999/{request.connector_type}{request.finish_code}{shell_letter}{insert_code_short}{request.contact_type}{request.key_position}"
    
    breakdown = {
        "spec": "D38999",
        "connector_type": request.connector_type,
        "finish": request.finish_code,
        "shell_size_code": shell_letter,
        "shell_size_num": shell_size_num,
        "insert_arrangement": insert_code_short,
        "contact_type": request.contact_type,
        "key_position": request.key_position,
    }
    
    # Check if this is a standard configuration
    is_standard = (
        insert_is_standard and
        request.connector_type in ["20", "24", "26"] and
        request.finish_code in ["W", "F", "T"] and
        request.key_position == "N"
    )
    
    if not insert_is_standard:
        note = "⚠️ Amphenol-specific insert arrangement - not MIL-standard"
    elif is_standard:
        note = "✅ Standard MIL configuration - typically in stock or short lead time"
    else:
        note = "⏳ Non-standard configuration - may require longer lead time"
    
    return GeneratedPartNumber(
        full_part_number=full_pn,
        breakdown=breakdown,
        is_standard=is_standard,
        availability_note=note
    )
