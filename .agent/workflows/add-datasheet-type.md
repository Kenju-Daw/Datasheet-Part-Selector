---
description: Add a new datasheet type (not D38999) to the system
---

# Add New Datasheet Type

This workflow guides adding support for a new connector/component datasheet.

## 1. Gather Information
Before starting, collect:
- [ ] PDF datasheet file
- [ ] Part number examples (5-10 different variants)
- [ ] Understanding of the part number structure
- [ ] Manufacturer name and product family

## 2. Create Fallback Schema (Optional but Recommended)
If the LLM extraction fails, add a fallback schema in:
```
backend/services/llm_processor.py
```

Add a new schema constant similar to `D38999_EXAMPLE_SCHEMA`:
```python
NEW_PART_SCHEMA = {
    "prefix": "PART-PREFIX-",
    "pattern": "{field1}{field2}{field3}",
    "fields": [
        {
            "name": "Human Readable Name",
            "code": "field1",
            "type": "enum",
            "required": True,
            "description": "What this field represents",
            "values": [
                {"code": "A", "name": "Option A", "description": "Description"}
            ]
        }
    ]
}
```

## 3. Upload the Datasheet
// turbo
1. Start the dev environment:
   ```powershell
   cd "c:\Users\kjara\Documents\GitHub\Datasheet Part Selector"
   .\start_backend.bat
   ```

2. Upload via frontend at http://localhost:5173/upload

## 4. Verify Extraction
After processing completes:
1. Check the schema via API:
   ```powershell
   curl http://localhost:8000/api/parts/schema/{datasheet_id}
   ```

2. Test configuration:
   - Open http://localhost:5173/configure/{datasheet_id}
   - Select values in each dropdown
   - Verify the generated part number matches expected format

## 5. Update Tests (If Adding Fallback)
Add test cases in `backend/tests/test_llm_processor.py` for the new schema.

## Troubleshooting
- **LLM returns wrong fields**: Add/update fallback schema
- **Tables not detected**: Check PDF quality, consider OCR
- **Part number format wrong**: Adjust `part_number_pattern` in schema
