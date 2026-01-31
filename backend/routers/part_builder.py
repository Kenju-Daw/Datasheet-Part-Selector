"""
Part Builder API Router

Provides endpoints for:
- Insert arrangement search by contact requirements
- Part number generation
- Contact ordering info
- Availability checking
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Optional
from pydantic import BaseModel
import json

from models import Datasheet, PartSchema, SpecField, get_session

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
    match_type: str  # "exact", "close", "over"
    extra_positions: Dict[str, int]  # unused positions
    is_standard: bool  # availability indicator


class InsertSearchResponse(BaseModel):
    """Search results"""
    matches: List[InsertMatch]
    total_requirements: int


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


# ============ Insert Arrangement Data (from parsed D38999) ============

# This would normally come from the database, but for now we hardcode the key data
INSERT_ARRANGEMENTS = [
    {"code": "9-2", "shell": "9", "insert": "2", "total": 2, "contacts": {"20": 2}, "rating": "I"},
    {"code": "15-4", "shell": "15", "insert": "4", "total": 4, "contacts": {"16": 4}, "rating": "II"},
    {"code": "15-15", "shell": "15", "insert": "15", "total": 15, "contacts": {"22": 14, "16": 1}, "rating": "I"},
    {"code": "15-18", "shell": "15", "insert": "18", "total": 18, "contacts": {"22": 18}, "rating": "I"},
    {"code": "15-19", "shell": "15", "insert": "19", "total": 19, "contacts": {"22": 19}, "rating": "I"},
    {"code": "15-25", "shell": "15", "insert": "25", "total": 25, "contacts": {"22D": 22, "16": 3}, "rating": "M"},
    {"code": "15-35", "shell": "15", "insert": "35", "total": 37, "contacts": {"22D": 37}, "rating": "M"},
    {"code": "17-2", "shell": "17", "insert": "2", "total": 39, "contacts": {"22D": 38, "8TW": 1}, "rating": "M"},
    {"code": "17-6", "shell": "17", "insert": "6", "total": 6, "contacts": {"12": 6}, "rating": "I"},
    {"code": "17-8", "shell": "17", "insert": "8", "total": 8, "contacts": {"22": 8}, "rating": "II"},
    {"code": "17-20", "shell": "17", "insert": "20", "total": 20, "contacts": {"20": 16, "16": 4}, "rating": "M"},
    {"code": "17-26", "shell": "17", "insert": "26", "total": 26, "contacts": {"22": 26}, "rating": "I"},
    {"code": "17-35", "shell": "17", "insert": "35", "total": 55, "contacts": {"22D": 55}, "rating": "M"},
    {"code": "19-11", "shell": "19", "insert": "11", "total": 11, "contacts": {"22": 11}, "rating": "II"},
    {"code": "19-18", "shell": "19", "insert": "18", "total": 18, "contacts": {"22D": 14, "8TW": 4}, "rating": "M"},
    {"code": "19-28", "shell": "19", "insert": "28", "total": 28, "contacts": {"22": 16, "8TW": 1}, "rating": "M"},
    {"code": "19-32", "shell": "19", "insert": "32", "total": 32, "contacts": {"22": 32}, "rating": "I"},
    {"code": "19-35", "shell": "19", "insert": "35", "total": 69, "contacts": {"22D": 66, "16": 3}, "rating": "M"},
    {"code": "21-12", "shell": "21", "insert": "12", "total": 12, "contacts": {"20": 3, "12": 9}, "rating": "I"},
    {"code": "21-21", "shell": "21", "insert": "21", "total": 41, "contacts": {"22D": 32, "12": 9}, "rating": "M"},
    {"code": "21-99", "shell": "21", "insert": "99", "total": 16, "contacts": {"22D": 5, "12": 11}, "rating": "M"},
    {"code": "21-121", "shell": "21", "insert": "121", "total": 121, "contacts": {"23": 121}, "rating": "N"},
    {"code": "23-1", "shell": "23", "insert": "1", "total": 100, "contacts": {"22M": 100}, "rating": "M"},
    {"code": "23-2", "shell": "23", "insert": "2", "total": 85, "contacts": {"22": 85}, "rating": "M"},
    {"code": "25-16", "shell": "25", "insert": "16", "total": 8, "contacts": {"20": 6, "4": 2}, "rating": "M"},
    {"code": "25-92", "shell": "25", "insert": "92", "total": 101, "contacts": {"22D": 92, "16": 9}, "rating": "M"},
    {"code": "25-97", "shell": "25", "insert": "97", "total": 42, "contacts": {"22D": 26, "16": 3, "12": 13}, "rating": "M"},
]

CONNECTOR_TYPES = [
    {"code": "20", "name": "Wall Mount Receptacle", "desc": "Panel-mounted wall receptacle", "standard": True},
    {"code": "21", "name": "Box Mount Receptacle (Hermetic)", "desc": "Hermetically sealed box mount", "standard": False},
    {"code": "24", "name": "Jam Nut Receptacle", "desc": "Panel mount with jam nut", "standard": True},
    {"code": "23", "name": "Jam Nut Receptacle (Hermetic)", "desc": "Hermetically sealed jam nut", "standard": False},
    {"code": "25", "name": "Solder Mount Receptacle (Hermetic)", "desc": "Hermetic solder mount", "standard": False},
    {"code": "26", "name": "Straight Plug", "desc": "Cable-mounted straight plug", "standard": True},
    {"code": "27", "name": "Weld Mount Receptacle (Hermetic)", "desc": "Welded hermetic mount", "standard": False},
    {"code": "29", "name": "Lanyard Release Plug (Pin)", "desc": "Quick-release with pins", "standard": False},
    {"code": "30", "name": "Lanyard Release Plug (Socket)", "desc": "Quick-release with sockets", "standard": False},
]

SHELL_FINISHES = [
    {"code": "W", "name": "Olive Drab Cadmium", "desc": "500hr salt spray, -50dB EMI", "rohs": False},
    {"code": "F", "name": "Electroless Nickel", "desc": "48hr salt spray, -65dB EMI", "rohs": True},
    {"code": "T", "name": "Durmalon", "desc": "Nickel-PTFE, RoHS alt to Cadmium", "rohs": True},
    {"code": "Z", "name": "Zinc-Nickel", "desc": "500hr salt spray, RoHS", "rohs": True},
    {"code": "K", "name": "Passivated Stainless Steel", "desc": "Firewall capable, 500hr salt spray", "rohs": True},
    {"code": "L", "name": "Stainless Steel w/ Nickel", "desc": "Non-firewall, -65dB EMI", "rohs": True},
    {"code": "C", "name": "Anodic Coating", "desc": "Non-conductive, 500hr salt spray", "rohs": True},
    {"code": "G", "name": "Space Grade Nickel", "desc": "Electroless nickel for space", "rohs": True},
]

CONTACT_PART_NUMBERS = {
    "22D": {"pin": "M39029/58-360", "socket": "M39029/56-348", "seal": "MS27488-22-2"},
    "22": {"pin": "M39029/58-362", "socket": "M39029/56-350", "seal": "MS27488-22-2"},
    "20": {"pin": "M39029/58-363", "socket": "M39029/56-351", "seal": "MS27488-20-2"},
    "16": {"pin": "M39029/58-364", "socket": "M39029/56-352", "seal": "MS27488-16-2"},
    "12": {"pin": "M39029/58-365", "socket": "M39029/56-353", "seal": "MS27488-12-2"},
    "8": {"pin": "M39029/60-367", "socket": "M39029/59-366", "seal": "MS27488-8"},
    "10": {"pin": "M39029/58-528", "socket": "M39029/56-527", "seal": None},
}


# ============ API Endpoints ============

@router.get("/builder-data/{datasheet_id}")
async def get_part_builder_data(datasheet_id: str) -> PartBuilderData:
    """Get all data needed for the Part Builder UI"""
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
    """Search for insert arrangements matching contact requirements"""
    
    # Build requirement summary
    total_required = sum(r.quantity for r in request.requirements)
    req_by_size = {r.size: r.quantity for r in request.requirements}
    
    matches = []
    
    for insert in INSERT_ARRANGEMENTS:
        # Check if this insert can accommodate the requirements
        can_fit = True
        extra = {}
        
        for size, qty_needed in req_by_size.items():
            available = insert["contacts"].get(size, 0)
            if available >= qty_needed:
                extra[size] = available - qty_needed
            else:
                can_fit = False
                break
        
        if can_fit:
            # Determine match type
            total_extra = sum(extra.values())
            if total_extra == 0:
                match_type = "exact"
            elif total_extra <= 5:
                match_type = "close"
            else:
                match_type = "over"
            
            matches.append(InsertMatch(
                shell_size=insert["shell"],
                insert_arrangement=insert["insert"],
                code=insert["code"],
                total_contacts=insert["total"],
                contact_breakdown=insert["contacts"],
                service_rating=insert["rating"],
                match_type=match_type,
                extra_positions=extra,
                is_standard=True  # Most D38999 are standard
            ))
    
    # Sort by match quality (exact first, then close, then over)
    match_order = {"exact": 0, "close": 1, "over": 2}
    matches.sort(key=lambda m: (match_order[m.match_type], m.total_contacts))
    
    return InsertSearchResponse(matches=matches[:10], total_requirements=total_required)


@router.get("/contact-info/{size}/{contact_type}/{quantity}")
async def get_contact_ordering_info(size: str, contact_type: str, quantity: int) -> ContactOrderInfo:
    """Get ordering information for contacts"""
    
    info = CONTACT_PART_NUMBERS.get(size, {})
    
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
    
    shell, insert = request.insert_code.split("-")
    
    # Build the part number: D38999/[Type][Finish][Class][Shell]-[Insert][Contact][Key]
    full_pn = f"D38999/{request.connector_type}{request.finish_code}{request.shell_class}{shell}-{insert}{request.contact_type}{request.key_position}"
    
    breakdown = {
        "spec": "D38999",
        "connector_type": request.connector_type,
        "finish": request.finish_code,
        "class": request.shell_class,
        "shell_size": shell,
        "insert_arrangement": insert,
        "contact_type": request.contact_type,
        "key_position": request.key_position,
    }
    
    # Check if this is a standard configuration
    is_standard = (
        request.connector_type in ["20", "24", "26"] and
        request.finish_code in ["W", "F", "T"] and
        request.key_position == "N"
    )
    
    if is_standard:
        note = "✅ Standard configuration - typically in stock or short lead time"
    else:
        note = "⚠️ Non-standard configuration - may require longer lead time"
    
    return GeneratedPartNumber(
        full_part_number=full_pn,
        breakdown=breakdown,
        is_standard=is_standard,
        availability_note=note
    )
