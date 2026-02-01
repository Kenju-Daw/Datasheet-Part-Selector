"""
Knowledge Base Loader

Single source of truth for D38999 connector data.
Used by both Part Builder and Chat Engine to prevent data drift.

Purpose:
- Load connector_knowledge.json
- Provide typed accessors for insert arrangements, finishes, etc.
- Generate dynamic LLM grounding prompt from data
"""
import json
import logging
import jsonschema
from pathlib import Path
from functools import lru_cache
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Path to knowledge base JSON
KB_PATH = Path(__file__).parent.parent / "data" / "connector_knowledge.json"
SCHEMA_PATH = Path(__file__).parent.parent / "data" / "schemas" / "connector_schema.json"


def validate_knowledge(data: dict) -> bool:
    """Validate KB against JSON Schema."""
    if not SCHEMA_PATH.exists():
        logger.warning(f"Schema not found at {SCHEMA_PATH}, skipping validation.")
        return True

    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema = json.load(f)

        jsonschema.validate(instance=data, schema=schema)
        return True
    except jsonschema.ValidationError as e:
        logger.error(f"KB Validation Failed: {e.message}")
        raise e
    except Exception as e:
        logger.error(f"Schema validation error: {e}")
        raise e


@lru_cache(maxsize=1)
def load_knowledge() -> Dict[str, Any]:
    """
    Load the knowledge base from JSON.
    Cached to avoid repeated file reads.
    """
    if not KB_PATH.exists():
        logger.error(f"Knowledge base not found: {KB_PATH}")
        raise FileNotFoundError(f"Knowledge base not found: {KB_PATH}")
    
    with open(KB_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Validate against schema
    validate_knowledge(data)

    logger.info(f"Loaded knowledge base v{data['metadata']['version']}")
    return data


def get_metadata() -> Dict[str, Any]:
    """Get knowledge base metadata (version, source docs, etc.)"""
    return load_knowledge()["metadata"]


def get_shell_sizes() -> Dict[str, Dict]:
    """Get shell size mappings (number -> letter, max contacts)"""
    return load_knowledge()["shell_sizes"]


def get_contact_sizes() -> List[Dict]:
    """Get contact size specifications"""
    return load_knowledge()["contact_sizes"]


def get_insert_arrangements() -> List[Dict]:
    """Get all insert arrangements"""
    return load_knowledge()["insert_arrangements"]


def get_connector_types() -> List[Dict]:
    """Get connector type options"""
    return load_knowledge()["connector_types"]


def get_shell_finishes() -> List[Dict]:
    """Get shell finish options"""
    return load_knowledge()["shell_finishes"]


def get_contact_part_numbers() -> Dict[str, Dict]:
    """Get MIL contact part numbers by size"""
    return load_knowledge()["contact_part_numbers"]


def get_critical_notes() -> List[str]:
    """Get critical notes/warnings for LLM context"""
    return load_knowledge()["critical_notes"]


def generate_grounded_prompt() -> str:
    """
    Dynamically generate LLM system prompt from knowledge base.
    This ensures Chat Engine always uses the same data as Part Builder.
    """
    kb = load_knowledge()
    lines = []
    
    # Header
    lines.append("# D38999 MIL-DTL-38999 Series III Connectors\n")
    lines.append("You are a technical assistant for D38999 circular connector selection.")
    lines.append("Use ONLY the data below. Do NOT invent part numbers or insert arrangements.\n")
    
    # Shell sizes
    lines.append("## Shell Sizes")
    lines.append("| Number | Letter | Max Contacts |")
    lines.append("|--------|--------|--------------|")
    for num, info in kb["shell_sizes"].items():
        lines.append(f"| {num} | {info['letter']} | {info['max_contacts']} |")
    lines.append("")
    
    # Contact sizes
    lines.append("## Contact Sizes (AWG)")
    lines.append("| Size | AWG Range | Amps | Description |")
    lines.append("|------|-----------|------|-------------|")
    for cs in kb["contact_sizes"]:
        lines.append(f"| {cs['code']} | {cs['awg_range']} | {cs['amps']}A | {cs['description']} |")
    lines.append("")
    
    # Insert arrangements - MIL standard
    lines.append("## Insert Arrangements (MIL-STD)")
    lines.append("| Code | Shell | Total | Breakdown | Rating |")
    lines.append("|------|-------|-------|-----------|--------|")
    for ins in kb["insert_arrangements"]:
        if ins["is_mil_standard"]:
            breakdown = ", ".join(f"{v}×{k}" for k, v in ins["contacts"].items())
            lines.append(f"| {ins['code']} | {ins['shell']} | {ins['total']} | {breakdown} | {ins['rating']} |")
    lines.append("")
    
    # Insert arrangements - Manufacturer specific
    lines.append("## Insert Arrangements (Manufacturer-Specific)")
    lines.append("| Code | Shell | Total | Breakdown | Notes |")
    lines.append("|------|-------|-------|-----------|-------|")
    for ins in kb["insert_arrangements"]:
        if not ins["is_mil_standard"]:
            breakdown = ", ".join(f"{v}×{k}" for k, v in ins["contacts"].items())
            notes = ins.get("notes", "")
            lines.append(f"| {ins['code']} | {ins['shell']} | {ins['total']} | {breakdown} | {notes} |")
    lines.append("")
    
    # Connector types
    lines.append("## Connector Types")
    lines.append("| Code | Name | Standard |")
    lines.append("|------|------|----------|")
    for ct in kb["connector_types"]:
        std = "✅ MIL" if ct["is_mil_standard"] else "⚠️ Vendor"
        lines.append(f"| {ct['code']} | {ct['name']} | {std} |")
    lines.append("")
    
    # Shell finishes
    lines.append("## Shell Finishes")
    lines.append("| Code | Name | RoHS | Description |")
    lines.append("|------|------|------|-------------|")
    for sf in kb["shell_finishes"]:
        rohs = "✅" if sf["rohs_compliant"] else "❌"
        lines.append(f"| {sf['code']} | {sf['name']} | {rohs} | {sf['description']} |")
    lines.append("")
    
    # Contact part numbers
    lines.append("## Contact Part Numbers (MIL-SPEC)")
    lines.append("| Size | Pin | Socket | Seal |")
    lines.append("|------|-----|--------|------|")
    for size, pns in kb["contact_part_numbers"].items():
        seal = pns["seal"] or "—"
        lines.append(f"| {size} | {pns['pin']} | {pns['socket']} | {seal} |")
    lines.append("")
    
    # Critical notes
    lines.append("## ⚠️ CRITICAL NOTES")
    for note in kb["critical_notes"]:
        lines.append(f"- **{note}**")
    lines.append("")
    
    # Guidance
    lines.append("## Recommendation Process")
    lines.append("1. Identify required contact counts by size (from AWG)")
    lines.append("2. Find insert arrangement with sufficient contacts of each size")
    lines.append("3. Select smallest shell that fits the insert")
    lines.append("4. For mixed power+signal, consider mixed-contact inserts (e.g., 21-39)")
    lines.append("5. ALWAYS provide specific part numbers when possible")
    lines.append("")
    
    return "\n".join(lines)


def reload_knowledge():
    """Clear cache and reload knowledge base (for hot-reload)"""
    load_knowledge.cache_clear()
    return load_knowledge()


# CLI for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Knowledge Base CLI")
    parser.add_argument("--validate", action="store_true", help="Validate JSON structure")
    parser.add_argument("--prompt", action="store_true", help="Print generated LLM prompt")
    parser.add_argument("--info", action="store_true", help="Print KB info")
    args = parser.parse_args()
    
    if args.validate:
        try:
            kb = load_knowledge()
            print(f"✅ Knowledge base valid (v{kb['metadata']['version']})")
            print(f"   - {len(kb['insert_arrangements'])} insert arrangements")
            print(f"   - {len(kb['connector_types'])} connector types")
            print(f"   - {len(kb['shell_finishes'])} shell finishes")
        except Exception as e:
            print(f"❌ Validation failed: {e}")
    
    elif args.prompt:
        print(generate_grounded_prompt())
    
    elif args.info:
        kb = load_knowledge()
        print(json.dumps(kb["metadata"], indent=2))
    
    else:
        parser.print_help()
