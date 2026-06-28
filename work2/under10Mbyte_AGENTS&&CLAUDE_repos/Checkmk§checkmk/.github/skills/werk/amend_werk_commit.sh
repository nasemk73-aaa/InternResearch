#!/bin/bash
# Usage: amend_werk_commit.sh <jira_key1> [<jira_key2> ...]
# Amends the last commit (created by 'werk new') to the standard werk format
# with Jira issue key references.
#
# The Werk ID and title are derived from the existing commit subject, which
# 'werk new' formats as "XXXXX Title [with FIX/SEC prefix if applicable]".

set -e

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <jira_key1> [<jira_key2> ...]" >&2
    exit 1
fi

# Parse Werk ID and title from current commit subject ("XXXXX Title...")
CURRENT_SUBJECT=$(git log --format="%s" -1)
WERK_ID_PADDED="${CURRENT_SUBJECT%% *}"
WERK_ID=$((10#${WERK_ID_PADDED})) # strip leading zeros
WERK_TITLE="${CURRENT_SUBJECT#* }"

# Build commit message body: blank line + one Jira key per line
JIRA_BLOCK=$'\n'
for key in "$@"; do
    JIRA_BLOCK="${JIRA_BLOCK}
${key}"
done

git commit --amend -m "Add Werk #${WERK_ID}: ${WERK_TITLE}${JIRA_BLOCK}"
