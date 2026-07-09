# ruff: noqa: INP001
from __future__ import annotations

import os
import sys
from pathlib import Path

import environ
from django.core.management import execute_from_command_line

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_env_file() -> None:
    env_file = Path(os.environ.get("ENV_FILE", ".env"))
    if env_file.exists():
        environ.Env.read_env(env_file)


def set_default_environment() -> None:
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    os.environ.setdefault("POSTGRES_HOST", "127.0.0.1")
    os.environ.setdefault("POSTGRES_PORT", "5432")
    os.environ.setdefault("REDIS_HOST", "127.0.0.1")
    os.environ.setdefault("REDIS_PORT", "6379")
    os.environ.setdefault("POSTGRES_PASSWORD", "postgres")


def main() -> None:
    load_env_file()
    set_default_environment()
    execute_from_command_line([sys.argv[0], *sys.argv[1:]])


if __name__ == "__main__":
    main()
