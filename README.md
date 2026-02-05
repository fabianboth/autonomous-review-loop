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

## Quick Start

### Prerequisites

- [GitHub CLI](https://cli.github.com/) (`gh`) - Authenticated with your account
- [jq](https://jqlang.org/) - JSON processor

### Installation

```bash
git clone https://github.com/fabianboth/autonomous-review-loop.git
cd autonomous-review-loop
```

### Usage

From your project directory with an open PR, prompt your coding agent:

```
Please conduct the review loop as described in scripts/bash/reviewPrompt.txt
```

The agent will autonomously:
1. Wait for CI to complete
2. Fetch and analyze review comments
3. Fix valid issues, ask you about ambiguous ones
4. Resolve threads and push
5. Repeat until no comments remain

## Status

Currently in active development.
