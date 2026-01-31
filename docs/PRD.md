# Product Requirements Document (PRD)
## Datasheet Part Selector Application

| **Document ID** | PRD-DPS-001 |
|-----------------|-------------|
| **Version** | 1.1 |
| **Date** | 2026-01-31 |
| **Status** | Approved |

---

## 1. Executive Summary

### 1.1 Problem Statement
Part selection from dense technical datasheets (e.g., MIL-DTL-38999 connectors) is time-consuming and error-prone. Engineers must manually cross-reference specification tables, compatibility matrices, and part number structures—leading to delays and costly selection errors.

### 1.2 Solution
An AI-powered web application that:
1. Ingests PDF datasheets
2. Extracts and structures part data using AI (Docling + LLM)
3. Provides an interactive configurator for guided part selection
4. Generates valid part numbers with compatibility validation
5. (Future) Shows real-time distributor availability and pricing

### 1.3 Target Users
- Design Engineers selecting components
- Procurement teams verifying part numbers
- Field support engineers looking up specifications

---

## 2. Functional Requirements

### 2.1 System Architecture (SYS)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| SYS-001 | System shall be a standalone web application | P1 | App runs without external dependencies beyond specified services |
| SYS-002 | Backend shall use Python with FastAPI framework | P1 | API server starts on port 8000 |
| SYS-003 | Frontend shall use Vite + React | P1 | Dev server starts on port 5173 |
| SYS-004 | System shall use SQLite for development, PostgreSQL for production | P1 | SQLAlchemy abstraction allows seamless switching |
| SYS-005 | System shall use Redis for caching distributor data | P2 | Cache stores/retrieves data with configurable TTL |
| SYS-006 | System shall expose RESTful API endpoints | P1 | OpenAPI docs available at /docs |
| SYS-007 | Architecture shall support horizontal scaling | P3 | Stateless backend, shared DB |
| SYS-008 | System shall include Docker containerization | P2 | docker-compose up starts all services |

---

### 2.2 PDF Processing Pipeline (PDF)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| PDF-001 | System shall accept PDF datasheet uploads | P1 | Drag-drop or file picker accepts .pdf files up to 50MB |
| PDF-002 | System shall use Docling for PDF parsing | P1 | Docling extracts tables, text, images |
| PDF-003 | System shall extract tabular data from PDFs | P1 | Tables detected with >90% accuracy |
| PDF-004 | System shall handle multi-page datasheets | P1 | All pages processed, data merged |
| PDF-005 | System shall extract part number structure | P1 | Part number pattern identified (e.g., D38999/XXYZ...) |
| PDF-006 | System shall use LLM to understand field definitions | P1 | Field names, codes, allowed values extracted |
| PDF-007 | System shall detect compatibility constraints | P2 | "Only valid with..." relationships captured |
| PDF-008 | System shall store original PDF for reference | P1 | PDF retrievable via API |
| PDF-009 | System shall show processing status with progress | P1 | UI shows: Uploading → Parsing → Extracting → Complete |
| PDF-010 | System shall handle parsing errors gracefully | P1 | Errors logged, user notified with actionable message |
| PDF-011 | System shall support re-processing of datasheets | P2 | User can trigger re-parse with updated settings |
| PDF-012 | System shall show **detailed progress bar** during Docling parsing | P1 | Progress shows: pages processed, tables found, estimated time |
| PDF-013 | System shall provide **stage-by-stage progress** for LLM processing | P1 | Shows: Analyzing structure → Extracting fields → Building schema → Complete |
| PDF-014 | System shall use WebSocket or Server-Sent Events for real-time progress | P1 | Progress updates without page refresh |
| PDF-015 | System shall estimate and display remaining time for long operations | P2 | "Approximately 45 seconds remaining" shown |

---

### 2.3 Database & Data Model (DB)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| DB-001 | Schema shall be datasheet-agnostic | P1 | Same schema works for any component type |
| DB-002 | System shall store raw extraction alongside normalized data | P1 | Both JSON extraction and structured records exist |
| DB-003 | System shall track datasheet versions | P2 | Version number, upload date, modification history |
| DB-004 | System shall support multiple manufacturers | P1 | Manufacturer field on datasheet records |
| DB-005 | Schema shall support configurable field definitions | P1 | Field name, code, data type, allowed values stored |
| DB-006 | System shall generate all valid part variants | P2 | Cartesian product filtered by constraints |
| DB-007 | Database shall use migrations for schema changes | P1 | Alembic migrations present and functional |
| DB-008 | System shall support soft-delete for records | P1 | Deleted records retain data with flag |
| DB-009 | System shall **never permanently delete** datasheets | P1 | Deleted items moved to archive, recoverable |
| DB-010 | System shall maintain **full revision history** for all changes | P1 | Every edit creates versioned snapshot |
| DB-011 | System shall provide **archive view** for historical documents | P2 | UI shows archived datasheets with restore option |

