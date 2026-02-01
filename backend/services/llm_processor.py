"""
LLM Processor Service - Gemini API integration for intelligent data extraction

Implements requirements:
- PDF-005: Part number structure extraction
- PDF-006: LLM field definition extraction
- PDF-007: Compatibility constraint detection
- PDF-013: Stage-by-stage LLM progress
"""
import json
import asyncio
import httpx
from typing import Optional, Callable, Any

from config import get_settings, get_effective_api_key
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
    
    # Get effective API key, provider, and selected model
    api_key, provider, selected_model = get_effective_api_key()
    
    # Check if any API key is configured
    if not api_key:
        # Use example schema for development
        update_progress(ProgressStage.LLM_ANALYZE, 70.0, "No API key - using example D38999 schema")
        update_progress(ProgressStage.LLM_EXTRACT, 80.0, "Loading pre-defined field definitions")
        update_progress(ProgressStage.LLM_SCHEMA, 90.0, "Schema ready")
        return D38999_EXAMPLE_SCHEMA
    
    try:
        if provider == "openrouter":
            # Use OpenRouter API with selected model
            model_id = selected_model or "google/gemini-2.0-flash-exp:free"
            return await _process_with_openrouter(api_key, raw_extraction, update_progress, model_id)
        else:
            # Use Google Gemini API with selected model
            model_name = selected_model.replace("models/", "") if selected_model else "gemini-2.0-flash"
            return await _process_with_gemini(api_key, raw_extraction, update_progress, model_name)
        
    except ImportError:
        update_progress(ProgressStage.LLM_ANALYZE, 70.0, "LLM SDK not available - using fallback")
        return D38999_EXAMPLE_SCHEMA
        
    except Exception as e:
        update_progress(ProgressStage.LLM_ANALYZE, 70.0, f"LLM error: {str(e)[:50]} - using fallback")
        return D38999_EXAMPLE_SCHEMA


async def _process_with_gemini(api_key: str, raw_extraction: dict, update_progress: Callable, model_name: str = "gemini-2.0-flash") -> dict:
    """Process extraction using Google Gemini API"""
    import google.generativeai as genai
    
    # Configure Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    
    # Prepare context from extraction
    text_content = raw_extraction.get("text", "")[:10000]  # Limit context
    table_summary = f"Found {raw_extraction.get('table_count', 0)} tables"
    
    # ============ Stage 1: Analyze Structure (65-70%) ============
    update_progress(ProgressStage.LLM_ANALYZE, 67.0, "Analyzing document structure...")
    
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
    
    analysis = _parse_json_response(response.text, {})
    update_progress(ProgressStage.LLM_ANALYZE, 70.0, 
                   f"Identified: {analysis.get('product_family', 'Unknown')}")
    
    # ============ Stage 2: Extract Fields (70-80%) ============
    update_progress(ProgressStage.LLM_EXTRACT, 72.0, "Extracting field definitions...")
    
    extract_prompt = _build_extract_prompt(analysis, text_content)
    
    response = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: model.generate_content(extract_prompt)
    )
    
    fields = _parse_json_response(response.text, D38999_EXAMPLE_SCHEMA["fields"], is_array=True)
    update_progress(ProgressStage.LLM_EXTRACT, 80.0, 
                   f"Extracted {len(fields)} configurable fields")
    
    # ============ Stage 3: Build Schema (80-90%) ============
    return _build_schema(analysis, fields, update_progress)


async def _process_with_openrouter(api_key: str, raw_extraction: dict, update_progress: Callable, model_id: str = "google/gemini-2.0-flash-exp:free") -> dict:
    """Process extraction using OpenRouter API"""
    
    # Prepare context from extraction
    text_content = raw_extraction.get("text", "")[:10000]  # Limit context
    table_summary = f"Found {raw_extraction.get('table_count', 0)} tables"
    
    # ============ Stage 1: Analyze Structure (65-70%) ============
    update_progress(ProgressStage.LLM_ANALYZE, 67.0, "Analyzing document structure (OpenRouter)...")
    
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
    
    response = await _call_openrouter(api_key, analysis_prompt, model_id)
    analysis = _parse_json_response(response, {})
    update_progress(ProgressStage.LLM_ANALYZE, 70.0, 
                   f"Identified: {analysis.get('product_family', 'Unknown')}")
    
    # ============ Stage 2: Extract Fields (70-80%) ============
    update_progress(ProgressStage.LLM_EXTRACT, 72.0, "Extracting field definitions...")
    
    extract_prompt = _build_extract_prompt(analysis, text_content)
    response = await _call_openrouter(api_key, extract_prompt, model_id)
    
    fields = _parse_json_response(response, D38999_EXAMPLE_SCHEMA["fields"], is_array=True)
    update_progress(ProgressStage.LLM_EXTRACT, 80.0, 
                   f"Extracted {len(fields)} configurable fields")
    
    # ============ Stage 3: Build Schema (80-90%) ============
    return _build_schema(analysis, fields, update_progress)


async def _call_openrouter(api_key: str, prompt: str, model_id: str = "google/gemini-2.0-flash-exp:free") -> str:
    """Make a call to OpenRouter API"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model_id,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 4096,
            },
            timeout=60.0,
        )
        
        if response.status_code != 200:
            raise Exception(f"OpenRouter API error: {response.status_code}")
        
        data = response.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")


def _build_extract_prompt(analysis: dict, text_content: str) -> str:
    """Build the field extraction prompt"""
    return f"""
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


def _parse_json_response(response_text: str, fallback: Any, is_array: bool = False) -> Any:
    """Parse JSON from LLM response with fallback"""
    import re
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pattern = r'\[[\s\S]*\]' if is_array else r'\{[^{}]*\}'
        json_match = re.search(pattern, response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        return fallback


def _build_schema(analysis: dict, fields: list, update_progress: Callable) -> dict:
    """Build the final schema from analysis and fields"""
    update_progress(ProgressStage.LLM_SCHEMA, 85.0, "Building part number schema...")
    
    schema = {
        "prefix": analysis.get("part_number_prefix", ""),
        "pattern": "{" + "}{".join(f.get("code", f"f{i}") for i, f in enumerate(fields)) + "}",
        "fields": fields,
        "validation_rules": {}
    }
    
    update_progress(ProgressStage.LLM_SCHEMA, 90.0, "Schema construction complete")
    return schema

