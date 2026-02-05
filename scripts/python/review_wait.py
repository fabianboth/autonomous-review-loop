#!/usr/bin/env python3
"""
Wait for the CodeRabbit CI action to complete on the current PR.
If no CI is running, exits immediately.

Usage: python scripts/review_wait.py [--timeout=600]
"""

import json
import subprocess
import sys
import time
from typing import Any

INITIAL_DELAY = 10  # seconds - wait for CI to start after push
POLL_INTERVAL = 15  # seconds
DEFAULT_TIMEOUT = 600  # seconds (10 minutes)
RUNNING_STATES = {"pending", "in_progress", "queued", "waiting", "requested"}


def get_pr_number() -> str:
    result = subprocess.run(
        ["gh", "pr", "view", "--json", "number", "-q", ".number"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    pr_number = result.stdout.strip()
    if not pr_number:
        raise RuntimeError("No PR found for current branch")
    return pr_number


def get_coderabbit_check(pr_number: str) -> dict[str, Any] | None:
    result = subprocess.run(
        ["gh", "pr", "checks", pr_number, "--json", "name,state"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    if result.returncode != 0:
        err = (result.stderr or "").strip()
        raise RuntimeError(f"Failed to fetch PR checks: {err or 'unknown error'}")

    try:
        checks = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse PR checks JSON output: {result.stdout!r}") from exc
    else:
        for check in checks:
            if "coderabbit" in check.get("name", "").lower():
                return check
        return None


def parse_args() -> dict[str, int]:
    timeout = DEFAULT_TIMEOUT

    for arg in sys.argv[1:]:
        if arg.startswith("--timeout="):
            try:
                parsed = int(arg.split("=")[1])
                if parsed > 0:
                    timeout = parsed
                else:
                    print("Invalid timeout value, using default", file=sys.stderr)
            except ValueError:
                print("Invalid timeout value, using default", file=sys.stderr)

    return {"timeout": timeout}


def main() -> None:
    args = parse_args()
    timeout = args["timeout"]
    start_time = time.time()
    pr_number = get_pr_number()

    print(f"Waiting {INITIAL_DELAY}s for CI to start...")
    time.sleep(INITIAL_DELAY)

    initial_check = get_coderabbit_check(pr_number)
    initial_state = (initial_check.get("state", "") if initial_check else "").lower()

    if not initial_check or initial_state not in RUNNING_STATES:
        print("No CodeRabbit CI in progress")
        sys.exit(0)

    print(f"Waiting for CodeRabbit CI on PR #{pr_number}...")

    while time.time() - start_time < timeout:
        check = get_coderabbit_check(pr_number)
        state = (check.get("state", "") if check else "").lower()

        if not check or state not in RUNNING_STATES:
            state_msg = f" ({check['state']})" if check else ""
            print(f"\nCodeRabbit CI completed{state_msg}")
            sys.exit(0)

        print(".", end="", flush=True)
        time.sleep(POLL_INTERVAL)

    print(f"\nTimeout after {timeout}s")
    sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
