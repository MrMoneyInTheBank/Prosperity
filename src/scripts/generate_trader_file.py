import re
import subprocess
import tempfile
import typing as t
from datetime import datetime
from pathlib import Path

from src.config.constants import (
    PRODUCT_TRADERS_DIR,
    TRADER_FILE,
    TRADER_FOOTER_FILE,
    TRADER_HEADER_FILE,
    TRADERS_HISTORY_DIR,
)

IMPORT_RE: t.Final[re.Pattern[str]] = re.compile(
    r"^\s*(import\s.+|from\s.+import\s.+)$"
)
CONST_RE: t.Final[re.Pattern[str]] = re.compile(r"^[A-Z_][A-Z0-9_]*\s*=")


def gather_files(directory: Path) -> list[Path]:
    return sorted(
        [f for f in directory.glob("*.py") if f.name != "__init__.py"],
        key=lambda f: f.name,
    )


def split_sections(file_path: Path) -> tuple[list[str], list[str]]:
    consts: list[str] = []
    body: list[str] = []

    with open(file_path, "r") as f:
        lines = f.readlines()

        for line in lines:
            if IMPORT_RE.match(line):
                continue
            elif CONST_RE.match(line):
                consts.append(line)
            else:
                body.append(line)

    return consts, body


def generate_trader_submission_file_content(
    product_traders_dir: Path,
    trader_header_file: Path,
    trader_footer_file: Path,
) -> tuple[str, str]:
    all_consts: list[str] = []
    all_bodies: list[str] = []

    now: datetime = datetime.now()
    timestamp: str = now.strftime("%Y-%m-%d %H:%M:%S")
    ret_timestamp: str = now.strftime("%Y%m%d_%H%M%S")

    for file_path in gather_files(product_traders_dir):
        consts, body = split_sections(file_path)

        all_consts.extend(consts)
        all_bodies.extend(body)

    lines: list[str] = []

    lines.append("# =========================================\n")
    lines.append("# Auto-generated code for trader.py\n")
    lines.append(f"# Generated on {timestamp}\n")
    lines.append("# =========================================\n\n")

    with open(trader_header_file, "r") as f_header:
        lines.extend(f_header.readlines())
        lines.append("\n\n")

    lines.extend(all_consts)
    lines.append("\n\n")

    lines.extend(all_bodies)
    lines.append("\n\n")

    with open(trader_footer_file, "r") as f_footer:
        lines.extend(f_footer.readlines())
        lines.append("\n\n")

    lines.append("# End of auto-generated trader.py\n")

    return "".join(lines), ret_timestamp


def format_content(content: str) -> str:
    try:
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(content.encode())

        subprocess.run(
            ["ruff", "check", str(tmp_path), "--fix", "--select", "I"],
            check=True,
        )
        subprocess.run(["black", str(tmp_path)], check=True)

        formatted = tmp_path.read_text()
        tmp_path.unlink()

        return formatted

    except FileNotFoundError:
        print("Warning: ruff or black not installed; skipping formatting.")
        return content


def should_generate_file(content: str, trader_file_path: Path) -> bool:
    if not trader_file_path.exists():
        return True

    def normalize(content: str) -> str:
        lines = content.splitlines()
        return "\n".join(lines[4:])

    return normalize(trader_file_path.read_text()) != normalize(content)


def write_to_file(content: str, filepath: Path) -> None:
    with open(filepath, "w") as f:
        f.write(content)


def write_to_history(content: str, parent_dir: Path, timestamp: str) -> None:
    parent_dir.mkdir(parents=True, exist_ok=True)
    filepath: Path = parent_dir / f"trader_{timestamp}.py"

    write_to_file(content, filepath)


def main() -> None:
    file_content, timestamp = generate_trader_submission_file_content(
        product_traders_dir=PRODUCT_TRADERS_DIR,
        trader_header_file=TRADER_HEADER_FILE,
        trader_footer_file=TRADER_FOOTER_FILE,
    )

    formatted_content = format_content(file_content)

    if should_generate_file(content=formatted_content, trader_file_path=TRADER_FILE):
        write_to_file(content=formatted_content, filepath=TRADER_FILE)
        write_to_history(
            content=formatted_content,
            parent_dir=TRADERS_HISTORY_DIR,
            timestamp=timestamp,
        )
    else:
        print("No new changes in product traders, skipping generating trader.py file.")


if __name__ == "__main__":
    main()
