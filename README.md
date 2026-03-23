# Memory Skill

A Codex skill that maintains canonical agent memory in `~/.codex/memory/`
instead of ad hoc per-repo notes. It keeps the memory repo synchronized before
reads, routes durable knowledge into machine, repo, and topic packs, and
publishes memory updates immediately after writes.

## Install

```bash
git clone git@github.com:WncFht/memory-skill.git ~/.codex/skills/memory-skill
```

If you are replacing an older local install under another folder name, remove
that directory first so Codex only sees one active copy of the skill.

## How It Works

1. Before the first memory read in a task, the skill runs
   `~/.codex/memory/scripts/sync-memory.sh pre-read`.
2. The agent reads the smallest useful set of memory packs first:
   `core.md`, the current machine summary, and the current repo summary when it
   resolves cleanly.
3. During work, the agent writes durable findings back to the smallest useful
   scope under `~/.codex/memory/`.
4. After editing memory, the skill runs
   `~/.codex/memory/scripts/sync-memory.sh post-write` to commit, rebase, and
   push the updates.

## Memory Layout

- `core.md`: defaults that should affect most sessions
- `machines/`: host-specific summaries and repo path maps
- `repos/`: repo entrypoints and detail packs
- `topics/`: cross-repo knowledge such as networking or `chezmoi`
- `scripts/sync-memory.sh`: the shared sync helper used before reads and after
  writes

## What Belongs In Memory

- Durable user directives
- Repeatable environment facts
- Repo-specific rules that save future debugging time
- Cross-repo workflows that keep recurring

Keep temporary state, verbose logs, and one-off timelines out of the memory
tree.

## License

MIT
