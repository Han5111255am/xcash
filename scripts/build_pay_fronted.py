# ruff: noqa: INP001
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PAY_FRONTEND_DIR = PROJECT_ROOT / "pay-fronted"
STATIC_PAY_DIR = PROJECT_ROOT / "xcash" / "static" / "pay"
BUILD_TMP_DIR = PROJECT_ROOT / "xcash" / "static" / ".pay-build-tmp"


def resolve_project_path(path: Path) -> Path:
    resolved = path.resolve()
    project_root = PROJECT_ROOT.resolve()
    try:
        resolved.relative_to(project_root)
    except ValueError as exc:
        raise RuntimeError(f"refuse to operate outside project: {resolved}") from exc
    return resolved


def remove_directory(path: Path) -> None:
    target = resolve_project_path(path)
    if target.exists():
        shutil.rmtree(target)


def find_pnpm() -> str:
    pnpm = shutil.which("pnpm")
    if pnpm is None:
        raise RuntimeError("pnpm not found. Install pnpm or enable it with corepack.")
    return pnpm


def delete_ds_store_files(path: Path) -> None:
    for ds_store in path.rglob(".DS_Store"):
        ds_store.unlink()


def build_pay_frontend() -> None:
    if not PAY_FRONTEND_DIR.exists():
        raise RuntimeError(f"pay-fronted directory not found: {PAY_FRONTEND_DIR}")

    remove_directory(BUILD_TMP_DIR)
    try:
        subprocess.run(
            [
                find_pnpm(),
                "build",
                "--outDir",
                str(BUILD_TMP_DIR),
                "--emptyOutDir",
            ],
            cwd=PAY_FRONTEND_DIR,
            check=True,
        )
        delete_ds_store_files(BUILD_TMP_DIR)
        remove_directory(STATIC_PAY_DIR)
        shutil.move(str(BUILD_TMP_DIR), str(STATIC_PAY_DIR))
    finally:
        if BUILD_TMP_DIR.exists():
            remove_directory(BUILD_TMP_DIR)


def main() -> int:
    try:
        build_pay_frontend()
    except RuntimeError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1

    sys.stdout.write(f"pay-fronted built into {STATIC_PAY_DIR}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
