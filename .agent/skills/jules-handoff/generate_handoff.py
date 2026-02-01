import os
import datetime

# Configuration
OUTPUT_FILE = "JULES_PROMPT.md"
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
BRAIN_DIR = os.path.join(ROOT_DIR, ".gemini/antigravity/brain") 
# Note: In this environment, brain dir might be different. 
# We will try to find the active brain dir or just look for Artifacts in known locations if possible.
# Given the environment, artifacts are at C:\Users\kjara\.gemini\antigravity\brain\<uuid>\
# But the script needs to run from the repo root or find the repo root.

def find_latest_brain_dir():
    """Attempts to find the latest brain directory."""
    base_brain = os.path.expanduser("~/.gemini/antigravity/brain")
    if not os.path.exists(base_brain):
        return None
    
    # Get all subdirs
    dirs = [os.path.join(base_brain, d) for d in os.listdir(base_brain) if os.path.isdir(os.path.join(base_brain, d))]
    if not dirs:
        return None
    
    # Sort by modification time (latest first)
    dirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return dirs[0] # Return the most recent conversation

def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"[Error reading {path}: {e}]"

def generate_tree(startpath, max_depth=2):
    """Generates a simple tree structure."""
    tree_str = ""
    startpath = os.path.normpath(startpath)
    separator = os.path.sep
    
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        if level > max_depth:
            continue
        
        indent = ' ' * 4 * (level)
        tree_str += '{}{}/\n'.format(indent, os.path.basename(root))
        subindent = ' ' * 4 * (level + 1)
        
        # Filter files/dirs
        ignore_dirs = {'.git', 'venv', 'node_modules', '__pycache__', '.gemini', '.agent'}
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        
        for f in files:
            if f.endswith(('.py', '.js', '.jsx', '.json', '.md', '.html', '.css')):
                tree_str += '{}{}\n'.format(subindent, f)
                
    return tree_str

def main():
    print(f"Generating {OUTPUT_FILE}...")
    
    brain_dir = find_latest_brain_dir()
    if not brain_dir:
        print("Warning: Could not locate active Brain directory. Artifacts might be missing.")
        # Fallback to checking specific known locations if needed or just skip
        task_md_path = "task.md" # Valid if running in brain dir, which we likely aren't
    
    # Paths to critical files
    # We assume this script is run from the project root or we can derive it.
    # Current script loc: .agent/skills/jules-handoff/generate_handoff.py
    # So Root is ../../../
    
    project_root = ROOT_DIR
    
    # Artifact paths (Best effort)
    task_md = os.path.join(brain_dir, "task.md") if brain_dir else None
    impl_plan = os.path.join(brain_dir, "implementation_plan.md") if brain_dir else None
    
    # Read Content
    task_content = read_file(task_md) if task_md and os.path.exists(task_md) else "No task.md found."
    plan_content = read_file(impl_plan) if impl_plan and os.path.exists(impl_plan) else "No implementation_plan.md found."
    
    try:
        tree = generate_tree(project_root)
    except Exception as e:
        tree = f"Error generating tree: {e}"

    # Construct Prompt
    content = f"""<!-- JULES_PROMPT: Generated at {datetime.datetime.now().isoformat()} -->
<instruction>
You are an expert software engineer taking over a project. 
Your first goal is to understand the current state and the immediate next steps defined in the `task.md`.
Review the context below to orient yourself.
</instruction>

<workspace_context>
<project_structure>
{tree}
</project_structure>

<artifacts>
# Current Task Status (task.md)
{task_content}

# Implementation Plan
{plan_content}
</artifacts>
</workspace_context>

<mission_brief>
1. Review the unchecked items in `task.md`.
2. Continue execution from the last checked item.
3. If unsure, ask the user for clarification.

## Escalation Protocol
If you encounter:
- A logic error you cannot fix in 2 attempts
- Missing context that is not in the file tree
- A complex architectural decision

STOP. Do not guess. Tell the user: "I need to escalate this to Antigravity."
</mission_brief>
"""

    output_path = os.path.join(project_root, OUTPUT_FILE)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"✅ Handoff file created at: {output_path}")
    print(f"Size: {len(content)} bytes")

if __name__ == "__main__":
    main()
