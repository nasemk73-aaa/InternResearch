#!/bin/bash
# Usage: gather_commits.sh <jira_key1> [<jira_key2> ...]
# For each Jira key: find all related commits on the current branch and print
# their stats and diffs. Commits referenced by multiple keys are shown once.

set -e

if [ "$#" -eq 0 ]; then
    echo "Usage: $0 <jira_key1> [<jira_key2> ...]" >&2
    exit 1
fi

declare -A seen_by_sha

for key in "$@"; do
    mapfile -t shas < <(git log --format="%H" --grep="$key")

    if [ "${#shas[@]}" -eq 0 ]; then
        echo "=== $key: no commits found ==="
        echo ""
        continue
    fi

    echo "=== $key (${#shas[@]} commits) ==="

    for sha in "${shas[@]}"; do
        if [ -n "${seen_by_sha[$sha]}" ]; then
            continue
        fi
        seen_by_sha[$sha]=1

        echo ""
        git show "$sha" --stat -p
        echo ""
    done
done
