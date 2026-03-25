# Memory Skill

`memory-skill` 是 Codex agent memory repo 的运行时和工作约定。它负责：

- 初始化或接管 memory repo
- 解析当前生效的 memory root
- 在读取前同步，在写入后发布
- 把 memory 保持在“小而可复用”的粒度
- 在真实网络环境里尽量稳妥地处理 GitHub 同步、代理和认证

英文版说明见：[README.md](./README.md)

## 这个仓库负责什么

这个仓库是 skill 的实现，不是 memory 数据本身。

- skill repo：`~/.codex/skills/memory-skill`
- memory repo：通常是 `~/.codex/memory`
- active root 状态文件：`~/.codex/state/memory-skill/state.json`

也就是说：这里放的是运行时和文档，真正的 memory 内容在另一个 git repo
树里。

## 安装

```bash
git clone git@github.com:WncFht/memory-skill.git ~/.codex/skills/memory-skill
```

如果你是在替换旧安装，并且旧版本用了不同目录名，请先删掉旧目录，避免
Codex 同时识别到多个 `memory-skill` 副本。

## 首次使用

第一次同步前，先创建或接管一个 memory repo。

创建新的 memory repo：

```bash
~/.codex/skills/memory-skill/scripts/init-memory.sh --memory-root ~/.codex/memory
```

接管已有的合法 memory repo：

```bash
~/.codex/skills/memory-skill/scripts/init-memory.sh \
  --memory-root ~/.codex/memory \
  --adopt
```

初始化或接管完成后，当前 active memory root 会被记录到
`~/.codex/state/memory-skill/state.json`。

## 心智模型

最重要的不是“多读”，而是“按轮次读、按批次写”。

- 读轮次：先跑一次 `pre-read`，再从这个同步快照里读取一个或多个 memory 文件
- 写批次：完成一组相关改动后，跑一次 `post-write` 发布
- memory 是未来任务要复用的工作知识，不是聊天记录，也不是杂物堆

## 典型工作流

### 1. 读之前先同步

```bash
~/.codex/skills/memory-skill/scripts/sync-memory.sh pre-read
```

如果 memory repo 合法且干净，runtime 会：

- 解析 active memory root
- 获取 repo 锁
- 如果存在 upstream，就先 fetch 再 fast-forward
- 如果是 local-only repo，就保持本地模式

### 2. 先读最小必要集合

优先读取：

- `core.md`
- 当前机器摘要
- 当前 repo 摘要（如果能稳定解析）

只有当任务真的需要时，再扩展读取 topic pack 或 repo detail pack。

### 3. 写回持久、可复用的信息

适合写进 memory 的东西包括：

- 持久的用户偏好
- 机器级环境事实
- repo 级工作流
- 跨 repo 的操作知识

### 4. 发布写批次

```bash
~/.codex/skills/memory-skill/scripts/sync-memory.sh post-write
```

如果配置了远端，`post-write` 会：

- 在有改动时创建 commit
- fetch 远端
- 必要时 rebase 到 upstream
- push 当前分支

如果没有远端，也会保持本地 commit 语义一致。

## Active Memory Root 解析顺序

当前生效的 memory root 按下面顺序解析：

1. `--memory-root <path>`
2. `MEMORY_ROOT`
3. `~/.codex/state/memory-skill/state.json`
4. 默认值 `~/.codex/memory`

## Memory 目录结构

- `core.md`：影响大多数会话的默认规则
- `rules.md`：整理、提升、拆分 memory 的规则
- `machines/`：机器级摘要与 repo 路径映射
- `repos/`：repo 摘要与细分 memory pack
- `topics/`：跨 repo / 跨工具复用的主题知识

索引文件负责路由，memory pack 负责存放真正的知识。

## 常用命令

### 初始化一个新的 memory repo

```bash
~/.codex/skills/memory-skill/scripts/init-memory.sh \
  --memory-root ~/.codex/memory \
  --branch main
```

### 初始化时同时配置远端

