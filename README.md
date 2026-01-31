# Datasheet Part Selector

Transform dense PDF datasheets into intuitive, interactive web applications for streamlined part selection.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Gemini API Key (optional, for intelligent extraction)

### Backend Setup
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt

# Configure environment
copy ..\.env.example ..\.env
# Edit .env and add your GEMINI_API_KEY

# Run the server
python main.py
```

The API will be available at http://localhost:8000

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

The UI will be available at http://localhost:5173

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [PRD](docs/PRD.md) | 79 requirements across 8 categories |
| [Compliance Matrix](docs/COMPLIANCE_MATRIX.md) | Full traceability |
| [Development Guidelines](docs/DEVELOPMENT_GUIDELINES.md) | Best practices |
| [Skills](/.agent/skills/datasheet-selector/SKILL.md) | Gemini API, storage, frontend rules |

## 🔧 Workflows

Use these slash commands for common tasks:
- `/start-dev` - Start development environment
- `/upload-datasheet` - Upload and process a PDF
- `/add-datasheet-type` - Add support for new datasheets

## 🏗️ Project Structure

```
├── backend/          # FastAPI Python backend
│   ├── main.py       # Entry point
│   ├── models/       # SQLAlchemy + Pydantic
│   ├── routers/      # API endpoints
│   └── services/     # Docling + Gemini integration
├── frontend/         # Vite + React UI
├── datasheets/       # Uploaded PDFs
└── docs/             # Documentation
```

## ✨ Features

- **PDF Upload**: Drag-drop datasheets for automatic parsing
- **Docling Extraction**: AI-powered table and text extraction
- **LLM Processing**: Gemini understands part number structures
- **Live Configurator**: Select options, get valid part numbers
- **Progress Tracking**: Real-time SSE updates during processing
- **Archive System**: Never lose data, restore anytime

## 📄 License

MIT
