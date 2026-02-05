#!/usr/bin/env bash
set -euo pipefail

GRAPHQL_QUERY='query($owner: String!, $repo: String!, $pr: Int!) { repository(owner: $owner, name: $repo) { pullRequest(number: $pr) { reviews(first: 50) { nodes { id databaseId author { login } body reactions(first: 10) { nodes { user { login } content } } } } reviewThreads(first: 100) { nodes { id isResolved comments(first: 1) { nodes { author { login } path line body } } } } } } }'

die() {
    echo "Error: $1" >&2
    exit "${2:-1}"
}

check_dependencies() {
    command -v gh &>/dev/null || die "gh CLI is not installed. Install from https://cli.github.com/"
    command -v jq &>/dev/null || die "jq is not installed. Install from https://stedolan.github.io/jq/download/"
    gh auth status &>/dev/null || die "gh CLI is not authenticated. Run 'gh auth login' first."
}

get_pr_number() {
    local pr_number
    pr_number=$(gh pr view --json number -q '.number' 2>/dev/null) || die "No PR found for current branch"
    [[ -n "$pr_number" ]] || die "No PR found for current branch"
    echo "$pr_number"
}

get_repo_info() {
    local repo_json
    repo_json=$(gh repo view --json owner,name 2>&1) || die "Failed to get repository info: $repo_json"
    echo "$repo_json"
}

get_current_user() {
    local user
    user=$(gh api user -q '.login' 2>&1) || die "Failed to get current user: $user"
    echo "$user"
}

run_graphql() {
    local owner="$1" repo="$2" pr="$3"
    local result
    result=$(gh api graphql -F "owner=$owner" -F "repo=$repo" -F "pr=$pr" -f "query=$GRAPHQL_QUERY" 2>&1) || die "GraphQL query failed: $result"
    echo "$result"
}

main() {
    check_dependencies

    local repo_info owner repo pr_number current_user
    repo_info=$(get_repo_info)
    owner=$(echo "$repo_info" | jq -r '.owner.login')
    repo=$(echo "$repo_info" | jq -r '.name')
    pr_number=$(get_pr_number)
    current_user=$(get_current_user)

    local result pr_data
    result=$(run_graphql "$owner" "$repo" "$pr_number")
    pr_data=$(echo "$result" | jq '.data.repository.pullRequest')

    local coderabbit_reviews unreacted_reviews unresolved_threads review_bodies
    coderabbit_reviews=$(echo "$pr_data" | jq '[.reviews.nodes[] | select(.author.login == "coderabbitai" and .body != null and .body != "")]')

    unreacted_reviews=$(echo "$coderabbit_reviews" | jq --arg user "$current_user" '[
        .[] | select(
            ([.reactions.nodes[] | select(.user.login == $user and .content == "THUMBS_UP")] | length) == 0
        )
    ]')

    unresolved_threads=$(echo "$pr_data" | jq '[.reviewThreads.nodes[] | select(.isResolved == false and (.comments.nodes | length) > 0)]')

    # Strip HTML comments from review bodies
    review_bodies=$(echo "$unreacted_reviews" | jq '[.[] | {id: .id, body: .body}]')
    review_bodies=$(echo "$review_bodies" | jq '[
        .[] |
        .body |= (gsub("<!--[^>]*-->"; "") | gsub("^\\s+|\\s+$"; "")) |
        select(.body != "")
    ]')

    local thread_count review_count
    thread_count=$(echo "$unresolved_threads" | jq 'length')
    review_count=$(echo "$review_bodies" | jq 'length')

    mkdir -p .reviews

    if [[ "$thread_count" -eq 0 ]] && [[ "$review_count" -eq 0 ]]; then
        cat > .reviews/prComments.md << EOF
# Review Comments

**PR:** #${pr_number}

No unresolved comments.
EOF
        echo "No unresolved comments found on this PR"
        exit 0
    fi

    local resolve_cmd='gh api graphql -f query='\''mutation { resolveReviewThread(input: {threadId: "THREAD_ID"}) { thread { isResolved } } }'\'''
    local react_cmd='gh api graphql -f query='\''mutation { addReaction(input: {subjectId: "REVIEW_ID", content: THUMBS_UP}) { reaction { content } } }'\'''

    {
        echo "# Review Comments"
        echo ""
        echo "**PR:** #${pr_number}"
        echo "**Inline threads (unresolved):** ${thread_count}"
        echo "**Review comments (unreacted):** ${review_count}"
        echo ""
        echo "To resolve an inline thread after addressing it:"
        echo '```bash'
        echo "$resolve_cmd"
        echo '```'
        echo ""
        echo "To mark a review as addressed (adds reaction):"
        echo '```bash'
        echo "$react_cmd"
        echo '```'
        echo ""

        if [[ "$thread_count" -gt 0 ]]; then
            echo "---"
            echo ""
            echo "# Inline Comments (Unresolved)"
            echo ""

            local i=0
            while [[ $i -lt $thread_count ]]; do
                local thread thread_id comment path line author body
                thread=$(echo "$unresolved_threads" | jq ".[$i]")
                thread_id=$(echo "$thread" | jq -r '.id')
                comment=$(echo "$thread" | jq '.comments.nodes[0]')
                path=$(echo "$comment" | jq -r '.path // "unknown"')
                line=$(echo "$comment" | jq -r '.line // "?"')
                author=$(echo "$comment" | jq -r '.author.login // "unknown"')
                body=$(echo "$comment" | jq -r '.body // ""')

                [[ $i -gt 0 ]] && { echo ""; echo "---"; echo ""; }

                echo "## ${path}:${line}"
                echo ""
                echo "**Thread ID:** \`${thread_id}\`"
                echo "**Author:** ${author}"
                echo ""
                echo "$body"

                ((i++))
            done
        fi

        if [[ "$review_count" -gt 0 ]]; then
            echo ""
            echo "---"
            echo ""
            echo "# Review Comments (${review_count})"
            echo ""

            local i=0
            while [[ $i -lt $review_count ]]; do
                local review review_id body
                review=$(echo "$review_bodies" | jq ".[$i]")
                review_id=$(echo "$review" | jq -r '.id')
                body=$(echo "$review" | jq -r '.body // ""')

                [[ $i -gt 0 ]] && { echo ""; echo "---"; echo ""; }

                echo "**Review ID:** \`${review_id}\`"
                echo ""
                echo "$body"

                ((i++))
            done
        fi
    } > .reviews/prComments.md

    echo "Saved review comments to .reviews/prComments.md:"
    echo "  - ${thread_count} unresolved inline threads"
    echo "  - ${review_count} review comments"
}

main "$@"
