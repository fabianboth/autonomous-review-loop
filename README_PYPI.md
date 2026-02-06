# Autonomous Review Loop

![Autonomous Review Loop](https://raw.githubusercontent.com/fabianboth/autonomous-review-loop/main/assets/review_loop.webp)

Pair your review bot ([CodeRabbit](https://www.coderabbit.ai/), [Cursor BugBot](https://cursor.com/bugbot), etc.) with your coding agent. reviewloop delegates the entire review-fix-push cycle: it fetches comments, fixes issues, resolves threads, pushes, and repeats. You only step in when human judgment is needed.

## Installation

```bash
uv tool install reviewloop
```

```bash
reviewloop init
```

## Getting Started

### Claude Code

Select **Claude Code** during `reviewloop init`. Then run this within your claude code session:

```text
/reviewloop
```

### Any Coding Agent

Select **Script based** during `reviewloop init`. This creates standalone scripts and a prompt file at `scripts/reviewloop/reviewPrompt.txt`. Feed it to any coding agent (Cursor, Windsurf, etc.) with `@scripts/reviewloop/reviewPrompt.txt` to start the loop.

## How It Works

1. Waits for CI to complete
2. Fetches inline comments and review comments
3. Fixes valid issues, asks you about ambiguous ones
4. Resolves threads and pushes
5. Repeats until no unresolved comments remain

## Features

- **Batched decision-making:** Aggregate review requests instead of triaging comments one by one.
- **Parallel work:** Continue other tasks while the loop runs in the background.
- **Multi-pass resolution:** Iterates automatically until clean.
- **Agent-agnostic:** Works with Claude Code, Cursor, Windsurf, or any coding agent.

## Documentation

For full documentation, troubleshooting, and advanced usage, visit the [GitHub repository](https://github.com/fabianboth/autonomous-review-loop).
