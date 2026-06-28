# Checkmk Werk Writing Style Guide

## Audience

System administrators and Checkmk users with technical knowledge. Assume your audience understands basic technical concepts and intermediate system administration topics.

## Tone and Language

### General Approach

- **Be clear and technically accurate** - precision matters
- **Keep it conversational** - you can address the reader directly ("you", "your")
- **Common speech is fine** - no need for overly formal language
- **A bit of personality is welcome** - werks can be slightly entertaining to read
- **Stay professional** - no insults, no inappropriate language, maintain political correctness
- **Active voice preferred** - "The system now supports X" beats "X is now supported"

### Examples of Good Tone

- ✅ "If you have BI aggregations with many rules, you'll notice faster page loads"
- ✅ "This was a tricky one - turns out the agent receiver had a race condition"
- ✅ "Good news: the dashboard no longer crashes when you edit large aggregations"

### Examples of Bad Tone

- ❌ "It has been observed that users with Business Intelligence rule sets exceeding..."
- ❌ "This is the worst bug we've ever seen and we're embarrassed by it"

## Structure

### Title

- Clear, action-oriented description (50-70 characters max)
- Start with action verb when possible
- Examples:
  - "Fixed crash when editing BI aggregations"
  - "Add support for Azure MySQL monitoring"
  - "Service discovery now respects disabled checks"

### Description

**Front-load the important stuff** - main impact first, details later

**Use headlines for larger Werks** - they help readers scan and find what matters to them.

Example structure:

```
## What changed
Brief description of the change

## Why this matters
User impact and benefits

## Technical background (optional)
Optional deeper technical details
```

## Content Guidelines

### What to include

- ✅ **User-visible changes** - what actually changes for users
- ✅ **The "why"** - why this change matters or what problem it solves
- ✅ **Usage instructions** - how to use new features
- ✅ **Migration steps** - what users need to do (for breaking changes)
- ✅ **Configuration changes** - new settings or changed defaults
- ✅ **Performance improvements** - if noticeable to users
- ✅ **Focus on practical impact** - what changes for the user's daily work?
- ✅ **Be specific** - "30% faster" beats "improved performance"
- ✅ **Examples help** - show concrete usage when introducing features

### What to Avoid

- ❌ **Repeating known facts** - don't explain what BI aggregations are if you're just fixing a bug in them
- ❌ **Obvious statements** - assume your audience knows the basics
- ❌ **Pure code refactorings** - unless there's user-visible impact
- ❌ **Test improvements** - internal quality work doesn't need a werk

### Technical Details: When and How

**You CAN include implementation details or technical background**, but:

- Make it clear these sections are **optional background info**
- Put them under a separate headline like "Technical background" or "How it works"
- Focus the main text on user impact first

Example:

```
## What changed
The agent receiver now handles concurrent connections correctly and won't crash
when multiple agents send data simultaneously.

## Technical background
Previously, the receiver had a race condition in the data buffer management.
Multiple threads could access the buffer concurrently without proper locking,
leading to memory corruption. We've added proper synchronization using a mutex.
```

## Common Patterns

### Feature

```
You can now [do something new]. [Explain how to use it and when it's useful]
```

### Fix

```
Previously, [describe the problem clearly]. This has been fixed.

[Optional: explain the resolution or what changed]
```

**Notes for fix werks:**

### Security

```
We've fixed a security vulnerability where [brief description of the issue].

[Impact and any required actions]
```

**Notes for security werks:**

- Describe the impact clearly
- Avoid detailed exploit information
- Mention affected versions if relevant
- Provide mitigation steps if needed

### Breaking Changes (compatible: no)

When something breaks compatibility:

- **Clearly state what breaks** - be specific
- **Provide migration path** - tell users what to do
- **Explain why** - breaking changes need justification

Example:

```
## What changed
The configuration format for custom checks has changed. Old configurations
won't work after upgrading.

## Migration required
Update your custom check configurations using the migration script:
`cmk-update-config --migrate-custom-checks`

The script converts your old configs automatically.

## Why this change
The old format couldn't support parameterized checks, which several new
monitoring plugins require. The new format is also more consistent with
other Checkmk configuration patterns.
```

### Checkmk specific language

Some references should be presented in a specific format:

- When referencing a Checkmk ruleset or a specific Checkmk service, write the ruleset's/service's official title in _italic_. Don't use internal IDs.
- Reference service/host states (Ok, Warning, Critical, Unknown) as preformatted and uppercase: `OK`, `WARN`, `CRIT`, `UNKWN`

### Concrete examples

#### Example 1: Feature, Level 1

```
# AWS tag import: Enable filtering and ignoring of tags

This werk enables users to filter the tags imported for AWS monitoring as Checkmk labels or to ignore all such tags.
A new option "Import tags as host labels" is available for both the AWS rule and the AWS quick setup. Users can choose to either import all valid tags or to filter valid tags by a regular expression pattern. To ignore AWS tags the option must be unchecked.

Tags are imported as Checkmk host labels in the format "cmk/aws/tag/{key}:{value}" for EC2 and ELB piggyback hosts.

This change does not affect earlier configurations of the AWS rule. Such configurations continue to import all valid tags.
```

**Why this is a good feature werk:**

