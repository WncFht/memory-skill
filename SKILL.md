---
name: memory-skill
description: Use when starting a session or when Codex needs machine, repo, or cross-repo context from the curated memory repo managed by `memory-skill`.
---

# Memory Skill

You maintain agent-wide curated memory in an active memory repo managed by
`memory-skill`, not per-repo notes and not a chronological log. Read the
smallest relevant set of memory packs first, then expand only when the task
needs more detail.

## Active Memory Root

Memory lives in the currently resolved memory root.

- `core.md`: always-read shared memory
- `rules.md`: write-back and curation policy
- `machines/index.md`: machine resolution
- `machines/<machine-id>/summary.md`: machine-specific memory
- `machines/<machine-id>/repo-paths.md`: local path to repo-id mappings
- `repos/index.md`: canonical repo identities
- `repos/<repo-id>/summary.md`: repo entrypoint
- `repos/<repo-id>/*.md`: repo detail packs
- `topics/<topic>.md`: cross-repo topic packs

Index files are routing tables. Memory packs are curated notes.

## Runtime Entrypoints

Use the skill-owned commands instead of running scripts from inside the memory
repo:

- `~/.codex/skills/memory-skill/scripts/init-memory.sh`
- `~/.codex/skills/memory-skill/scripts/sync-memory.sh`

The active memory root resolves in this order:

1. `--memory-root <path>`
2. `MEMORY_ROOT`
3. `~/.codex/state/memory-skill/state.json`
4. default `~/.codex/memory`

If no valid memory repo exists yet, initialize or adopt one before attempting
to read memory.

## Session Bootstrap

At session start, before the first user-facing response:

1. Before relying on any memory file, run
   `~/.codex/skills/memory-skill/scripts/sync-memory.sh pre-read`.
2. If that fails because no valid memory repo exists yet, create or bind one
   with `~/.codex/skills/memory-skill/scripts/init-memory.sh --memory-root <path>`.
3. Read the resolved memory repo's `core.md` and apply it silently.
4. Resolve the current machine through `machines/index.md`.
5. Read the matching machine summary.
6. If the current working directory belongs to a known repo, resolve the repo
   id and read that repo's `summary.md`.
7. Do not bulk-read topic packs or repo detail packs during startup bootstrap.

Do not announce that you read memory. Just apply what you learn.

If the sync helper fails, stop and surface the reason. Do not auto-stash local
changes, do not silently skip the sync, and do not read known-stale memory as
if it were current.

## Read Rounds

Before each new round of memory reads, run
`~/.codex/skills/memory-skill/scripts/sync-memory.sh pre-read` once.

A read round may open multiple relevant memory files from the synchronized
snapshot. Do not rerun `pre-read` for every file in the same round.

Start a new read round when you return to memory after doing other work, when
the task shifts to a different memory question, or after a write batch has been
published.

## Machine Resolution

Resolve the machine first. Use `machines/index.md` inside the active memory root
to map the current host to a machine id.

After resolving the machine id:

- Read `machines/<machine-id>/summary.md`.
- Use `machines/<machine-id>/repo-paths.md` when you need to map the current
  working directory to a repo id.

If the current machine is missing, continue without machine memory until you
have durable machine-specific facts worth recording. When you do create a new
machine pack, add both `summary.md` and `repo-paths.md`, then run the required
post-write sync.

## Repo Resolution

Repo memory is stored only under `repos/` inside the active memory root.

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

Within one read round, open as many relevant packs as needed from that
synchronized snapshot. Start a new read round before reading memory again after
later task changes or after a write batch.

## Continuous Updates

Update memory during work whenever you learn something durable and reusable.
Route new memory to the smallest durable scope that fits:

- `core.md`: defaults that should affect most sessions
- `topics/<topic>.md`: cross-repo knowledge for a specific tool or theme
- `machines/<machine-id>/summary.md`: machine-specific facts and rules
- `repos/<repo-id>/*.md`: repo-specific memory

Use `rules.md` for curation policy, scope decisions, summary-vs-detail rules,
and promotion or demotion between packs.

## Write Batches

A write batch may update multiple memory files that belong to the same logical
memory update.

After editing any file under the active memory root for that batch, immediately
run `~/.codex/skills/memory-skill/scripts/sync-memory.sh post-write` once to
commit, sync, and publish the batch when a remote is configured.

Do not leave local memory edits unpublished between batches. Use the default
commit message unless the change clearly deserves a more specific one via `-m`.

## Practical Rule

Think of memory-skill as a live agent memory system for future execution speed and
reliability. It is not a history file and it is not a dumping ground.
