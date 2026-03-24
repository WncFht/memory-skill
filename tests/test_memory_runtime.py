from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SYNC_WRAPPER = ROOT / "scripts" / "sync-memory.sh"
INIT_WRAPPER = ROOT / "scripts" / "init-memory.sh"
SYNC_CMD = ROOT / "scripts" / "sync-memory.cmd"
INIT_CMD = ROOT / "scripts" / "init-memory.cmd"
SYNC_PS1 = ROOT / "scripts" / "sync-memory.ps1"
INIT_PS1 = ROOT / "scripts" / "init-memory.ps1"


def run(args: list[str], *, env: dict[str, str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def git(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


class MemoryRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp())
        self.home_dir = self.temp_dir / "home"
        self.home_dir.mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def env(self, **overrides: str) -> dict[str, str]:
        env = os.environ.copy()
        env["HOME"] = str(self.home_dir)
        env["USERPROFILE"] = str(self.home_dir)
        env.update(overrides)
        return env

    def init_repo(self, path: Path, *, remote: Path | None = None) -> subprocess.CompletedProcess[str]:
        args = [str(INIT_WRAPPER), "--memory-root", str(path)]
        if remote:
            args.extend(["--remote", str(remote)])
        return run(args, env=self.env())

    def sync(self, path: Path, operation: str, *, env_overrides: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        env = self.env(**(env_overrides or {}))
        return run([str(SYNC_WRAPPER), "--memory-root", str(path), operation], env=env)

    def test_init_creates_memory_repo_and_state(self) -> None:
        memory_root = self.temp_dir / "memory"
        result = self.init_repo(memory_root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((memory_root / "core.md").is_file())
        self.assertTrue((memory_root / "rules.md").is_file())
        self.assertTrue((memory_root / "machines" / "index.md").is_file())
        self.assertTrue((memory_root / "repos" / "index.md").is_file())
        state_file = self.home_dir / ".codex" / "state" / "memory-skill" / "state.json"
        payload = json.loads(state_file.read_text(encoding="utf-8"))
        self.assertEqual(payload["memory_root"], str(memory_root))
        self.assertIn("memory repo initialized", result.stdout)

    def test_explicit_memory_root_overrides_env_and_state(self) -> None:
        state_root = self.temp_dir / "state-root"
        env_root = self.temp_dir / "env-root"
        explicit_root = self.temp_dir / "explicit-root"

        self.assertEqual(self.init_repo(state_root).returncode, 0)
        self.assertEqual(self.init_repo(env_root).returncode, 0)
        self.assertEqual(self.init_repo(explicit_root).returncode, 0)

        state_file = self.home_dir / ".codex" / "state" / "memory-skill" / "state.json"
        state_file.write_text(
            json.dumps({"memory_root": str(state_root)}, indent=2) + "\n",
            encoding="utf-8",
        )

        result = run(
            [str(SYNC_WRAPPER), "--memory-root", str(explicit_root), "pre-read"],
            env=self.env(MEMORY_ROOT=str(env_root)),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(str(explicit_root), result.stdout)
        self.assertNotIn(str(state_root), result.stdout)

    def test_saved_root_is_used_when_no_override_exists(self) -> None:
        memory_root = self.temp_dir / "memory"
        self.assertEqual(self.init_repo(memory_root).returncode, 0)
        result = run([str(SYNC_WRAPPER), "pre-read"], env=self.env())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(str(memory_root), result.stdout)

    def test_adopt_rejects_invalid_existing_directory(self) -> None:
        invalid_root = self.temp_dir / "not-a-memory-repo"
        invalid_root.mkdir()
        (invalid_root / "random.txt").write_text("hello\n", encoding="utf-8")
        result = run(
            [str(INIT_WRAPPER), "--memory-root", str(invalid_root), "--adopt"],
            env=self.env(),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("What happened:", result.stderr)
        self.assertIn("not a valid memory repo layout", result.stderr)

    def test_pre_read_rejects_dirty_worktree(self) -> None:
        memory_root = self.temp_dir / "memory"
        self.assertEqual(self.init_repo(memory_root).returncode, 0)
        (memory_root / "core.md").write_text("dirty\n", encoding="utf-8")
        result = self.sync(memory_root, "pre-read")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("uncommitted changes", result.stderr)

    def test_post_write_bootstraps_remote_tracking(self) -> None:
        remote = self.temp_dir / "remote.git"
        git(["init", "--bare", str(remote)], cwd=self.temp_dir)
        memory_root = self.temp_dir / "memory"
        init_result = self.init_repo(memory_root, remote=remote)
        self.assertEqual(init_result.returncode, 0, init_result.stderr)

        with (memory_root / "core.md").open("a", encoding="utf-8") as handle:
            handle.write("new line\n")

        result = self.sync(memory_root, "post-write")
        self.assertEqual(result.returncode, 0, result.stderr)
        upstream = git(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"], cwd=memory_root)
        self.assertEqual(upstream.stdout.strip(), "origin/main")
        self.assertIn("Remote bootstrap", result.stdout)

    def test_stale_lock_is_recovered(self) -> None:
        memory_root = self.temp_dir / "memory"
        self.assertEqual(self.init_repo(memory_root).returncode, 0)
        git_dir = Path(git(["rev-parse", "--git-dir"], cwd=memory_root).stdout.strip())
        if not git_dir.is_absolute():
            git_dir = memory_root / git_dir
        lock_dir = git_dir / "memory-sync.lock"
        lock_dir.mkdir()
        (lock_dir / "owner.json").write_text(
            json.dumps({"host": "localhost", "pid": 999999, "operation": "pre-read"}),
            encoding="utf-8",
        )
        heartbeat = lock_dir / "heartbeat"
        heartbeat.write_text("0\n", encoding="utf-8")
        stale_time = time.time() - 120
        os.utime(heartbeat, (stale_time, stale_time))

        result = self.sync(memory_root, "pre-read")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(lock_dir.exists())

    def test_live_lock_times_out_with_owner_details(self) -> None:
        memory_root = self.temp_dir / "memory"
        self.assertEqual(self.init_repo(memory_root).returncode, 0)
        git_dir = Path(git(["rev-parse", "--git-dir"], cwd=memory_root).stdout.strip())
        if not git_dir.is_absolute():
            git_dir = memory_root / git_dir
        lock_dir = git_dir / "memory-sync.lock"
        lock_dir.mkdir()
        (lock_dir / "owner.json").write_text(
            json.dumps(
                {
                    "host": socket.gethostname(),
                    "pid": os.getpid(),
                    "operation": "pre-read",
                    "memory_root": str(memory_root),
                    "started_at": "now",
                }
            ),
            encoding="utf-8",
        )
        (lock_dir / "heartbeat").write_text("0\n", encoding="utf-8")

        result = self.sync(
            memory_root,
            "pre-read",
            env_overrides={
                "MEMORY_SYNC_WAIT_TIMEOUT_SECONDS": "0.4",
                "MEMORY_SYNC_WAIT_POLL_SECONDS": "0.1",
            },
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Timed out waiting for the sync lock", result.stderr)
        self.assertIn("host=", result.stderr)
        self.assertIn("pid=", result.stderr)

    def test_supported_entrypoints_exist_and_posix_wrappers_work(self) -> None:
        self.assertTrue(SYNC_WRAPPER.is_file())
        self.assertTrue(INIT_WRAPPER.is_file())
        self.assertTrue(SYNC_CMD.is_file())
        self.assertTrue(INIT_CMD.is_file())
        self.assertTrue(SYNC_PS1.is_file())
        self.assertTrue(INIT_PS1.is_file())

        init_help = run([str(INIT_WRAPPER), "--help"], env=self.env())
        sync_help = run([str(SYNC_WRAPPER), "--help"], env=self.env())
        self.assertEqual(init_help.returncode, 0, init_help.stderr)
        self.assertEqual(sync_help.returncode, 0, sync_help.stderr)
        self.assertIn("usage:", init_help.stdout)
        self.assertIn("usage:", sync_help.stdout)


if __name__ == "__main__":
    unittest.main()
