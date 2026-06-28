---
name: create-pr
description: Creates a GitHub Pull Request for RunCat365 following the project's PR template. Use this skill whenever the user wants to open, submit, or create a PR, pull request, or wants to propose changes to the main branch.
---

# Create a Pull Request for RunCat365

Follow these steps to create a PR that conforms to the `.github/pull_request_template.md`.

## Step 1: Gather branch information

Run these commands in parallel to understand the changes:

```bash
git log main..HEAD --oneline
git diff main..HEAD --stat
git diff main..HEAD
```

Also check the current branch name:

```bash
git branch --show-current
```

## Step 2: Determine the PR type

Based on the diff, classify the change as exactly one of:

| Type            | When to use                                                      |
| --------------- | ---------------------------------------------------------------- |
| **Bug Fix**     | Corrects incorrect behavior without adding new functionality     |
| **Refactoring** | Improves code structure or readability without changing behavior |
| **New Feature** | Adds new user-visible functionality                              |
| **Others**      | Documentation, CI changes, build config, etc.                    |

If unsure, ask the user before proceeding.

## Step 3: Draft the PR body

**IMPORTANT: The entire PR body must be written in English, regardless of the language the user is communicating in.**

Fill in the template below. Every section must be present — do not omit any.

```markdown
## Context of Contribution

- [x] Bug Fix ← check only the one that applies
- [ ] Refactoring
- [ ] New Feature
- [ ] Others

## Summary of the Proposal

<concise summary of what this PR proposes — 1–3 sentences>

## Reason for the new feature

<If Bug Fix / Refactoring / Others: write "N/A">
<If New Feature: explain why the feature is necessary, how many users it benefits,
and why benefits outweigh maintenance cost>

## Checklist

- [x] This PR does not contain commits of multiple contexts.
- [x] Code follows proper indentation and naming conventions.
- [x] Implemented using only APIs that can be submitted to the Microsoft Store.
- [x] Works correctly in both dark theme and light theme.
- [x] Works correctly on any device.
```

**Checklist rules:**

- All checklist items default to `[x]` (checked).
- If you have reason to believe an item may **not** hold (e.g., the change is UI-only so dark/light theme was not verifiable), leave it as `[ ]` and note the concern in the Summary.
- The "multiple contexts" item is `[x]` only if all commits on this branch belong to a single topic. If they don't, warn the user before creating the PR.

## Step 4: Generate a concise PR title

- Under 70 characters
- Imperative form, e.g. "Add French localization" or "Fix CPU usage spike on wake"
- Do not prefix with a tag like `feat:` or `fix:` — this repo does not use Conventional Commits

## Step 5: Confirm with the user

Show the user:

- The proposed **title**
- The full **body** (rendered as markdown if possible)

Ask: "Does this look right? Any changes before I create the PR?"

Make requested edits, then proceed only after the user confirms.

## Step 6: Create the PR

```bash
gh pr create \
  --title "<title>" \
  --body "$(cat <<'EOF'
<body>
EOF
)" \
  --base main
```

Return the PR URL to the user.

## Notes

- Always target `main` as the base branch unless the user specifies otherwise.
- Do not push the branch yourself — assume it is already pushed. If `gh pr create` fails because the branch has no upstream, run `git push -u origin HEAD` first and inform the user.
- If the branch already has an open PR, use `gh pr edit` to update it instead of creating a duplicate.
