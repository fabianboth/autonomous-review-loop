# Autonomous Review Loop

![Autonomous Review Loop](assets/review_loop.webp)

A workflow tool that automates the review-fix-push cycle by delegating to your coding agent.

## Why

When you create a PR, code review (human or automated) generates comments you need to triage: reading each one, deciding what to fix vs. reject, discussing with your coding agent, then resolving threads one by one. The whole cycle is tedious and distracting.

The solution: delegate the entire review loop to your coding agent. It waits for CI to complete, fetches all comments, decides which are valid, fixes the issues, resolves threads, pushes, and repeats until clean. You only get pulled in when there's an actual decision that needs human judgment.

## Features

- **Batched decision-making** - Get aggregate review requests instead of triaging individual comments one by one
- **Parallel work** - Continue other tasks while the review loop runs autonomously in the background
- **Multi-pass resolution** - Iterates automatically until no unresolved comments remain
- **Agent-agnostic** - Works with any coding agent (Claude Code, Cursor, etc.) and any review tool

## Prerequisites

- [Claude Code](https://claude.com/code) - Anthropic's CLI for Claude
- [GitHub CLI](https://cli.github.com/) (`gh`) - Authenticated with your account
- [jq](https://jqlang.org/) - JSON processor

## Installation

```bash
uv tool install reviewloop
```

Then initialize in your project:

```bash
reviewloop init
```

## Usage

### With Claude Code Skill

From your project directory with an open PR, invoke the skill:

```text
/reviewloop
```

The agent will autonomously:
1. Wait for CI to complete
2. Fetch and analyze review comments
3. Fix valid issues, ask you about ambiguous ones
4. Resolve threads and push
5. Repeat until no comments remain

### With Standalone Scripts

If you initialized with `--mode script`, prompt your coding agent with the contents of `scripts/reviewloop/reviewPrompt.txt`.

## Troubleshooting

### "No PR found for current branch"

Ensure you're on a branch with an open PR:

```bash
gh pr view
```

### "gh CLI is not authenticated"

Run:

```bash
gh auth login
```

### Skill not appearing in Claude Code

1. Check the skill file exists: `.claude/skills/reviewloop/SKILL.md`
2. Verify the frontmatter is valid YAML
3. Restart Claude Code

### CI timeout

The default timeout is 10 minutes. If your CI takes longer, the script will inform you and you can re-run with a longer timeout:

```bash
scripts/reviewloop/review-wait.sh --timeout=1200
```

## Status

Currently in active development.
