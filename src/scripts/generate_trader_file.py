from datetime import datetime
from pathlib import Path
import re
import typing as t

from src.config.constants import PRODUCT_TRADERS_DIR, TRADER_FILE

IMPORT_RE: t.Final[re.Pattern[str]] = re.compile(
    r"^\s*(import\s.+|from\s.+import\s.+)$"
)
CONST_RE: t.Final[re.Pattern[str]] = re.compile(r"^[A-Z_][A-Z0-9_]*\s*=")


def gather_files(directory: Path) -> list[Path]:
    return [f for f in directory.glob("*.py") if f.name != "__init__.py"]


def split_sections(file_path: Path) -> tuple[list[str], list[str], list[str]]:
    imports: list[str] = []
    consts: list[str] = []
    body: list[str] = []

    with open(file_path, "r") as f:
        lines = f.readlines()

        for line in lines:
            if IMPORT_RE.match(line):
                imports.append(line)
            elif CONST_RE.match(line):
                consts.append(line)
            else:
                body.append(line)

    return imports, consts, body


def generate_trader_submission_file(
    product_traders_dir: Path, trader_file_path: Path
) -> None:
    all_imports: set[str] = set()
    all_consts: list[str] = []
    all_bodies: list[str] = []

    now: datetime = datetime.now()
    timestamp: str = now.strftime("%Y-%m-%d %H:%M:%S")

    for file_path in gather_files(product_traders_dir):
        imports, consts, body = split_sections(file_path)

        all_imports.update(imports)
        all_consts.extend(consts)
        all_bodies.extend(body)

    with open(trader_file_path, "w") as f:
        f.write("# =========================================\n")
        f.write("# Auto-generated starter code for trader.py\n")
        f.write(f"# Generated on {timestamp}\n")
        f.write("# Source: all files in product_traders/\n")
        f.write("# =========================================\n\n")

        f.writelines(sorted(all_imports))
        if all_imports:
            f.write("\n\n")

        f.writelines(all_consts)
        if all_consts:
            f.write("\n\n")

        f.writelines(all_bodies)

        f.write("\n# End of auto-generated trader.py\n")
        f.write("\n")


def main() -> None:
    generate_trader_submission_file(
        product_traders_dir=PRODUCT_TRADERS_DIR, trader_file_path=TRADER_FILE
    )


if __name__ == "__main__":
    main()
