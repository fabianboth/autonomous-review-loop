# CLAUDE.md

Autonomous Review Loop - a workflow tool that automates the review-fix-push cycle by delegating to your coding agent.

## CRITICAL: File Editing on Windows

**When using Edit tools on Windows, you MUST use backslashes (`\`) in file paths, NOT forward slashes (`/`).**

## Project Structure

```
/
├── pyproject.toml        # Project configuration (uv, pyright, ruff)
├── uv.lock               # Dependency lock file
├── scripts/
│   └── bash/             # Review loop scripts
│       ├── review-wait.sh
│       ├── review-comments.sh
│       └── reviewPrompt.txt
└── specs/                # Feature specifications
```

## Tech Stack

- **Bash**: 4.0+ for review loop scripts
- **Python**: 3.13+ with uv (for project tooling)
- **Linting/Formatting**: ruff
- **Type Checking**: pyright (strict mode)

## Commands

```bash
uv run ruff check
uv run ruff format
uv run pyright
```

## Code Style

- Self-explaining modular code: comment-free where possible (only comments when genuinely helpful)
- Bash scripts use strict mode (`set -euo pipefail`)
- Python 3.13+, line length 120, double quotes
- Strict type hints (pyright strict mode) - all methods must be typed
- Never suppress type/lint errors - fix them  (rare exceptions only)
- Avoid creating barrel exports via init files, always directly import instead

## Change Verification

Always verify code changes:

- Format code with `uv run ruff format`
- Verify changes with `uv run ruff check`
- Verify type checking with `uv run pyright`
