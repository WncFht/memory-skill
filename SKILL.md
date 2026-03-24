---
name: memory-skill
description: Use when Codex needs machine, repo, or cross-repo context from the curated memory tree in `~/.codex/memory/`.
---

# Memory Skill

You maintain agent-wide curated memory in `~/.codex/memory/`, not per-repo
notes and not a chronological log. Read the smallest relevant set of memory
packs first, then expand only when the task needs more detail.

## Canonical Root

All memory lives under `~/.codex/memory/`.

- `core.md`: always-read shared memory
- `rules.md`: write-back and curation policy
- `scripts/sync-memory.sh`: sync helper for pre-read and post-write git flow
- `machines/index.md`: machine resolution
- `machines/<machine-id>/summary.md`: machine-specific memory
- `machines/<machine-id>/repo-paths.md`: local path to repo-id mappings
- `repos/index.md`: canonical repo identities
- `repos/<repo-id>/summary.md`: repo entrypoint
- `repos/<repo-id>/*.md`: repo detail packs
- `topics/<topic>.md`: cross-repo topic packs

Index files are routing tables. Memory packs are curated notes.

## Before First Memory Read

Before relying on memory for a task:

1. Before relying on any memory file, run
   `~/.codex/memory/scripts/sync-memory.sh pre-read`.
2. Read `~/.codex/memory/core.md` and apply it silently.
3. Resolve the current machine through `~/.codex/memory/machines/index.md`.
4. Read the matching machine summary.
5. If the current working directory belongs to a known repo, resolve the repo
   id and read that repo's `summary.md`.
6. Do not bulk-read topic packs or repo detail packs during initial loading.

Do not announce that you read memory. Just apply what you learn.

If the sync helper fails, stop and surface the reason. Do not auto-stash local
changes, do not silently skip the sync, and do not read known-stale memory as
if it were current.

## Machine Resolution

Resolve the machine first. Use `~/.codex/memory/machines/index.md` to map the
current host to a machine id.

After resolving the machine id:

- Read `machines/<machine-id>/summary.md`.
- Use `machines/<machine-id>/repo-paths.md` when you need to map the current
  working directory to a repo id.

If the current machine is missing, continue without machine memory until you
have durable machine-specific facts worth recording. When you do create a new
machine pack, add both `summary.md` and `repo-paths.md`, then run the required
post-write sync.

## Repo Resolution

Repo memory is stored only under `~/.codex/memory/repos/`.

To resolve the current repo:

1. Prefer exact or longest-parent-prefix path matches from the current
   machine's `repo-paths.md`.
2. If no path match exists and you are inside a git repo, use git metadata to
   match an existing repo entry in `repos/index.md`.
3. If the repo is still unknown, work without repo memory until you have enough
   stable information to create a new repo pack.

Never write repo memory back into the repo itself.

## Progressive Disclosure

Read the minimum useful set of files first:

- `core.md`
- the current machine summary
- the current repo summary, if resolved

Only expand additional packs when needed:

- Read a topic pack when the task involves that tool, platform, workflow, or
  failure mode.
- Read a repo detail pack when the repo summary points to it or the task is
  clearly about that area.
- Prefer reading one additional file at a time.
- Stop expanding once you have enough context to proceed reliably.

Never load the whole memory tree just because it exists.

Run the pre-read sync once before the first memory read in a task, then read as
many relevant packs as needed from that synchronized snapshot. Run it again
only after you have written memory or when fresh remote edits are likely.

## Continuous Updates

Update memory during work whenever you learn something durable and reusable.
Route new memory to the smallest durable scope that fits:

- `core.md`: defaults that should affect most sessions
- `topics/<topic>.md`: cross-repo knowledge for a specific tool or theme
- `machines/<machine-id>/summary.md`: machine-specific facts and rules
- `repos/<repo-id>/*.md`: repo-specific memory

Use `rules.md` for curation policy, scope decisions, summary-vs-detail rules,
and promotion or demotion between packs.

After editing any file under `~/.codex/memory/`, immediately run
`~/.codex/memory/scripts/sync-memory.sh post-write`.
Use the default commit message unless the change clearly deserves a more
specific one via `-m`.

## Practical Rule

Think of memory-skill as a live agent memory system for future execution speed and
reliability. It is not a history file and it is not a dumping ground.
