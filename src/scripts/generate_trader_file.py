from datetime import datetime
from pathlib import Path
import re
import typing as t
import subprocess

from src.config.constants import (
    PRODUCT_TRADERS_DIR,
    TRADER_FILE,
    TRADER_HEADER_FILE,
    TRADER_FOOTER_FILE,
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


def generate_trader_submission_file(
    product_traders_dir: Path,
    trader_file_path: Path,
    trader_header_file: Path,
    trader_footer_file: Path,
) -> None:
    all_consts: list[str] = []
    all_bodies: list[str] = []

    now: datetime = datetime.now()
    timestamp: str = now.strftime("%Y-%m-%d %H:%M:%S")

    for file_path in gather_files(product_traders_dir):
        consts, body = split_sections(file_path)

        all_consts.extend(consts)
        all_bodies.extend(body)

    with open(trader_file_path, "w") as f:
        f.write("# =========================================\n")
        f.write("# Auto-generated code for trader.py\n")
        f.write(f"# Generated on {timestamp}\n")
        f.write("# =========================================\n\n")

        with open(trader_header_file, "r") as f_header:
            f.writelines(f_header.readlines())
            f.write("\n\n")

        f.writelines(all_consts)
        if all_consts:
            f.write("\n\n")

        f.writelines(all_bodies)

        f.write("\n\n")

        with open(trader_footer_file, "r") as f_footer:
            f.writelines(f_footer.readlines())
            f.write("\n")

        f.write("\n# End of auto-generated trader.py\n")

    try:
        subprocess.run(
            ["ruff", "check", str(trader_file_path), "--fix", "--select", "I"],
            check=True,
        )
        subprocess.run(["black", trader_file_path])
    except FileNotFoundError:
        print("Warning: ruff or black not installed; skipping formatting.")


def main() -> None:
    generate_trader_submission_file(
        product_traders_dir=PRODUCT_TRADERS_DIR,
        trader_file_path=TRADER_FILE,
        trader_header_file=TRADER_HEADER_FILE,
        trader_footer_file=TRADER_FOOTER_FILE,
    )


if __name__ == "__main__":
    main()
