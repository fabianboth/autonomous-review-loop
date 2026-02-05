# CLAUDE.md

Autonomous Review Loop - a workflow tool that automates the review-fix-push cycle by delegating to your coding agent.

## CRITICAL: File Editing on Windows

**When using Edit tools on Windows, you MUST use backslashes (`\`) in file paths, NOT forward slashes (`/`).**

## Project Structure

```
/
├── scripts/
│   ├── typescript/       # TypeScript implementation
│   │   ├── review-wait.mjs
│   │   ├── review-comments.mjs
│   │   └── reviewPrompt.txt
│   └── python/           # Python implementation
│       ├── review_wait.py
│       ├── review_comments.py
│       └── reviewPrompt.txt
└── specs/                # Feature specifications
```

## Tech Stack

- **TypeScript**: Node.js scripts (.mjs)
- **Python**: Python 3.x scripts
- **Linting/Formatting**: Biome (for .ts, .js, .json)

## Code Style

- TypeScript: ES modules, strict typing (no `any`)
- Python: Type hints encouraged
- Biome enforced: tabs, double quotes, semicolons