---

### 2.4 Frontend UI (UI)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| UI-001 | UI shall have a modern, premium aesthetic | P1 | Dark mode, gradients, micro-animations |
| UI-002 | UI shall be fully responsive | P1 | Works on desktop (1920px) to tablet (768px) |
| UI-003 | UI shall include a landing/dashboard page | P1 | Shows uploaded datasheets, quick actions |
| UI-004 | UI shall include a PDF upload page | P1 | Drag-drop zone with progress indicator |
| UI-005 | UI shall include a datasheet viewer page | P2 | Shows extracted data in formatted view |
| UI-006 | UI shall include a part configurator page | P1 | Interactive dropdowns for each field |
| UI-007 | UI shall include a part search page | P1 | Keyword and filter-based search |
| UI-008 | UI shall show the original PDF inline | P2 | PDF.js viewer embedded |
| UI-009 | UI shall use consistent design system | P1 | Reusable components, CSS variables |
| UI-010 | UI shall have intuitive navigation | P1 | Sidebar + breadcrumbs |

---

### 2.5 Part Configuration Engine (CFG)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| CFG-001 | Configurator shall dynamically load field definitions | P1 | Dropdowns populated from DB schema |
| CFG-002 | Configurator shall show live part number preview | P1 | Updates as user selects options |
| CFG-003 | Configurator shall validate option compatibility | P1 | Invalid combos disabled with tooltip |
| CFG-004 | Configurator shall decode existing part numbers | P1 | Paste part number → fields auto-populated |
| CFG-005 | Configurator shall highlight required vs optional fields | P1 | Visual distinction between required/optional |
| CFG-006 | Configurator shall show field descriptions on hover | P2 | Tooltips with spec references |
| CFG-007 | Configurator shall support "copy to clipboard" for part number | P1 | One-click copy with confirmation toast |
| CFG-008 | Configurator shall show related specifications | P2 | Displays temp range, pin count, etc. for selection |
| CFG-009 | Configurator shall allow saving configurations | P3 | User can save/name configurations for later |
| CFG-010 | System shall generate exploded part number view | P1 | Visual breakdown: D38999/[26][W][B][35][S][N] |

---

### 2.6 Part Builder (PB)

> [!NOTE]
> Added 2026-02-01 based on user requirements for a requirements-first workflow.

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| PB-001 | Part Builder shall use requirements-first workflow | P1 | User specifies contacts first, then selects insert |
| PB-002 | System shall search for insert arrangements by contact requirements | P1 | API returns matching inserts for given contact sizes/quantities |
| PB-003 | Part Builder shall show only Contact Size and Quantity in Step 1 | P1 | No Pin/Socket selection until Step 3 |
| PB-004 | System shall categorize insert matches (exact, close, over) | P1 | Match type badge shown on each insert card |
| PB-005 | Part Builder shall gray-out unavailable options (Mouser/DigiKey style) | P1 | Unavailable items dimmed, striped, non-clickable |
| PB-006 | System shall show availability indicator (Standard/Special Order) | P1 | Green for standard, yellow for special |
| PB-007 | Part Builder shall generate MIL-spec part numbers only | P1 | Format: D38999/XXYZ-NNSN |
| PB-008 | Part Builder shall show contact ordering info (M39029 part numbers) | P1 | Contact part numbers displayed with quantities |
| PB-009 | System shall calculate seal plug requirements for unused positions | P2 | Seal plug part numbers and quantities shown |
| PB-010 | Part Builder shall have 4-step wizard UI | P1 | Steps: Requirements → Insert → Configure → Part Number |
| PB-011 | System shall provide part number verification workflow | P2 | Workflow to check PN on Octopart/Mouser/DigiKey |
| PB-012 | Part Builder shall support mixed contact sizes | P1 | e.g., 15× 22D + 3× 16 in single insert |

---

### 2.7 Distributor Integration (DIST)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| DIST-001 | System shall have abstract distributor interface | P1 | Base class with search/get_stock methods |
| DIST-002 | System shall support DigiKey API integration | P2 | DigiKey client implements interface |
| DIST-003 | System shall support Mouser API integration | P2 | Mouser client implements interface |
| DIST-004 | System shall cache distributor responses | P2 | Redis cache with 15-min TTL default |
| DIST-005 | System shall display stock availability in UI | P2 | Green/yellow/red indicator per distributor |
| DIST-006 | System shall display pricing breakdown | P2 | Price tiers (1/10/100/1000+ qty) shown |
| DIST-007 | System shall link to distributor product pages | P2 | Direct links to DigiKey/Mouser pages |
| DIST-008 | API keys shall be stored securely in env vars | P1 | No hardcoded credentials |
| DIST-009 | System shall handle API rate limits gracefully | P2 | Backoff strategy, user notification |
| DIST-010 | System shall work offline without distributor data | P1 | Configurator functional, stock shows "N/A" |

