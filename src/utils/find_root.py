from pathlib import Path
import typing as t

TOML_FILE_NAME: t.Final[str] = "pyproject.toml"
GIT_DIR_NAME: t.Final[str] = ".git"


def find_project_root(start: Path) -> Path:
    for path in [start, *start.parents]:
        if (path / TOML_FILE_NAME).exists() or (path / GIT_DIR_NAME).exists():
            return path
    raise RuntimeError("Prosperity project root not found.")
