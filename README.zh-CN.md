# Memory Skill

`memory-skill` 是一个为 agent memory repo 提供运行时能力的 Codex skill。
它可以初始化新的 memory repo、接管已有 repo、从命令行参数、环境变量或
本地状态中解析当前生效的 memory root，并在读取前和写入后保持仓库同步。

英文版说明见：[README.md](./README.md)

## 安装

```bash
git clone git@github.com:WncFht/memory-skill.git ~/.codex/skills/memory-skill
```

如果你是在替换旧版本，并且旧版本使用了不同的目录名，请先移除旧目录，
避免 Codex 同时识别到多个同名 skill 副本。

## 首次设置

在第一次执行同步前，先创建或绑定一个 memory repo：

```bash
~/.codex/skills/memory-skill/scripts/init-memory.sh --memory-root ~/.codex/memory
```

如果你不想把 memory repo 放在 `~/.codex/memory`，可以传入别的路径。
skill 会把当前 active memory root 记录到
`~/.codex/state/memory-skill/state.json`。

## Active Memory Root 解析顺序

当前生效的 memory root 按下面顺序解析：

1. `--memory-root <path>`
2. `MEMORY_ROOT`
3. `~/.codex/state/memory-skill/state.json`
4. 默认值 `~/.codex/memory`

## 工作方式

1. 在一个任务中第一次读取 memory 之前，skill 会运行
   `~/.codex/skills/memory-skill/scripts/sync-memory.sh pre-read`。
2. agent 会先读取最小必要集合：
   `core.md`、当前机器摘要，以及能稳定解析时的当前 repo 摘要。
3. 在执行过程中，agent 会把可复用、持久的结论写回 active memory root
   下最合适的粒度。
4. 修改 memory 后，skill 会运行
   `~/.codex/skills/memory-skill/scripts/sync-memory.sh post-write`，
   在配置了远端时完成提交、同步和发布。

## 支持的入口脚本

- `scripts/init-memory.sh`
- `scripts/init-memory.cmd`
- `scripts/init-memory.ps1`
- `scripts/sync-memory.sh`
- `scripts/sync-memory.cmd`
- `scripts/sync-memory.ps1`

这些包装脚本都会委托给同一个 Python runtime，因此在 Windows、Linux 和
macOS 上能保持一致行为。

## Memory 目录结构

- `core.md`：影响大多数会话的通用默认规则
- `machines/`：机器级摘要和 repo 路径映射
- `repos/`：repo 入口摘要和细分 memory packs
- `topics/`：跨 repo 的主题知识，例如网络或 `chezmoi`
- 本地状态：`~/.codex/state/memory-skill/state.json`

## 什么内容适合写进 Memory

- 持久的用户指令
- 可重复利用的环境事实
- 能节省后续排障时间的 repo 规则
- 会反复出现的跨 repo 工作流

不要把临时状态、冗长日志或一次性的时间线塞进 memory tree。

## License

MIT