---

### 2.8 User Experience (UX)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| UX-001 | System shall provide keyboard navigation | P2 | Tab through fields, Enter to confirm |
| UX-002 | System shall show loading states for all async ops | P1 | Skeleton loaders or spinners present |
| UX-003 | System shall provide helpful error messages | P1 | User-friendly, actionable error text |
| UX-004 | System shall support undo for selections | P3 | Ctrl+Z reverts last change |
| UX-005 | System shall remember user preferences | P3 | Last used datasheet, theme preference |
| UX-006 | System shall provide onboarding for new users | P3 | First-run tutorial or tooltips |
| UX-007 | System shall export configurations to CSV/PDF | P2 | Download button with format selection |

---

## 3. Non-Functional Requirements (NFR)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| NFR-001 | PDF parsing shall complete in <60s for 50-page docs | P1 | Timed test passes |
| NFR-002 | API responses shall be <200ms for cached data | P1 | p95 latency <200ms |
| NFR-003 | System shall support 50 concurrent users | P2 | Load test passes |
| NFR-004 | Code shall have >80% test coverage | P2 | pytest --cov reports >80% |
| NFR-005 | System shall follow PEP8 and ESLint standards | P1 | Linters pass with no errors |
| NFR-006 | Secrets shall not be committed to version control | P1 | .env in .gitignore, no secrets in code |
| NFR-007 | System shall log all API requests | P2 | Structured JSON logs to stdout |
| NFR-008 | Database shall have automated backups | P3 | PostgreSQL backup script exists |

---

## 4. Project Structure

```
Datasheet Part Selector/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Environment configuration
│   ├── requirements.txt           # Python dependencies
│   ├── alembic/                   # Database migrations
│   │   ├── versions/
│   │   └── env.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py            # SQLAlchemy models
│   │   └── schemas.py             # Pydantic schemas
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── datasheets.py          # PDF upload/management endpoints
│   │   ├── parts.py               # Part search/configure endpoints
│   │   └── distributors.py        # Stock/pricing endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pdf_parser.py          # Docling integration
│   │   ├── llm_processor.py       # Gemini API integration
│   │   ├── part_generator.py      # Part number logic
│   │   └── distributor_client.py  # DigiKey/Mouser clients
│   └── tests/
│       ├── conftest.py
│       ├── test_pdf_parser.py
│       ├── test_part_generator.py
│       └── test_api.py
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── public/
│   │   └── favicon.svg
│   └── src/
│       ├── main.jsx               # React entry point
│       ├── App.jsx                # Main app with routing
│       ├── index.css              # Global styles & design system
│       ├── api/
│       │   └── client.js          # API client wrapper
│       ├── components/
│       │   ├── Header.jsx
│       │   ├── Sidebar.jsx
│       │   ├── PartNumberBuilder.jsx
│       │   ├── FieldDropdown.jsx
│       │   ├── StockIndicator.jsx
│       │   └── PDFViewer.jsx
│       ├── pages/
│       │   ├── Dashboard.jsx
│       │   ├── Upload.jsx
│       │   ├── Viewer.jsx
│       │   ├── Configurator.jsx
│       │   └── Search.jsx
│       └── hooks/
│           ├── useDatasheet.js
│           └── usePart.js
│
├── datasheets/                    # Uploaded PDF storage
│   └── amphenolaerospace_D38999_IIIseriesTV-1157224.pdf
│
├── docs/
│   ├── PRD.md                     # This document
│   ├── COMPLIANCE_MATRIX.md       # Requirements traceability
│   └── ARCHITECTURE.md            # Technical deep-dive
│
├── docker-compose.yml             # Container orchestration
├── Dockerfile.backend
├── Dockerfile.frontend
├── .env.example                   # Environment template
├── .gitignore
└── README.md
```

---

## 5. UI Wireframes (Conceptual)

