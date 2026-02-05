# Autonomous Review Loop

A workflow tool that automates the review-fix-push cycle by delegating to your coding agent.

## Why

When you create a PR, a code review agent like CodeRabbit runs in CI. You end up spending time manually triaging review comments: reading each one, copying relevant bits, deciding what to fix vs. reject, discussing with your coding agent, then resolving threads one by one. The whole cycle is tedious and distracting.

The solution: delegate the entire review loop to your coding agent. It waits for the review to complete, fetches all comments, decides which are valid, fixes the issues, resolves threads, pushes, and repeats until clean. You only get pulled in when there's an actual decision that needs human judgment.

## Features

- **Batched decision-making** - Get aggregate review requests instead of triaging individual comments one by one
- **Parallel work** - Continue other tasks while the review loop runs autonomously in the background
- **Multi-pass resolution** - Iterates automatically until no unresolved comments remain
- **Agent-agnostic** - Works with any coding agent (Claude Code, Cursor, etc.) and any review agent (CodeRabbit, etc.)

## Status

Currently in active development.