```bash
~/.codex/skills/memory-skill/scripts/init-memory.sh \
  --memory-root ~/.codex/memory \
  --remote git@github.com:your-org/agent-memory.git
```

### 读之前同步

```bash
~/.codex/skills/memory-skill/scripts/sync-memory.sh pre-read
```

### 写完之后发布

```bash
~/.codex/skills/memory-skill/scripts/sync-memory.sh post-write
```

### 给写批次指定 commit message

```bash
~/.codex/skills/memory-skill/scripts/sync-memory.sh post-write \
  -m "docs(memory): record archbox proxy setup"
```

## 网络、代理与认证

真实机器上的 GitHub SSH 并不总是稳定，所以 runtime 现在把这件事当成一等
公民来处理。

### runtime 现在会做什么

- 所有 git 调用都走 proxy-aware 环境
- GitHub SSH 不通时，支持带 token 的 HTTPS fallback
- 未显式配置代理时，会尝试常见本地 SOCKS 端口
- 失败信息会尽量给出可执行的修复提示

### GitHub 认证相关环境变量

| 变量 | 用途 |
| --- | --- |
| `MEMORY_SYNC_GITHUB_TOKEN` | 私有 GitHub repo 的首选 token |
| `GITHUB_TOKEN` | 回退 token |
| `GH_TOKEN` | 额外回退 token |

### 代理相关环境变量

| 变量 | 用途 |
| --- | --- |
| `MEMORY_SYNC_SOCKS_PROXY` | 显式指定 SOCKS 代理，例如 `socks5://127.0.0.1:7897` |
| `ALL_PROXY` / `all_proxy` | 复用已有代理环境 |
| `MEMORY_SYNC_DISABLE_LOCAL_PROXY_AUTODETECT=1` | 禁用内建本地代理自动探测 |

如果没有显式代理，runtime 目前会尝试以下常见本地 SOCKS 入口：

- `socks5://127.0.0.1:7897`
- `socks5h://127.0.0.1:7891`

### 同步相关调优环境变量

| 变量 | 默认值 | 用途 |
| --- | --- | --- |
| `MEMORY_SYNC_HEARTBEAT_SECONDS` | `2.0` | 锁心跳间隔 |
| `MEMORY_SYNC_STALE_AFTER_SECONDS` | `30.0` | stale lock 判定阈值 |
| `MEMORY_SYNC_WAIT_TIMEOUT_SECONDS` | `300.0` | 等锁超时 |
| `MEMORY_SYNC_WAIT_POLL_SECONDS` | `0.2` | 轮询锁状态的间隔 |

## 常见问题

### `pre-read` 提示 worktree 有未提交改动

这是故意的。`pre-read` 只信任干净的快照。

- 这些改动应该保留：先跑 `post-write`
- 这些改动不该存在：清理后再重试

### GitHub SSH 报 connection closed / timed out

优先按这个顺序排查：

- 显式设置 `MEMORY_SYNC_SOCKS_PROXY`
- 确认可用的本地 SOCKS 代理确实在监听
- 私有 repo 再补 `MEMORY_SYNC_GITHUB_TOKEN`

### runtime 提示不能把旧 memory 当成当前快照

这是设计目标。除了“repo 还没初始化”这种情况以外，sync 失败时就应该停止并
把原因抛给调用方，而不是悄悄继续读旧数据。

### `post-write` 因为 git identity 缺失而失败

先配置一次 git：

```bash
git config --global user.name "your-name"
git config --global user.email "you@example.com"
```

### 想看更详细的 runbook

见 [docs/sync-and-troubleshooting.md](./docs/sync-and-troubleshooting.md)。

## 开发

运行 runtime 测试：

```bash
python -m unittest discover -s ~/.codex/skills/memory-skill/tests -p 'test_memory_runtime.py'
```

Shell / CMD / PowerShell 包装脚本都会委托给同一个 Python runtime，因此
Linux、macOS、Windows 三端行为会尽量保持一致。

## License

MIT
