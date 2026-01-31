# Datasheet Part Selector - Development Guidelines

## Best Practices Reference

This document contains quick-reference rules for developers working on this project.

---

## Gemini API Rules

### DO ✅
- Use structured JSON prompts with clear output format
- Provide fallback schemas for known part families
- Log all LLM responses for debugging
- Limit context to 10,000 characters
- Handle JSON parsing errors with regex fallback

### DON'T ❌
- Don't send entire PDFs to the API (use extracted text/tables)
- Don't hardcode API keys in source files
- Don't trust LLM output without validation
- Don't make synchronous calls without timeout

---

## Database Rules

### DO ✅
- Use soft-delete (`is_deleted = True`) - never permanent delete
- Create revisions before any datasheet modification
- Store original PDF files for reference
- Use SQLAlchemy async sessions
- Index `full_part_number` for search

### DON'T ❌
- Don't delete rows from datasheets or revisions
- Don't modify `raw_extraction` after initial save
- Don't use raw SQL queries - use SQLAlchemy ORM
- Don't store sensitive data in the database

---

## Frontend Rules

### DO ✅
- Use CSS variables from `index.css` for all colors
- Show loading skeletons during API calls
- Display toast notifications for user actions
- Use SSE for real-time progress updates
- Include copy-to-clipboard for part numbers

### DON'T ❌
- Don't hardcode colors or fonts
- Don't make API calls without error handling
- Don't block UI during long operations
- Don't use alert() - use toast component

---

## Part Number Builder Rules

### Required Features
1. Live preview that updates on selection
2. Exploded view with segment labels
3. One-click copy with visual feedback
4. Validation errors for invalid combinations
5. Monospace font for part numbers

### Field Dropdowns
- Show code + name: `"W — Olive Drab Cadmium"`
- Include description on selection
- Mark required fields with asterisk
- Disable invalid options based on constraints

---

## Progress Tracking Rules

### Must Display
- Current stage name (human-readable)
- Percentage (0-100%)
- Pages processed / total
- Tables found count
- Estimated time remaining

### Implementation
- Use Server-Sent Events (SSE) for real-time updates
- Update database progress_percent periodically
- Calculate time estimates from elapsed time + percentage

---

## File Organization

```
backend/
├── main.py              # Entry point, SSE endpoint
├── config.py            # Environment settings
├── models/
│   ├── database.py      # SQLAlchemy models
│   └── schemas.py       # Pydantic schemas
├── routers/
│   ├── datasheets.py    # Upload, archive, reprocess
│   └── parts.py         # Configure, decode, search
└── services/
    ├── pdf_parser.py    # Docling integration
    └── llm_processor.py # Gemini API

frontend/src/
├── App.jsx              # Routing
├── index.css            # Design system
├── api/client.js        # API wrapper
├── components/          # Reusable components
└── pages/               # Route pages
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Start backend | `cd backend; .\venv\Scripts\activate; python main.py` |
| Start frontend | `cd frontend; npm run dev` |
| API docs | http://localhost:8000/docs |
| Frontend | http://localhost:5173 |

| Requirement | Location |
|-------------|----------|
| PRD | `/docs/PRD.md` |
| Compliance Matrix | `/docs/COMPLIANCE_MATRIX.md` |
| Workflows | `/.agent/workflows/` |
| Skills | `/.agent/skills/datasheet-selector/` |
