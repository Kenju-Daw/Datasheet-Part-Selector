# 🐙 GitHub Cheat Sheet for "Datasheet Part Selector"

This guide explains the Git/GitHub terms and workflow we use.

## 📚 Key Terms

| Term | Definition | Analogy |
|------|------------|---------|
| **Repo (Repository)** | The folder containing all your project files and their history. | The entire "File Cabinet". |
| **Commit** | A save point. It has a unique ID (hash) and a message. | "Save Game" after passing a level. |
| **Push** | Uploading your local commits to the cloud (GitHub). | Uploading your save file to the cloud. |
| **Pull** | Downloading new changes from the cloud to your computer. | Downloading the latest DLC. |
| **Branch** | A parallel version of the code. Allows you to work without breaking the main code. | A parallel reality / Multiverse. |
| **PR (Pull Request)** | A request to merge your branch's changes into the main code. It allows for review. | "Hey boss, check my work before we publish it." |
| **Merge** | Combining the changes from a PR into the main branch. | Officially accepting the work. |

---

## 🚀 Workflow

### 1. How we (Antigravity & Jules) publish
We usually work directly on the `main` branch or a `wip` (Work In Progress) branch.
When you say "Antigravity, upload this", I run:

```bash
git add .                  # Stage all changes
git commit -m "Message"    # Save the snapshot
git push origin main       # Upload to GitHub
```

### 2. How to manage "PRs" (Pull Requests)
If you are working with a team (or just me and Jules), the "Proper" way is:

1.  **Create a Branch**:
    ```bash
    git checkout -b feature/new-button
    ```
2.  **Make Changes**: (The agent writes code)
3.  **Push Branch**:
    ```bash
    git push -u origin feature/new-button
    ```
4.  **Open PR on GitHub**: Go to the website. You'll see "Compare & Pull Request". Click it.
5.  **Merge**: Once approved, click "Squash and Merge".

---

## ❓ "Is `agents.md` enough?"
**No.** `agents.md` tells you *WHO* does the work and *WHAT* their roles are.
But it does not explain *HOW* to move the code around (which is what this file does).

**Recommendation**:
- Use `agents.md` to know **who to ask**.
- Use `GIT_CHEAT_SHEET.md` to know **how to save/share**.
