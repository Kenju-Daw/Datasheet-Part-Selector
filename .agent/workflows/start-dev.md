---
description: Start the Datasheet Part Selector development environment
---

# Start Development Environment

// turbo-all

## Backend Setup
1. Open a terminal and navigate to the backend directory:
   ```powershell
   cd "c:\Users\kjara\Documents\GitHub\Datasheet Part Selector\backend"
   ```

2. Activate virtual environment and start server:
   ```powershell
   .\venv\Scripts\activate; python main.py
   ```
   - Server runs at http://localhost:8000
   - API docs at http://localhost:8000/docs

## Frontend Setup
3. Open a new terminal and navigate to frontend:
   ```powershell
   cd "c:\Users\kjara\Documents\GitHub\Datasheet Part Selector\frontend"
   ```

4. Start the dev server:
   ```powershell
   npm run dev
   ```
   - UI runs at http://localhost:5173

## Quick Start Scripts
Alternatively, use the batch files in the project root:
- `start_backend.bat` - Starts the FastAPI backend
- `start_frontend.bat` - Starts the Vite dev server

## Verification
- Backend health: GET http://localhost:8000/health
- Frontend loads dashboard at http://localhost:5173
