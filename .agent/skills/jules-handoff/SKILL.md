---
name: Jules Handoff Generator
description: Auto-generates a context snapshot (JULES_PROMPT.md) for handing off work to a smaller model (Jules).
---

# Jules Handoff Skill

This skill allows you to "package" the current state of development into a single, concise markdown file (`JULES_PROMPT.md`). 
This is useful when switching agents or when you want to minimize token usage for the next step.

## How it works
The skill runs a Python script that:
1.  Locates the active "Brain" directory (where artifacts live).
2.  Reads the latest `task.md` and `implementation_plan.md`.
3.  Scans the project directory to build a file tree.
4.  Combines these into a standardized prompt format.

## Usage

**Option 1: Workflow (Recommended)**
Run the workflow:
```bash
/handoff-to-jules
```

**Option 2: Manual Trigger**
You can manually run the script if needed:
```bash
python .agent/skills/jules-handoff/generate_handoff.py
```

## Output
The script creates/overwrites: `[RepoRoot]/JULES_PROMPT.md`
