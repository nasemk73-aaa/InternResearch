---
name: jira-read-ticket
description: Fetch and display a Jira ticket's description, comments, attachments, and linked tickets
---

# Read a Jira Ticket

Fetches a Jira ticket and displays its full context: description, comments, attachments, and linked tickets. User names are anonymized.

> **Note:** This skill is limited to the CMK project to avoid interfering with sensitive customer data. Only `CMK-` prefixed tickets are supported.

## Arguments

The user provides one or more Jira ticket keys as the argument (e.g., `/jira-read-ticket CMK-12345` or `/jira-read-ticket CMK-12345 CMK-67890`).

## Workflow

### 1. Fetch ticket context

For each ticket key provided, run the helper script:

```bash
.venv/bin/python .github/skills/jira-read-ticket/read_ticket.py <TICKET_KEY>
```

If the script fails, report the error to the user and continue with the remaining tickets.

If multiple tickets are requested, fetch them in parallel using separate Bash calls.

### 2. Review attachments

Skip this step entirely if the script output contains no attachment sections.

If there are attachments, launch **at most 2 Task agents** (subagent_type: `general-purpose`) in parallel:

- **Images agent** (only if there are image attachments): One agent receives ALL image file paths. It should read each image with the Read tool and describe what it shows (UI state, error messages, annotations, etc.). Return a concise summary per image.
- **Other files agent** (only if there are non-image attachments): One agent receives ALL other file paths. For text-based files (logs, configs, CSVs), read and summarize key findings. For archives (tar, zip, gz), extract via Bash and summarize structure. Return a concise summary per file.

### 3. Present the ticket

Present the ticket context to the user. Summarize the key information:

- What the ticket is about (type, status, priority)
- The core ask from the description
- Key takeaways from comments (decisions made, blockers, etc.)
- Notable linked tickets and their relevance
- Attachment summaries (if any)

Keep it concise — the user can ask follow-up questions if they need more detail.
