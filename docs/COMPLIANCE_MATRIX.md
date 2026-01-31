# Compliance Matrix
## Datasheet Part Selector - Requirements Traceability

| **Document ID** | CM-DPS-001 |
|-----------------|-------------|
| **Version** | 1.1 |
| **Last Updated** | 2026-01-31 |
| **PRD Reference** | [PRD.md](file:///c:/Users/kjara/Documents/GitHub/Datasheet%20Part%20Selector/docs/PRD.md) |

---

## Status Legend

| Symbol | Status | Description |
|--------|--------|-------------|
| ⬜ | Not Started | Work has not begun |
| 🔄 | In Progress | Currently being implemented |
| ✅ | Complete | Implemented and verified |
| ⏸️ | On Hold | Blocked or deferred |
| ❌ | Cancelled | Removed from scope |

---

## 1. System Architecture (SYS)

| ID | Requirement | Priority | Status | Implementation | Verification | Notes |
|----|-------------|----------|--------|----------------|--------------|-------|
| SYS-001 | Standalone web application | P1 | ⬜ | — | — | |
| SYS-002 | Python + FastAPI backend | P1 | ⬜ | `backend/main.py` | API docs at /docs | |
| SYS-003 | Vite + React frontend | P1 | ⬜ | `frontend/` | Dev server :5173 | |
| SYS-004 | SQLite (dev) / PostgreSQL (prod) | P1 | ⬜ | `models/database.py` | DB connection test |
| SYS-005 | Redis caching | P2 | ⬜ | `docker-compose.yml` | Cache hit/miss logs | |
| SYS-006 | RESTful API endpoints | P1 | ⬜ | `backend/routers/` | OpenAPI spec | |
| SYS-007 | Horizontal scaling support | P3 | ⬜ | — | Load test | |
| SYS-008 | Docker containerization | P2 | ⬜ | `Dockerfile.*` | compose up success | |

---

## 2. PDF Processing Pipeline (PDF)

| ID | Requirement | Priority | Status | Implementation | Verification | Notes |
|----|-------------|----------|--------|----------------|--------------|-------|
| PDF-001 | PDF datasheet uploads | P1 | ⬜ | `routers/datasheets.py` | Upload 50MB file | |
| PDF-002 | Docling integration | P1 | ⬜ | `services/pdf_parser.py` | Parse D38999 PDF | |
| PDF-003 | Table extraction | P1 | ⬜ | `services/pdf_parser.py` | >90% accuracy | |
| PDF-004 | Multi-page handling | P1 | ⬜ | `services/pdf_parser.py` | 50+ page test | |
| PDF-005 | Part number structure extraction | P1 | ⬜ | `services/llm_processor.py` | D38999 pattern matched | |
| PDF-006 | LLM field definition extraction | P1 | ⬜ | `services/llm_processor.py` | Fields populated | |
| PDF-007 | Compatibility constraint detection | P2 | ⬜ | `services/llm_processor.py` | Constraints logged | |
| PDF-008 | Original PDF storage | P1 | ⬜ | `datasheets/` | PDF retrievable | |
| PDF-009 | Processing status progress | P1 | ⬜ | `pages/Upload.jsx` | UI shows stages | |
| PDF-010 | Graceful error handling | P1 | ⬜ | All services | Error toast shown | |
| PDF-011 | Re-processing support | P2 | ⬜ | `routers/datasheets.py` | Re-parse button works | |
| PDF-012 | **Detailed progress bar** for Docling | P1 | ⬜ | `services/pdf_parser.py` | Pages, tables, time shown | |
| PDF-013 | **Stage-by-stage LLM progress** | P1 | ⬜ | `services/llm_processor.py` | 4 stages displayed | |
| PDF-014 | WebSocket/SSE real-time updates | P1 | ⬜ | `routers/datasheets.py` | No page refresh needed | |
| PDF-015 | Estimated remaining time | P2 | ⬜ | `pages/Upload.jsx` | Time estimate shown | |

---

## 3. Database & Data Model (DB)

| ID | Requirement | Priority | Status | Implementation | Verification | Notes |
|----|-------------|----------|--------|----------------|--------------|-------|
| DB-001 | Datasheet-agnostic schema | P1 | ⬜ | `models/database.py` | Different component types work | |
| DB-002 | Raw + normalized data storage | P1 | ⬜ | `models/database.py` | Both JSON and records exist | |
| DB-003 | Datasheet versioning | P2 | ⬜ | `models/database.py` | Version field populated | |
| DB-004 | Multi-manufacturer support | P1 | ⬜ | `models/database.py` | Multiple manufacturers stored | |
| DB-005 | Configurable field definitions | P1 | ⬜ | `models/database.py` | Dynamic fields work | |
| DB-006 | Part variant generation | P2 | ⬜ | `services/part_generator.py` | All valid combos created | |
| DB-007 | Alembic migrations | P1 | ⬜ | `alembic/` | Migrations run clean | |
| DB-008 | Soft-delete (no permanent delete) | P1 | ⬜ | `models/database.py` | Deleted flag works | |
| DB-009 | **Archive instead of delete** | P1 | ⬜ | `models/database.py` | Items recoverable | |
| DB-010 | **Full revision history** | P1 | ⬜ | `models/database.py` | Versioned snapshots | |
| DB-011 | Archive view in UI | P2 | ⬜ | `pages/Archive.jsx` | Restore option shown | |

---

## 4. Frontend UI (UI)

| ID | Requirement | Priority | Status | Implementation | Verification | Notes |
|----|-------------|----------|--------|----------------|--------------|-------|
| UI-001 | Premium aesthetic (dark mode, animations) | P1 | ⬜ | `index.css` | Visual inspection | |
| UI-002 | Responsive design (768px-1920px) | P1 | ⬜ | `index.css` | Browser resize test | |
| UI-003 | Dashboard page | P1 | ⬜ | `pages/Dashboard.jsx` | Datasheets listed | |
| UI-004 | PDF upload page | P1 | ⬜ | `pages/Upload.jsx` | Drag-drop works | |
| UI-005 | Datasheet viewer page | P2 | ⬜ | `pages/Viewer.jsx` | Data displayed | |
| UI-006 | Part configurator page | P1 | ⬜ | `pages/Configurator.jsx` | Dropdowns functional | |
| UI-007 | Part search page | P1 | ⬜ | `pages/Search.jsx` | Search returns results | |
| UI-008 | Inline PDF viewer | P2 | ⬜ | `components/PDFViewer.jsx` | PDF renders | |
| UI-009 | Consistent design system | P1 | ⬜ | `index.css`, `components/` | CSS variables used | |
| UI-010 | Intuitive navigation | P1 | ⬜ | `components/Sidebar.jsx` | User can navigate | |

---

## 5. Part Configuration Engine (CFG)

| ID | Requirement | Priority | Status | Implementation | Verification | Notes |
|----|-------------|----------|--------|----------------|--------------|-------|
| CFG-001 | Dynamic field loading | P1 | ⬜ | `pages/Configurator.jsx` | DB-driven dropdowns | |
| CFG-002 | Live part number preview | P1 | ⬜ | `components/PartNumberBuilder.jsx` | Updates on selection | |
| CFG-003 | Compatibility validation | P1 | ⬜ | `services/part_generator.py` | Invalid disabled | |
| CFG-004 | Part number decoding | P1 | ⬜ | `services/part_generator.py` | Paste → auto-fill | |
| CFG-005 | Required/optional field indication | P1 | ⬜ | `components/FieldDropdown.jsx` | Visual distinction | |
| CFG-006 | Field tooltips | P2 | ⬜ | `components/FieldDropdown.jsx` | Hover shows info | |
| CFG-007 | Copy to clipboard | P1 | ⬜ | `components/PartNumberBuilder.jsx` | Copy + toast | |
| CFG-008 | Related specifications display | P2 | ⬜ | `pages/Configurator.jsx` | Specs shown | |
| CFG-009 | Save configurations | P3 | ⬜ | `routers/parts.py` | Saved configs persist | |
| CFG-010 | Exploded part number view | P1 | ⬜ | `components/PartNumberBuilder.jsx` | Segments labeled | |

---

## 6. Part Builder (PB)

> Added 2026-02-01 - Requirements-first workflow for D38999 connectors

| ID | Requirement | Priority | Status | Implementation | Verification | Notes |
|----|-------------|----------|--------|----------------|--------------|-------|
| PB-001 | Requirements-first workflow | P1 | ✅ | `pages/PartBuilder.jsx` | 4-step wizard | User specifies contacts first |
| PB-002 | Insert search by contact requirements | P1 | ✅ | `routers/part_builder.py` | API tested | Returns exact/close/over matches |
| PB-003 | Step 1 shows only Size + Quantity | P1 | ✅ | `pages/PartBuilder.jsx` | UI verified | Pin/Socket in Step 3 |
| PB-004 | Match categorization (exact/close/over) | P1 | ✅ | `routers/part_builder.py` | Badges shown | Color-coded badges |
| PB-005 | Gray-out unavailable options | P1 | ✅ | `pages/PartBuilder.jsx` | Visual inspection | Mouser/DigiKey style |
| PB-006 | Availability indicator | P1 | ✅ | `pages/PartBuilder.jsx` | Standard/Special shown | Green/yellow indicators |
| PB-007 | MIL-spec part numbers only | P1 | ✅ | `routers/part_builder.py` | Format verified | D38999/XXYZ-NNSN |
| PB-008 | Contact ordering info (M39029) | P1 | ✅ | `pages/PartBuilder.jsx` | Part numbers shown | Pin/socket part numbers |
| PB-009 | Seal plug calculation | P2 | ⬜ | — | — | Future enhancement |
| PB-010 | 4-step wizard UI | P1 | ✅ | `pages/PartBuilder.jsx` | Steps verified | Requirements→Insert→Config→PN |
| PB-011 | Part number verification workflow | P2 | ✅ | `.agent/workflows/` | Workflow created | `/verify-part-number` |
| PB-012 | Mixed contact sizes support | P1 | ✅ | `routers/part_builder.py` | API tested | 15×22D + 3×16 works |

---

## 7. Distributor Integration (DIST)

| ID | Requirement | Priority | Status | Implementation | Verification | Notes |
|----|-------------|----------|--------|----------------|--------------|-------|
| DIST-001 | Abstract distributor interface | P1 | ⬜ | `services/distributor_client.py` | Base class exists | |
| DIST-002 | DigiKey API integration | P2 | ⬜ | `services/distributor_client.py` | API calls work | |
| DIST-003 | Mouser API integration | P2 | ⬜ | `services/distributor_client.py` | API calls work | |
| DIST-004 | Response caching | P2 | ⬜ | `services/distributor_client.py` | Redis cached | |
| DIST-005 | Stock availability display | P2 | ⬜ | `components/StockIndicator.jsx` | Indicators shown | |
| DIST-006 | Pricing breakdown | P2 | ⬜ | `pages/Configurator.jsx` | Price tiers shown | |
| DIST-007 | Distributor page links | P2 | ⬜ | `pages/Configurator.jsx` | Links work | |
| DIST-008 | Secure API key storage | P1 | ⬜ | `.env`, `config.py` | No hardcoded secrets | |
| DIST-009 | Rate limit handling | P2 | ⬜ | `services/distributor_client.py` | Backoff tested | |
| DIST-010 | Offline functionality | P1 | ⬜ | `pages/Configurator.jsx` | Works without APIs | |

---

## 8. User Experience (UX)

| ID | Requirement | Priority | Status | Implementation | Verification | Notes |
|----|-------------|----------|--------|----------------|--------------|-------|
| UX-001 | Keyboard navigation | P2 | ⬜ | All pages | Tab navigation works | |
| UX-002 | Loading states | P1 | ⬜ | All pages | Spinners/skeletons shown | |
| UX-003 | Helpful error messages | P1 | ⬜ | All pages | Clear error text | |
| UX-004 | Undo support | P3 | ⬜ | `pages/Configurator.jsx` | Ctrl+Z works | |
| UX-005 | Preference persistence | P3 | ⬜ | LocalStorage | Prefs remembered | |
| UX-006 | Onboarding flow | P3 | ⬜ | `components/` | Tutorial shown | |
| UX-007 | Export to CSV/PDF | P2 | ⬜ | `pages/Configurator.jsx` | Download works | |

---

## 9. Non-Functional Requirements (NFR)

| ID | Requirement | Priority | Status | Implementation | Verification | Notes |
|----|-------------|----------|--------|----------------|--------------|-------|
| NFR-001 | PDF parsing <60s | P1 | ⬜ | `services/pdf_parser.py` | Timed test | |
| NFR-002 | API <200ms (cached) | P1 | ⬜ | All routers | Latency test | |
| NFR-003 | 50 concurrent users | P2 | ⬜ | Load test | Artillery/k6 test | |
| NFR-004 | >80% test coverage | P2 | ⬜ | `tests/` | pytest --cov | |
| NFR-005 | PEP8/ESLint compliance | P1 | ⬜ | All code | Linters pass | |
| NFR-006 | No committed secrets | P1 | ⬜ | `.gitignore` | Audit pass | |
| NFR-007 | Structured logging | P2 | ⬜ | All services | JSON logs | |
| NFR-008 | Automated backups | P3 | ⬜ | Scripts | Backup runs | |

---

## 10. Scope Changes Log

| ID | Date | Description | Impact | Status | Approved By |
|----|------|-------------|--------|--------|-------------|
| SC-001 | 2026-01-31 | Initial scope defined | — | ✅ | User |
| SC-002 | 2026-01-31 | Added detailed progress tracking (PDF-012 to PDF-015) | +4 reqs | ✅ | User |
| SC-003 | 2026-01-31 | Added archiving/versioning (DB-009 to DB-011) | +3 reqs | ✅ | User |
| SC-004 | 2026-01-31 | Changed DB from PostgreSQL to SQLite for dev | Simpler setup | ✅ | User |
| SC-005 | 2026-02-01 | Added Part Builder (PB-001 to PB-012) | +12 reqs | ✅ | User |

---

## 11. Summary Statistics

| Category | Total | P1 | P2 | P3 | Complete | In Progress |
|----------|-------|----|----|----|---------:|------------:|
| SYS | 8 | 4 | 2 | 2 | 0 | 0 |
| PDF | 15 | 11 | 4 | 0 | 0 | 0 |
| DB | 11 | 8 | 2 | 1 | 0 | 0 |
| UI | 10 | 7 | 3 | 0 | 0 | 0 |
| CFG | 10 | 7 | 2 | 1 | 0 | 0 |
| **PB** | **12** | **10** | **2** | **0** | **11** | **0** |
| DIST | 10 | 2 | 7 | 1 | 0 | 0 |
| UX | 7 | 2 | 2 | 3 | 0 | 0 |
| NFR | 8 | 3 | 3 | 2 | 0 | 0 |
| **TOTAL** | **91** | **54** | **27** | **10** | **11** | **0** |

---

## 12. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-31 | Antigravity | Initial matrix creation |
| 1.1 | 2026-01-31 | Antigravity | Added PDF-012 to PDF-015, DB-009 to DB-011, updated SYS-004 |
| 1.2 | 2026-02-01 | Antigravity | Added Part Builder section (PB-001 to PB-012), 11/12 complete |
