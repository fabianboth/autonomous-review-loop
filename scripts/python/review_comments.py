#!/usr/bin/env python3
# ruff: noqa: T201, S603, S607
"""Fetch unresolved PR review comments from CodeRabbit and save to .reviews/prComments.md."""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

GRAPHQL_QUERY = """query($owner: String!, $repo: String!, $pr: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr) {
      reviews(first: 50) {
        nodes {
          id
          databaseId
          author { login }
          body
          reactions(first: 10) {
            nodes { user { login } content }
          }
        }
      }
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          comments(first: 1) {
            nodes { author { login } path line body }
          }
        }
      }
    }
  }
}""".replace("\n", " ")


def strip_html_comments(body: str) -> str:
    return re.sub(r"<!--[\s\S]*?-->", "", body).strip()


def run_graphql(query: str, variables: dict[str, str | int]) -> dict[str, Any]:
    args = ["gh", "api", "graphql"]
    for key, value in variables.items():
        args.extend(["-F", f"{key}={value}"])
    args.extend(["-f", f"query={query}"])

    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or "GraphQL query failed")
    return json.loads(result.stdout)


def get_current_user() -> str:
    result = subprocess.run(
        ["gh", "api", "user", "-q", ".login"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return result.stdout.strip()


def get_repo_info() -> dict[str, Any]:
    result = subprocess.run(
        ["gh", "repo", "view", "--json", "owner,name"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return json.loads(result.stdout)


def get_pr_number() -> int:
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
    try:
        return int(pr_number)
    except ValueError as exc:
        raise RuntimeError(f"Invalid PR number: {pr_number}") from exc


def has_user_reacted(review: dict[str, Any], username: str) -> bool:
    return any(
        r.get("user", {}).get("login") == username and r.get("content") == "THUMBS_UP"
        for r in review.get("reactions", {}).get("nodes", [])
    )


def main() -> None:
    repo_info = get_repo_info()
    pr_number = get_pr_number()
    current_user = get_current_user()

    result = run_graphql(
        GRAPHQL_QUERY,
        {
            "owner": repo_info["owner"]["login"],
            "repo": repo_info["name"],
            "pr": pr_number,
        },
    )

    pr_data = result["data"]["repository"]["pullRequest"]

    coderabbit_reviews = [
        r for r in pr_data["reviews"]["nodes"] if r.get("author", {}).get("login") == "coderabbitai" and r.get("body")
    ]

    unreacted_reviews = [r for r in coderabbit_reviews if not has_user_reacted(r, current_user)]

    unresolved_threads = [
        t for t in pr_data["reviewThreads"]["nodes"] if not t["isResolved"] and t["comments"]["nodes"]
    ]

    review_bodies = [
        {"id": r["id"], "body": strip_html_comments(r["body"])}
        for r in unreacted_reviews
        if strip_html_comments(r["body"])
    ]

    has_content = len(unresolved_threads) > 0 or len(review_bodies) > 0

    reviews_dir = Path(".reviews")
    reviews_dir.mkdir(exist_ok=True)

    if not has_content:
        content = f"# Review Comments\n\n**PR:** #{pr_number}\n\nNo unresolved comments.\n"
        (reviews_dir / "prComments.md").write_text(content, encoding="utf-8")
        print("No unresolved comments found on this PR")
        return

    resolve_cmd = (
        'gh api graphql -f query=\'mutation { resolveReviewThread(input: {threadId: "THREAD_ID"}) '
        "{ thread { isResolved } } }'"
    )
    react_cmd = (
        'gh api graphql -f query=\'mutation { addReaction(input: {subjectId: "REVIEW_ID", '
        "content: THUMBS_UP}) { reaction { content } } }'"
    )

    output = f"""# Review Comments

**PR:** #{pr_number}
**Inline threads (unresolved):** {len(unresolved_threads)}
**Review comments (unreacted):** {len(review_bodies)}

To resolve an inline thread after addressing it:
```bash
{resolve_cmd}
```

To mark a review as addressed (adds reaction):
```bash
{react_cmd}
```

"""

    if unresolved_threads:
        output += "---\n\n# Inline Comments (Unresolved)\n\n"
        thread_parts = []
        for t in unresolved_threads:
            comment = t["comments"]["nodes"][0]
            location = f"{comment['path']}:{comment.get('line', '?')}"
            author = comment.get("author", {}).get("login", "unknown")
            thread_parts.append(
                f"## {location}\n\n**Thread ID:** `{t['id']}`\n**Author:** {author}\n\n{comment['body']}"
            )
        output += "\n\n---\n\n".join(thread_parts)

    if review_bodies:
        output += f"\n\n---\n\n# Review Comments ({len(review_bodies)})\n\n"
        review_parts = [f"**Review ID:** `{r['id']}`\n\n{r['body']}" for r in review_bodies]
        output += "\n\n---\n\n".join(review_parts)

    (reviews_dir / "prComments.md").write_text(output, encoding="utf-8")
    print("Saved review comments to .reviews/prComments.md:")
    print(f"  - {len(unresolved_threads)} unresolved inline threads")
    print(f"  - {len(review_bodies)} review comments")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
