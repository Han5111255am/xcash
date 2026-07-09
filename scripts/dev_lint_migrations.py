# ruff: noqa: INP001
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from dev_manage import load_env_file
from dev_manage import set_default_environment
from django.core.management import execute_from_command_line


def git_ref_exists(ref: str) -> bool:
    git_executable = shutil.which("git")
    if git_executable is None:
        return False
    result = subprocess.run(
        [git_executable, "rev-parse", "--verify", "--quiet", ref],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def main() -> None:
    load_env_file()
    set_default_environment()

    base_ref = os.environ.get("MIGRATION_LINTER_BASE", "origin/main")
    if not git_ref_exists(base_ref):
        base_ref = "HEAD"

    project_root = Path(__file__).resolve().parent.parent
    execute_from_command_line(
        [
            sys.argv[0],
            "lintmigrations",
            "--git-commit-id",
            base_ref,
            "--project-root-path",
            str(project_root),
            "--no-cache",
        ]
    )


if __name__ == "__main__":
    main()
