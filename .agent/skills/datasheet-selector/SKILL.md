---
name: Datasheet Part Selector
description: Skills and best practices for the Datasheet Part Selector application - PDF parsing, data storage, Gemini API usage, and frontend Part Builder.
---

# Datasheet Part Selector Skill

This skill defines the standards and best practices for developing the Datasheet Part Selector application.

---

## 1. Gemini API Usage Rules

### Configuration
- **Model**: Use `gemini-1.5-flash` for speed, `gemini-1.5-pro` for accuracy
- **API Key**: Stored in `.env` as `GEMINI_API_KEY`
- **Location**: `backend/services/llm_processor.py`

### Prompt Engineering Best Practices
```python
# GOOD: Structured prompts with clear JSON output format
prompt = """
Analyze this datasheet content and extract field definitions.
Respond ONLY in valid JSON format:
{
    "fields": [
        {"name": "...", "code": "...", "values": [...]}
    ]
}
"""

# BAD: Vague prompts without structure
prompt = "What are the part number fields in this datasheet?"
```

### Error Handling
- **Always provide fallback schemas** for known part families
- **Parse JSON defensively** - use regex extraction as backup
- **Log LLM responses** for debugging extraction issues

```python
try:
    response = model.generate_content(prompt)
    result = json.loads(response.text)
except json.JSONDecodeError:
    # Fallback to regex extraction
    import re
    json_match = re.search(r'\{[\s\S]*\}', response.text)
    if json_match:
        result = json.loads(json_match.group())
    else:
        result = FALLBACK_SCHEMA
```

### Token Management
- **Limit input context** to 10,000 characters for table extraction
- **Use streaming** for long operations (progress updates)
- **Cache results** - don't re-call LLM for same datasheet

---

## 2. Data Storage Architecture

### SQLite Schema (Development)
Database file: `datasheet_selector.db` in backend root

### Key Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `datasheets` | Uploaded PDFs | id, name, status, raw_extraction |
| `datasheet_revisions` | Version history | datasheet_id, version, snapshot_data |
| `part_schemas` | Part number patterns | pattern, prefix, datasheet_id |
| `spec_fields` | Configurable options | name, code, allowed_values, position |
| `part_variants` | Generated configs | full_part_number, field_values |

### Storage Rules

1. **Never delete data permanently** - Use soft-delete (`is_deleted = True`)
2. **Archive on change** - Create revision before re-processing
3. **Store raw extraction** - Keep original Docling output in JSONB
4. **Index part numbers** - Full-text search on `full_part_number`

### File Storage
```
datasheets/
├── {uuid}_{original_filename}.pdf   # Uploaded PDFs
```
- Store original PDF for reference (requirement PDF-008)
- Use UUID prefix to prevent filename conflicts

### Archiving Pattern
```python
# Before any datasheet modification:
revision = DatasheetRevision(
    datasheet_id=datasheet.id,
    version=datasheet.version,
    snapshot_data={"raw_extraction": datasheet.raw_extraction},
    change_description="Snapshot before re-processing"
)
session.add(revision)
datasheet.version += 1
```

---

## 3. Frontend Part Selector Standards

### Component Structure
```
frontend/src/
├── components/
│   ├── Sidebar.jsx          # Navigation
│   ├── PartNumberBuilder.jsx # Live preview with exploded view
│   └── FieldDropdown.jsx     # Smart select with descriptions
├── pages/
│   ├── Dashboard.jsx         # Stats + datasheet list
│   ├── Upload.jsx            # Drag-drop + progress
│   ├── Configurator.jsx      # Part number builder
│   └── Search.jsx            # Part search
└── api/
    └── client.js             # API wrapper + SSE
```

### Design System (index.css)
- **Always use CSS variables** - Never hardcode colors
- **Dark mode default** - Use `--bg-primary: #0f0f0f`
- **Accent gradient** - `--accent-gradient` for primary buttons
- **Font stack** - Inter for UI, JetBrains Mono for part numbers

```css
/* GOOD */
.button { background: var(--accent-gradient); }

/* BAD */
.button { background: linear-gradient(...); }
```

### Part Number Builder Requirements
1. **Live preview** - Update as user selects options
2. **Exploded view** - Show segment labels below part number
3. **Copy button** - One-click clipboard copy with toast
4. **Validation feedback** - Show errors for invalid combinations
5. **Monospace font** - Use `font-family: var(--font-mono)`

### Progress Bar Requirements (PDF-012 to PDF-015)
Must show:
- Current stage name
- Percentage complete
- Pages processed / total
- Tables found
- Estimated time remaining

```jsx
<div className="progress-details">
  <div>📄 {progress.pages_processed}/{progress.pages_total} pages</div>
  <div>📊 {progress.tables_found} tables</div>
  <div>⏱️ ~{progress.estimated_seconds_remaining}s remaining</div>
</div>
```

### API Integration
- **Use SSE for progress** - EventSource to `/api/progress/{id}`
- **Handle connection errors** - Show retry button
- **Optimistic updates** - Update UI before API confirms

---

## 4. Processing Pipeline Flow

```
PDF Upload
    ↓
Docling Parsing (pages, tables)
    ↓
Store raw_extraction in DB
    ↓
Gemini LLM Analysis
    ↓
Extract field definitions
    ↓
Create PartSchema + SpecFields
    ↓
Mark datasheet as "complete"
    ↓
Ready for configuration
```

### Progress Stages
| Stage | Percent | Actions |
|-------|---------|---------|
| `upload` | 0-5% | File saved to disk |
| `docling_init` | 5-10% | Initialize parser |
| `docling_pages` | 10-30% | Parse PDF structure |
| `docling_tables` | 30-60% | Extract tables |
| `llm_analyze` | 60-70% | Analyze with Gemini |
| `llm_extract` | 70-80% | Extract fields |
| `llm_schema` | 80-90% | Build schema |
| `saving` | 90-100% | Save to database |

---

## 5. Common Commands

```powershell
# Start backend
cd backend; .\venv\Scripts\activate; python main.py

# Start frontend
cd frontend; npm run dev

# Run tests
cd backend; .\venv\Scripts\activate; pytest

# Check API docs
Start-Process "http://localhost:8000/docs"

# View database
sqlite3 backend/datasheet_selector.db ".tables"
```

---

## 6. Troubleshooting

| Problem | Solution |
|---------|----------|
| `No module named 'fastapi'` | Run `pip install -r requirements.txt` in venv |
| Frontend shows "Connection refused" | Start backend first |
| LLM returns wrong schema | Add fallback schema in `llm_processor.py` |
| Tables not extracted | Check PDF quality, enable OCR |
| Progress bar stuck | Check backend logs for errors |
