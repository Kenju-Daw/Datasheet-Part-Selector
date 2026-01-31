---
description: Upload and process a new PDF datasheet
---

# Upload Datasheet Workflow

## Prerequisites
- Backend server running at http://localhost:8000
- Frontend running at http://localhost:5173

## Via Frontend UI
1. Navigate to http://localhost:5173/upload
2. Drag and drop a PDF file (max 50MB)
3. Fill in optional metadata:
   - **Name**: Human-readable name (e.g., "D38999 Series III")
   - **Manufacturer**: Company name (e.g., "Amphenol")
4. Click "Start Processing"
5. Watch the progress bar showing:
   - Pages processed
   - Tables found
   - Estimated time remaining

## Via API (curl)
```powershell
curl -X POST "http://localhost:8000/api/datasheets/upload" `
  -F "file=@path/to/datasheet.pdf" `
  -F "name=D38999 Series III" `
  -F "manufacturer=Amphenol"
```

## Monitor Progress via SSE
Connect to the progress stream:
```javascript
const eventSource = new EventSource('/api/progress/{datasheet_id}');
eventSource.addEventListener('progress', (e) => console.log(JSON.parse(e.data)));
```

## Processing Stages
| Stage | Description |
|-------|-------------|
| `docling_init` | Initializing Docling PDF parser |
| `docling_pages` | Parsing PDF structure |
| `docling_tables` | Extracting tables |
| `llm_analyze` | Analyzing with Gemini API |
| `llm_extract` | Extracting field definitions |
| `llm_schema` | Building part number schema |
| `complete` | Ready for configuration |

## After Processing
- Datasheet appears in Dashboard
- Click "Configure" to use the Part Number Builder
- Schema available at `/api/parts/schema/{datasheet_id}`
