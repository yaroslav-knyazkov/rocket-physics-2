# -*- coding: utf-8 -*-
"""Tests for .claude/hooks/block-bash-write.sh (needs bash; skipped without it).

Run from the repo root:
    PYTHONUTF8=1 python -m pytest .claude/scripts/tests/test_hooks.py -v

The hook reads the PreToolUse payload from stdin and exits 0 (allow) or 2
(block). Each test builds a synthetic payload and runs the hook with a cwd
that looks like a main repo with an active task worktree
(`.claude/wt-active.json`). Nothing is written anywhere except tmp_path.
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[2] / "hooks" / "block-bash-write.sh"


def _find_bash() -> str | None:
    # Prefer Git Bash on Windows: a bare `bash` may be the WSL launcher.
    for cand in (r"C:\Program Files\Git\bin\bash.exe",
                 r"C:\Program Files (x86)\Git\bin\bash.exe"):
        if os.path.exists(cand):
            return cand
    return shutil.which("bash")


BASH = _find_bash()
pytestmark = pytest.mark.skipif(BASH is None, reason="bash is not available")


def run_hook(repo: Path, command: str) -> subprocess.CompletedProcess:
    payload = json.dumps({"tool_input": {"command": command}})
    return subprocess.run([BASH, str(HOOK)], input=payload, capture_output=True,
                          text=True, encoding="utf-8", errors="replace", cwd=str(repo))


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "wt-active.json").write_text(
        json.dumps({"current": "x", "worktrees": {"x": {"path": str(tmp_path / "wt-x")}}}),
        encoding="utf-8")
    return tmp_path


# A message that reads like every write rule at once.
BODY = "feat: add x\n\nBody: cp a b; sed -i s/a/b/ f > out.txt, tee file, rm -rf y"


@pytest.mark.parametrize("command", [
    f'python .claude/scripts/wt.py commit --slug X -m "{BODY}"',
    f'git commit -m "{BODY}"',
    f"git commit -m '{BODY}'",
    f'git commit --message="{BODY}"',
    f'git commit -m "first line" -m "{BODY}"',
    f'cd /tmp && git add -A && git commit -m "{BODY}" && git push',
])
def test_commit_messages_are_not_scanned_for_writes(repo, command):
    r = run_hook(repo, command)
    assert r.returncode == 0, r.stderr


@pytest.mark.parametrize("command", [
    "sed -i s/a/b/ f.txt",
    'git commit -m "x" && echo hi > out.txt',
    'git commit -m "x"; sed -i s/a/b/ f.txt',
    'git commit -m "x" ; echo a > .env',
])
def test_real_writes_next_to_a_commit_message_are_still_blocked(repo, command):
    r = run_hook(repo, command)
    assert r.returncode == 2, r.stdout + r.stderr


def test_plain_write_is_blocked_and_read_only_passes(repo):
    assert run_hook(repo, "echo hi > out.txt").returncode == 2
    assert run_hook(repo, 'grep -n "a > b" file.txt').returncode == 0
    assert run_hook(repo, "git status 2>&1 | head").returncode == 0


def test_env_rule_is_independent_of_the_worktree(tmp_path):
    # no .claude/wt-active.json here
    r = run_hook(tmp_path, 'git commit -m "x"; echo a > .env')
    assert r.returncode == 2
