---
description: Update compliance matrix with what was built (run every ~5 prompts)
---

# Update Compliance Matrix Workflow

This workflow should be run approximately every 5 prompts during development to keep the compliance matrix synchronized with actual implementation status.

## Status Legend

| Symbol | Meaning |
|--------|---------|
| ⬜ | Not started |
| 🔄 | In progress |
| ✅ | Complete |
| ❌ | Blocked / Issue |
| ⏸️ | Paused / Deferred |

## Steps

1. **Review recent changes**
   - Check task.md for completed items
   - Review any new files or features implemented

2. **Open Compliance Matrix**
   - File: `docs/COMPLIANCE_MATRIX.md`

3. **Update requirement statuses**
   - Find requirements that match completed work
   - Update Status column: `⬜` → `🔄` → `✅`
   - Update Implementation column with file paths
   - Update Verification column with test method used

4. **Update Summary Statistics**
   - Scroll to "Summary Statistics" section
   - Update Complete/In Progress counts for each category
   - Update TOTAL row

5. **Add Scope Change if applicable**
   - If new requirements were added, log in "Scope Changes Log"
   - Format: `| SC-XXX | YYYY-MM-DD | Description | +N reqs | ✅ | User |`

6. **Update Revision History**
   - Add new version entry
   - Format: `| 1.X | YYYY-MM-DD | Antigravity | Brief description |`

## Quick Reference: Current Categories

| Prefix | Category |
|--------|----------|
| SYS | System Architecture |
| PDF | PDF Processing |
| DB | Database |
| UI | User Interface |
| CFG | Configurator |
| PB | Part Builder |
| DIST | Distributor Integration |
| UX | User Experience |
| NFR | Non-Functional Requirements |

## Example Update

```markdown
| PB-005 | Gray-out unavailable options | P1 | ✅ | `pages/PartBuilder.jsx` | Visual inspection | Mouser/DigiKey style |
```

---

> **Tip**: Run `/update-compliance` after completing a major feature or every ~5 prompts to keep documentation in sync.
