# Memory Skill

A Codex skill that owns the runtime for agent memory repos. It can initialize a
new memory repo, adopt an existing one, resolve the active memory root from
flags, environment, or local state, and keep the repo synchronized before reads
and after writes.

Chinese README: [README.zh-CN.md](./README.zh-CN.md)

## Install

```bash
git clone git@github.com:WncFht/memory-skill.git ~/.codex/skills/memory-skill
```

If you are replacing an older local install under another folder name, remove
that directory first so Codex only sees one active copy of the skill.

## First-Run Setup

Create or bind a memory repo before the first sync:

```bash
~/.codex/skills/memory-skill/scripts/init-memory.sh --memory-root ~/.codex/memory
```

Use a different path if you do not want the repo under `~/.codex/memory`. The
skill saves the active root in `~/.codex/state/memory-skill/state.json`.

## How It Works

1. Before the first memory read in a task, the skill runs
   `~/.codex/skills/memory-skill/scripts/sync-memory.sh pre-read`.
2. The agent reads the smallest useful set of memory packs first:
   `core.md`, the current machine summary, and the current repo summary when it
   resolves cleanly.
3. During work, the agent writes durable findings back to the smallest useful
   scope under the active memory root.
4. After editing memory, the skill runs
   `~/.codex/skills/memory-skill/scripts/sync-memory.sh post-write` to commit,
   sync, and publish the updates when a remote is configured.

## Supported Entrypoints

- `scripts/init-memory.sh`
- `scripts/init-memory.cmd`
- `scripts/init-memory.ps1`
- `scripts/sync-memory.sh`
- `scripts/sync-memory.cmd`
- `scripts/sync-memory.ps1`

The wrappers all delegate to the same Python runtime so behavior stays aligned
across Windows, Linux, and macOS.

## Memory Layout

- `core.md`: defaults that should affect most sessions
- `machines/`: host-specific summaries and repo path maps
- `repos/`: repo entrypoints and detail packs
- `topics/`: cross-repo knowledge such as networking or `chezmoi`
- local state: `~/.codex/state/memory-skill/state.json`

## What Belongs In Memory

- Durable user directives
- Repeatable environment facts
- Repo-specific rules that save future debugging time
- Cross-repo workflows that keep recurring

Keep temporary state, verbose logs, and one-off timelines out of the memory
tree.

## License

MIT
