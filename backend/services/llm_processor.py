"""
LLM Processor Service - Gemini API integration for intelligent data extraction

Implements requirements:
- PDF-005: Part number structure extraction
- PDF-006: LLM field definition extraction
- PDF-007: Compatibility constraint detection
- PDF-013: Stage-by-stage LLM progress
"""
import json
from typing import Optional, Callable, Any

from config import get_settings
from models.schemas import ProgressStage


settings = get_settings()


# Example D38999 schema for reference/fallback
D38999_EXAMPLE_SCHEMA = {
    "prefix": "D38999/",
    "pattern": "{series}{class}{shell}{insert}{contact}{polar}",
    "fields": [
        {
            "name": "Connector Series/Type",
            "code": "series",
            "type": "enum",
            "required": True,
            "description": "Defines the connector type (receptacle, plug, etc.)",
            "values": [
                {"code": "20", "name": "Wall Mount Receptacle", "description": "Panel-mounted receptacle"},
                {"code": "21", "name": "Cable Connecting Receptacle", "description": "In-line cable receptacle"},
                {"code": "24", "name": "Cable Connecting Plug", "description": "Cable plug with backshell"},
                {"code": "26", "name": "Cable Connecting Plug", "description": "Standard cable plug"},
            ]
        },
        {
            "name": "Class (Material/Finish)",
            "code": "class",
            "type": "enum",
            "required": True,
            "description": "Shell material and plating",
            "values": [
                {"code": "W", "name": "Olive Drab Cadmium", "description": "Electroless nickel + OD cadmium"},
                {"code": "F", "name": "Electroless Nickel", "description": "Aluminum, electroless nickel"},
                {"code": "K", "name": "Stainless Steel", "description": "Passivated stainless steel"},
                {"code": "Z", "name": "Black Zinc Nickel", "description": "For RoHS compliance"},
            ]
        },
        {
            "name": "Shell Size",
            "code": "shell",
            "type": "enum",
            "required": True,
            "description": "Physical size of connector shell",
            "values": [
                {"code": "A", "name": "Size 9", "description": "0.500\" diameter"},
                {"code": "B", "name": "Size 11", "description": "0.688\" diameter"},
                {"code": "C", "name": "Size 13", "description": "0.825\" diameter"},
                {"code": "D", "name": "Size 15", "description": "0.963\" diameter"},
                {"code": "E", "name": "Size 17", "description": "1.100\" diameter"},
                {"code": "F", "name": "Size 19", "description": "1.237\" diameter"},
                {"code": "G", "name": "Size 21", "description": "1.375\" diameter"},
                {"code": "H", "name": "Size 23", "description": "1.500\" diameter"},
                {"code": "J", "name": "Size 25", "description": "1.625\" diameter"},
            ]
        },
        {
            "name": "Insert Arrangement",
            "code": "insert",
            "type": "enum",
            "required": True,
            "description": "Contact pattern/pin count",
            "values": [
                {"code": "35", "name": "55 contacts", "description": "Size 22D contacts"},
                {"code": "98", "name": "10 contacts", "description": "Mixed sizes"},
                {"code": "99", "name": "8 contacts", "description": "High current"},
            ]
        },
        {
            "name": "Contact Style",
            "code": "contact",
            "type": "enum",
            "required": True,
            "description": "Pin or socket contacts",
            "values": [
                {"code": "P", "name": "Pin", "description": "Male contacts"},
                {"code": "S", "name": "Socket", "description": "Female contacts"},
            ]
        },
        {
            "name": "Polarization",
            "code": "polar",
            "type": "enum",
            "required": False,
            "description": "Key position for orientation",
            "values": [
                {"code": "N", "name": "Normal", "description": "Standard key position"},
                {"code": "A", "name": "Position A", "description": "Rotated 45°"},
                {"code": "B", "name": "Position B", "description": "Rotated 90°"},
                {"code": "C", "name": "Position C", "description": "Rotated 135°"},
            ]
        }
    ],
    "validation_rules": {
        "shell_insert_constraints": {
            "A": ["1", "2", "3", "4", "5", "6"],
            "B": ["7", "8", "9", "10", "11", "35"],
        }
    }
}


