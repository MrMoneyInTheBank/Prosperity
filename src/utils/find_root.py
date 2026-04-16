from pathlib import Path


def find_project_root(start: Path) -> Path:
    from src.config.constants import GIT_DIR_NAME, TOML_FILE_NAME

    for path in [start, *start.parents]:
        if (path / TOML_FILE_NAME).exists() or (path / GIT_DIR_NAME).exists():
            return path
    raise RuntimeError("Prosperity project root not found.")