### 5.1 Dashboard
```
┌─────────────────────────────────────────────────────────────────┐
│  [Logo]  Datasheet Part Selector           [Search] [Settings] │
├─────────┬───────────────────────────────────────────────────────┤
│         │                                                       │
│ MENU    │   📊 DASHBOARD                                        │
│         │   ─────────────────────────────────────────────────   │
│ Dashboard│                                                       │
│ Upload  │   ┌─────────────────┐  ┌─────────────────┐            │
│ Search  │   │ + Upload New    │  │ Recent Activity │            │
│ Settings│   │   Datasheet     │  │ ─────────────── │            │
│         │   │    [Drop Zone]  │  │ D38999 viewed   │            │
│         │   └─────────────────┘  │ 5 min ago       │            │
│         │                        └─────────────────┘            │
│         │   YOUR DATASHEETS                                     │
│         │   ┌──────────────────────────────────────────────┐   │
│         │   │ 📄 D38999 Series III     Amphenol     ✓ Ready │   │
│         │   │    128 variants | Last parsed: Today 5:30 PM │   │
│         │   │    [Configure] [View PDF] [Re-parse]         │   │
│         │   └──────────────────────────────────────────────┘   │
└─────────┴───────────────────────────────────────────────────────┘
```

### 5.2 Part Configurator
```
┌─────────────────────────────────────────────────────────────────┐
│  [Logo]  D38999 Series III Configurator    [Search] [Settings] │
├─────────┬───────────────────────────────────────────────────────┤
│         │                                                       │
│ MENU    │   🔧 CONFIGURE PART                                   │
│         │   ─────────────────────────────────────────────────   │
│         │                                                       │
│         │   PART NUMBER PREVIEW                                 │
│         │   ┌──────────────────────────────────────────────┐   │
│         │   │  D38999 / 26  W  B  35  S  N                 │   │
│         │   │          ↑   ↑  ↑  ↑   ↑  ↑                  │   │
│         │   │     Series│   │  │  │   │  └─ Polarization   │   │
│         │   │     Class─┘   │  │  │   └─── Contact Style   │   │
│         │   │     Shell Size┘  │  └─────── Insert Arrange  │   │
│         │   │     Connector Type──┘                         │   │
│         │   │                                    [📋 Copy]  │   │
│         │   └──────────────────────────────────────────────┘   │
│         │                                                       │
│         │   CONFIGURATION                                       │
│         │   ┌────────────────────┐ ┌────────────────────┐      │
│         │   │ Connector Type   ▼ │ │ Class            ▼ │      │
│         │   │ Wall Mount Recpt   │ │ Olive Drab Cadmium │      │
│         │   └────────────────────┘ └────────────────────┘      │
│         │   ┌────────────────────┐ ┌────────────────────┐      │
│         │   │ Shell Size       ▼ │ │ Insert Arrange   ▼ │      │
│         │   │ Size 11 (B)        │ │ 35 (55 contacts)   │      │
│         │   └────────────────────┘ └────────────────────┘      │
│         │                                                       │
│         │   SPECIFICATIONS                                      │
│         │   ├─ Contacts: 55 (Size 22D)                         │
│         │   ├─ Temp Range: -65°C to +200°C                     │
│         │   └─ EMI Shielding: 65dB @ 10GHz                     │
│         │                                                       │
│         │   AVAILABILITY (Coming Soon)                          │
│         │   ├─ DigiKey: ── (Enable API)                        │
│         │   └─ Mouser:  ── (Enable API)                        │
└─────────┴───────────────────────────────────────────────────────┘
```

---

## 6. Scope Management

### 6.1 In Scope (MVP)
- PDF upload and Docling-based extraction
- LLM-powered field definition extraction
- Interactive part configurator
- Part number generation and decoding
- PostgreSQL persistence
- Modern, responsive UI

### 6.2 Out of Scope (Future)
- User authentication/multi-tenancy
- Mobile native apps
- Real-time collaboration
- Custom report generation
- ERP/PLM integrations (SAP, Teamcenter)

### 6.3 Scope Change Process
All scope changes shall be:
1. Documented with a unique ID (SC-XXX)
2. Added to the Compliance Matrix
3. Reviewed for impact on timeline/priority
4. Approved before implementation

---

## 7. Assumptions & Dependencies

### 7.1 Assumptions
- User has Python 3.11+ installed
- User has Node.js 18+ installed
- User can provision PostgreSQL (local or Docker)
- Gemini API key is available (or alternative LLM)

### 7.2 Dependencies
| Dependency | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Backend runtime |
| FastAPI | 0.109+ | API framework |
| Docling | Latest | PDF parsing |
| PostgreSQL | 15+ | Database |
| Node.js | 18+ | Frontend build |
| React | 18+ | UI framework |
| Vite | 5+ | Dev server/bundler |

---

## 8. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-31 | Antigravity | Initial draft |
| 1.1 | 2026-01-31 | Antigravity | Added: Detailed progress tracking (PDF-012 to PDF-015), Archiving/versioning (DB-009 to DB-011), Changed DB to SQLite for dev |
| 1.2 | 2026-02-01 | Antigravity | Added: Part Builder section (PB-001 to PB-012) with requirements-first workflow, availability gray-out, MIL part numbers |
