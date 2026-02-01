# 🤖 Agent Registry

This document defines the agentic team working on the **Datasheet Part Selector** project.

## 🧠 Antigravity (Lead Architect)
**Role**: Senior Software Engineer & System Architect
**Primary Responsibilities**:
- **System Design**: Defining architecture, schemas, and data flows.
- **Complex Features**: Implementing core logic (e.g., Multi-Connector search, Semantic Search).
- **Deep Debugging**: Investigating 500 errors, race conditions, and heavy computation logic.
- **Verification**: Creating and running complex test suites (`verify_all_awg.ps1`).
- **Tooling**: Writing workflows and skills for other agents.

**When to use**: Use for high-complexity tasks, planning, and architectural decisions.

---

## ⚡ Jules (Junior Developer)
**Role**: Maintenance, Polish, & Optimization
**Primary Responsibilities**:
- **UI Polish**: Adding tooltips, fixing padding/margins, updating icons.
- **Linting & Formatting**: Running standard linters and fixing stylistic issues.
- **Documentation**: Updating minor README sections or fixing typos.
- **Simple Features**: Adding "Copy to Clipboard" buttons, minor form inputs.
- **Unit Tests**: Writing boilerplate test cases.

**Handoff Protocol**:
1. Check `task.md` for "Polish & Maintenance" items.
2. Run `/handoff-to-jules` to generate `JULES_PROMPT.md`.
3. Provide the file to Jules.
4. **Escalation**: If Jules gets stuck, bring the code back to Antigravity.

---

## 🛠️ Agent Workflows

### `/handoff-to-jules`
**Trigger**: User command or Phase completion.
**Action**: Generates `JULES_PROMPT.md` containing:
- Project File Tree
- Current `task.md` status
- `implementation_plan.md` context
- Escalation protocols

### `/verify-integrity` (Proposed)
**Trigger**: Before handing back to Antigravity.
**Action**: Runs build and test scripts to ensure Jules hasn't broken the build.
