---
description: Restart the backend server to apply code changes
---

# Restart Backend Server

// turbo-all

## Steps

1. Stop any running Python processes:
   ```powershell
   Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force -ErrorAction SilentlyContinue
   ```

2. Navigate to backend directory and start server:
   ```powershell
   cd "c:\Users\kjara\Documents\GitHub\Datasheet Part Selector\backend"
   .\venv\Scripts\activate; python main.py
   ```

## (Optional) Clear Stuck Database Records

If you have datasheets stuck in "Parsing" or "Error" status:
```powershell
.\venv\Scripts\activate; python clear_stuck.py
```

## When to Use
- After making code changes to backend files
- After fixing bugs in services or routers
- When the server becomes unresponsive
- When processes get stuck

## Verification
- Server should show "Uvicorn running on http://0.0.0.0:8000"
- Check http://localhost:8000/docs loads the API documentation
- Console should show print statements for any PDF processing

## Console Log Indicators
When processing a PDF, watch for these console messages:
- `[xxxxxxxx] ✓ Docling import successful`
- `[xxxxxxxx] Creating DocumentConverter...`
- `[xxxxxxxx] Starting PDF conversion (this takes several minutes)...`
- `[xxxxxxxx] ✓ PDF conversion complete!`
