# Autonomous Review Loop Constitution

## Core Principles

### I. Agent-Agnostic Design
The tool must work with any coding agent (Claude Code, Cursor, etc.) and any review agent (CodeRabbit, etc.). Avoid tight coupling to specific platforms.

### II. Dual Implementation Parity
Maintain feature parity between TypeScript and Python implementations. Both should behave identically and be equally well-maintained.

### III. Simplicity & Reliability
Keep scripts focused and reliable. The tool runs in CI/automation contexts where failures are costly. Prefer clear error messages over silent failures.

### IV. Minimal Dependencies
Keep dependencies minimal in both implementations. The tool should be easy to install and run without complex setup.

## Technology Standards

### Stack & Tools
- **TypeScript**: Node.js ES modules (.mjs)
- **Python**: Python 3.x with type hints
- **Linting/Formatting**: Biome (for JS/TS/JSON)

### Implementation Constraints
- TypeScript: Strict typing, no `any`
- Python: Type hints encouraged
- Both: Clear CLI interfaces, meaningful exit codes

## Development Workflow

### Code Style
- Biome enforced: tabs, double quotes, semicolons (TS/JS)
- Keep functions small and focused
- Prefer composition over complexity

### Verification
- Test both implementations when making changes
- Ensure scripts handle edge cases (no PR, no comments, API failures)

**Version**: 1.0.0 | **Ratified**: 2025-02-05