- Explains what the feature does in user terms
- Provides usage instructions
- Explains the tag format
- Notes backward compatibility
- Conversational but professional tone

#### Example 2: Feature, Level 2

```
# Linux agent: single directory deployment

It's now possible to deploy the Checkmk agent under a single directory on Linux systems.

## What does this mean?

When installing a Checkmk agent on a Linux (or UNIX) host, its contents are distributed over
multiple folders, like `/usr/lib/check_mk_agent`, `/var/lib/check_mk_agent`,
`/etc/check_mk`, `/usr/bin`.
While this approach loosely follows the filesystem hierarchy standard for UNIX-like systems,
it also violates it in some details.

Since there is no real advantage in this approach, and it's sometimes hard to overview all
agent related files, we now offer to install the Checkmk agent under one single root directory
on Linux systems, which defaults to `/opt/checkmk/agent/default`.

## New bakery ruleset _Customize agent package (Linux)_

You can deploy the agent files under a single directory by entering a path at the new agent bakery
ruleset _Customize agent package (Linux)_, under _Installation directories: Directory for Checkmk agent_.

This path defaults to `/opt/checkmk/agent`, and it's active as soon as you add a rule instance.
Please note that the agent installation will always create one additional `default` subfolder, so the final
agent installation directory is `<installation_directory>/default`.

Note: There is also an optional _Customize user_ entry that can be used to enable the new non-root agent deployment,
which is described in more detail in Werk #17901.

The ruleset _Customize agent package (Linux)_ is also a replacement for the
_Installation paths for agent files (Linux, UNIX)_ ruleset. When configuring both rulesets, the
new _Customize agent package (Linux)_ ruleset will win, and the other one will be ignored.
Though, when currently using the old ruleset, please keep it activated while updating to the new
ruleset, since the agent package needs the custom installation paths to properly migrate runtime
files on agent update.

After configuring _Customize agent package (Linux)_ and baking agents, you can either install
the resulting packages manually on target hosts, or letting them update on next automatic
agent update.

We plan to make the single directory deployment the new standard. Hence, the ruleset
_Installation paths for agent files(Linux, UNIX)_ will be removed in a future Checkmk release,
so we recommend to use the new approach of _Customize agent package (Linux)_ instead.

## Is this ruleset really Linux-only?

You can configure the _Customize agent package_ ruleset as described above, bake agents,
and observe that all resulting UNIX-like packages come with the new single directory structure.
Hence, the answer is: Yes, the single directory depoyment is available for all baked agents for
UNIX-like systems. However, we declare the whole feature as Linux-only because only managed
packages (`.rpm` and `.deb`) come with the whole featureset. This includes the migration of
existing Checkmk agent installations and making shipped executables available under symlinks
at `/usr/bin` (since they are located under `/opt/checkmk/agent/default/package/bin` now and
are not directly available in `$PATH`).

## Some technical details (FYI)

When choosing the single directory deployment, all contents of the Checkmk agent will be installed under
the folder `<configured_directory>/default`, which itself will contain two subfolders `package` and `runtime`.
`package` contains all static agent files resulting from the Agent Bakery configuration; `runtime` is there
for all files that get created while agent operation. This includes state files, logs, cache files, etc..

Internally, the agent finds its files with the help of some environment variables that exist equally for the
old multiple directory deployment, like `MK_LIBDIR`, `MK_VARDIR`, `MK_BIN`, `MK_CONFDIR`.
Additionally, there is now the new environment variable `MK_INSTALLDIR` that acts, when existant, as a switch
to activate the single directory deployment. When available, the agent will set all environment variables
by itself based on `MK_INSTALLDIR`, e.g., `MK_LIBDIR=${MK_INSTALLDIR}/package`.
```

**Why this is a good prominent feature werk:**

- For a prominent feature, it's okay to go a bit more into details
- Briefly explains motivation and scope
- Explains what the feature does in user terms
- Provides usage instructions
- Provides relevant context
- Conversational but professional tone

#### Example 3: Fix

```
# Fix Reset to default for 'Trusted Certificate Authorities for SSL'

While modifying the global setting "Trusted Certificate Authorities for SSL"
resetting to default caused the software to crash with the following message:

_Internal error: cannot access local variable 'current' where it is not associated with a value_
```

**Why this is a good fix werk:**

- Clear description of the problem
- Includes the exact error message users would see
- Concise - no unnecessary explanation
- Technical but accessible

#### Example 4: Security

```
# Fix Livestatus injection via REST-API

Prior to this fix, a REST API endpoint improperly handled escaping of data received through POST requests. This vulnerability allowed users with the `update_and_acknowledge` permission for events to inject arbitrary Livestatus commands via the affected endpoint.

**Affected Versions**:

- 2.4.0 (beta)
- 2.3.0
- 2.2.0
- 2.1.0 (EOL)

**Vulnerability Management**:

We have rated the issue with a CVSS score of 6.0 (Medium) with the following CVSS vector: `CVSS:4.0/AV:N/AC:L/AT:P/PR:L/UI:N/VC:N/VI:L/VA:H/SC:N/SI:N/SA:N`, and assigned `CVE-2024-38865`.
```

**Why this is a good security werk:**

- Clear description of the vulnerability without exploit details
- Lists affected versions
- Includes CVSS score and CVE ID
- Professional security disclosure format
- Explains impact without being alarmist
