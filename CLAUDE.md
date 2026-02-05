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
│   ├── python/           # Python implementation (primary)
│   │   ├── review_wait.py
│   │   ├── review_comments.py
│   │   └── reviewPrompt.txt
│   └── typescript/       # TypeScript implementation (reference)
│       ├── review-wait.mjs
│       ├── review-comments.mjs
│       └── reviewPrompt.txt
└── specs/                # Feature specifications
```

## Tech Stack

- **Python**: 3.13+ with uv for dependency management
- **Type Checking**: pyright (strict mode)
- **Linting/Formatting**: ruff (ALL rules with sensible ignores)
- **TypeScript**: Node.js scripts (.mjs) - retained for reference

## Commands

```bash
uv sync

# Run scripts
uv run review-wait       # Wait for CodeRabbit CI
uv run review-comments   # Fetch PR comments

# Linting (auto-fixes enabled via pyproject.toml)
uv run ruff check
uv run ruff format

# Type checking (strict mode)
uv run pyright
```

## Code Style

- Python 3.13+, line length 120, double quotes
- Self-explaining modular code: We strive for self explaining, comment free code without docstrings (only comments in rare exceptions)
- Strict type hints (pyright strict mode) - all methods must be typed
- Prefer kwargs when calling methods for clarity
- Use dataclasses for structured data
- Never suppress type/lint errors - fix them (rare exceptions only)
- Avoid creating barrel exports via init files, always directly import instead

## Change Verification

Always used to verify code changes:

- Format code with `uv run ruff format`
- Verify changes with `uv run ruff check`
- Verify type checking with `uv run pyright`