async def process_extraction_with_llm(
    datasheet_id: str,
    raw_extraction: dict,
    progress_callback: Optional[Callable] = None
) -> dict:
    """
    Process raw extraction data with Gemini LLM (PDF-013)
    
    Stages:
    1. Analyzing structure (65-70%)
    2. Extracting fields (70-80%)
    3. Building schema (80-90%)
    """
    
    def update_progress(stage: ProgressStage, percent: float, message: str):
        if progress_callback:
            progress_callback(stage, percent, message)
    
    # Check if Gemini API key is configured
    if not settings.gemini_api_key:
        # Use example schema for development
        update_progress(ProgressStage.LLM_ANALYZE, 70.0, "No API key - using example D38999 schema")
        update_progress(ProgressStage.LLM_EXTRACT, 80.0, "Loading pre-defined field definitions")
        update_progress(ProgressStage.LLM_SCHEMA, 90.0, "Schema ready")
        return D38999_EXAMPLE_SCHEMA
    
    try:
        import google.generativeai as genai
        
        # Configure Gemini
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # ============ Stage 1: Analyze Structure (65-70%) ============
        update_progress(ProgressStage.LLM_ANALYZE, 67.0, "Analyzing document structure...")
        
        # Prepare context from extraction
        text_content = raw_extraction.get("text", "")[:10000]  # Limit context
        table_summary = f"Found {raw_extraction.get('table_count', 0)} tables"
        
        # Initial analysis prompt
        analysis_prompt = f"""
        Analyze this technical datasheet content and identify:
        1. The manufacturer and product family
        2. The part number structure/format
        3. Key specification categories
        
        Content excerpt:
        {text_content[:3000]}
        
        {table_summary}
        
        Respond in JSON format:
        {{
            "manufacturer": "...",
            "product_family": "...",
            "part_number_prefix": "...",
            "part_number_example": "...",
            "field_count_estimate": N
        }}
        """
        
        response = await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: model.generate_content(analysis_prompt)
        )
        
        try:
            analysis = json.loads(response.text)
        except json.JSONDecodeError:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{[^{}]*\}', response.text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                analysis = {}
        
        update_progress(ProgressStage.LLM_ANALYZE, 70.0, 
                       f"Identified: {analysis.get('product_family', 'Unknown')}")
        
        # ============ Stage 2: Extract Fields (70-80%) ============
        update_progress(ProgressStage.LLM_EXTRACT, 72.0, "Extracting field definitions...")
        
        # Field extraction prompt
        extract_prompt = f"""
        For this datasheet with part number format like: {analysis.get('part_number_example', 'Unknown')}
        
        Extract the configurable fields in the part number structure.
        For each field, identify:
        - Name (human readable)
        - Code (short identifier)
        - Allowed values (code, name, description)
        - Whether it's required
        
        Content:
        {text_content[:5000]}
        
        Respond as JSON array:
        [
            {{
                "name": "Field Name",
                "code": "fieldcode",
                "type": "enum",
                "required": true,
                "description": "...",
                "values": [
                    {{"code": "X", "name": "Value Name", "description": "..."}}
                ]
            }}
        ]
        """
        
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: model.generate_content(extract_prompt)
        )
        
        try:
            fields = json.loads(response.text)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\[[\s\S]*\]', response.text)
            if json_match:
                fields = json.loads(json_match.group())
            else:
                fields = D38999_EXAMPLE_SCHEMA["fields"]
        
        update_progress(ProgressStage.LLM_EXTRACT, 80.0, 
                       f"Extracted {len(fields)} configurable fields")
        
        # ============ Stage 3: Build Schema (80-90%) ============
        update_progress(ProgressStage.LLM_SCHEMA, 85.0, "Building part number schema...")
        
        # Construct the schema
        schema = {
            "prefix": analysis.get("part_number_prefix", ""),
            "pattern": "{" + "}{".join(f.get("code", f"f{i}") for i, f in enumerate(fields)) + "}",
            "fields": fields,
            "validation_rules": {}
        }
        
        update_progress(ProgressStage.LLM_SCHEMA, 90.0, "Schema construction complete")
        
        return schema
        
    except ImportError:
        update_progress(ProgressStage.LLM_ANALYZE, 70.0, "Gemini SDK not available - using fallback")
        return D38999_EXAMPLE_SCHEMA
        
    except Exception as e:
        update_progress(ProgressStage.LLM_ANALYZE, 70.0, f"LLM error: {str(e)[:50]} - using fallback")
        return D38999_EXAMPLE_SCHEMA


# Need asyncio for run_in_executor
import asyncio
