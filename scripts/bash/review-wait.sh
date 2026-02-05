#!/usr/bin/env bash
# Usage: ./review-wait.sh [--timeout=600]
set -euo pipefail

INITIAL_DELAY=10
POLL_INTERVAL=15
DEFAULT_TIMEOUT=600
RUNNING_STATES=(pending in_progress queued waiting requested)

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

get_coderabbit_check() {
    local pr_number="$1"
    local checks_json
    checks_json=$(gh pr checks "$pr_number" --json name,state 2>&1) || die "Failed to fetch PR checks: $checks_json"
    echo "$checks_json" | jq -r '.[] | select(.name | ascii_downcase | contains("coderabbit"))' 2>/dev/null
}

is_running_state() {
    local state="${1,,}"
    local s
    for s in "${RUNNING_STATES[@]}"; do
        [[ "$state" == "$s" ]] && return 0
    done
    return 1
}

parse_args() {
    TIMEOUT=$DEFAULT_TIMEOUT
    local arg value
    for arg in "$@"; do
        if [[ "$arg" == --timeout=* ]]; then
            value="${arg#--timeout=}"
            if [[ "$value" =~ ^[0-9]+$ ]] && [[ "$value" -gt 0 ]]; then
                TIMEOUT="$value"
            else
                echo "Invalid timeout value, using default" >&2
            fi
        fi
    done
}

main() {
    parse_args "$@"
    check_dependencies

    local pr_number check state start_time current_time elapsed
    pr_number=$(get_pr_number)

    echo "Waiting ${INITIAL_DELAY}s for CI to start..."
    sleep "$INITIAL_DELAY"

    check=$(get_coderabbit_check "$pr_number")
    state=$(echo "$check" | jq -r '.state // ""')

    if [[ -z "$check" ]] || ! is_running_state "$state"; then
        echo "No CodeRabbit CI in progress"
        exit 0
    fi

    echo "Waiting for CodeRabbit CI on PR #${pr_number}..."
    start_time=$(date +%s)

    while true; do
        current_time=$(date +%s)
        elapsed=$((current_time - start_time))

        if [[ $elapsed -ge $TIMEOUT ]]; then
            echo ""
            echo "Timeout after ${TIMEOUT}s"
            exit 1
        fi

        check=$(get_coderabbit_check "$pr_number")
        state=$(echo "$check" | jq -r '.state // ""')

        if [[ -z "$check" ]] || ! is_running_state "$state"; then
            echo ""
            echo "CodeRabbit CI completed${state:+ ($state)}"
            exit 0
        fi

        printf "."
        sleep "$POLL_INTERVAL"
    done
}

main "$@"
