#!/usr/bin/env python3
"""Check code header files for incomplete fields.

This script scans files with @codex-header: v1 markers and identifies
files with TODO in fields that should have been auto-populated by the
annotate_code_headers.py script.

Usage:
    python check_incomplete_headers.py <files-or-dirs> --root <repo-root>

The script will output:
- Files with TODO in auto-populated fields (Key types, Key funcs, Entrypoints, Index)
- These files should be re-processed by annotate_code_headers.py
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

CODEX_MARKER = "@codex-header: v1"
HEADER_LINES = 20

# Fields that should be auto-populated by the script
# If these contain "TODO", it indicates incomplete processing
# Note: Key types and Index are optional - they remain "TODO" if empty
AUTO_POPULATED_FIELDS = {
    "Key funcs:",
    "Entrypoints:",
}

# Fields that legitimately start with TODO (require manual/AI filling)
MANUAL_FIELDS = {
    "Public API:",
    "Inputs/Outputs:",
    "Core flow:",
    "Dependencies:",
    "Error handling:",
    "Config/env:",
    "Side effects:",
    "Performance:",
    "Security:",
    "Tests:",
    "Known issues:",
}

# Regex patterns for detecting function definitions and entrypoints
_RE_PY_DEF = re.compile(r"^\s*def\s+([A-Za-z_]\w*)\s*\(")
_RE_PY_CLASS = re.compile(r"^\s*class\s+([A-Za-z_]\w*)\s*[\(:]")
_RE_JS_FN = re.compile(
    r"^\s*export\s+function\s+([A-Za-z_$][\w$]*)\s*\(|^\s*function\s+([A-Za-z_$][\w$]*)\s*\(|^\s*export\s+const\s+([A-Za-z_$][\w$]*)\s*=\s*\(|^\s*const\s+([A-Za-z_$][\w$]*)\s*=\s*\("
)
_RE_GO_FUNC = re.compile(r"^\s*func\s+\(?[A-Za-z_*\w]*\)?\s*([A-Za-z_]\w*)\s*\(")
_RE_RS_FN = re.compile(r"^\s*(?:pub\s+)?fn\s+([A-Za-z_]\w*)\s*\(")


def _extract_header_lines(lines: List[str]) -> List[str]:
    """Extract the 20-line header from a file if it exists."""
    # Skip prolog (shebang, encoding cookie, etc.)
    i = 0
    if lines and lines[0].startswith("#!"):
        i = 1
    if i < len(lines) and re.match(r"^#.*coding[:=]\s*[-\w.]+", lines[i]):
        i += 1

    # Check for marker in next HEADER_LINES lines
    scan_end = min(i + HEADER_LINES, len(lines))
    scan_text = "".join(lines[i:scan_end])

    if CODEX_MARKER not in scan_text:
        return []

    # Extract the header lines
    header_start = i
    header_end = min(header_start + HEADER_LINES, len(lines))
    return lines[header_start:header_end]


def _strip_comment_prefix(line: str, style: str) -> str:
    """Remove comment prefix from a line."""
    line = line.rstrip()

    if style == "line":
        # Remove "# " or similar
        if line.startswith("#"):
            line = line.lstrip("#").lstrip()
    elif style == "block":
        # Remove " * " or similar
        line = line.replace("/*", "").replace("*/", "").lstrip("*").lstrip()
    elif style == "html":
        # Remove "  " from HTML comments
        line = line.lstrip()

    return line


def _detect_comment_style(line: str) -> str:
    """Detect comment style from first line of header."""
    line = line.strip()
    if line.startswith("#"):
        return "line"
    elif line.startswith("/*"):
        return "block"
    elif line.startswith("<!--"):
        return "html"
    elif line.startswith("--"):
        return "line"
    return "line"  # default


def _has_functions(path: Path, suffix: str) -> bool:
    """Check if file has function definitions."""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()
    except Exception:
        return False

    # Skip header (prolog + 20 lines)
    prolog_lines = 0
    if lines and lines[0].startswith("#!"):
        prolog_lines = 1
    if prolog_lines < len(lines) and re.match(
        r"^#.*coding[:=]\s*[-\w.]+", lines[prolog_lines]
    ):
        prolog_lines += 1

    header_start = prolog_lines
    header_end = min(header_start + HEADER_LINES, len(lines))
    body_lines = lines[header_end:]

    # Check for function definitions
    for line in body_lines:
        if len(line) > 5000:
            continue

        if suffix in {".py", ".pyi"}:
            if _RE_PY_DEF.match(line):
                return True
        elif suffix in {".js", ".jsx", ".ts", ".tsx"}:
            if _RE_JS_FN.match(line):
                return True
        elif suffix == ".go":
            if _RE_GO_FUNC.match(line):
                return True
        elif suffix == ".rs":
            if _RE_RS_FN.match(line):
                return True
        elif suffix in {".java", ".kt"}:
            if "def " in line and "void" not in line:  # Simple check
                return True

    return False


def _has_entrypoint(path: Path, suffix: str) -> bool:
    """Check if file has entrypoint (e.g., if __name__ == '__main__')."""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return False

    if suffix in {".py", ".pyi"}:
        return "__main__" in content
    elif suffix in {".js", ".jsx", ".ts", ".tsx"}:
        return "export default" in content or "export {" in content
    elif suffix == ".rs":
        return "fn main()" in content
    elif suffix == ".go":
        return "func main()" in content

    return False


def _check_header_incomplete(
    header_lines: List[str], path: Path
) -> Tuple[bool, List[str]]:
    """Check if header has TODO in auto-populated fields.

    Returns (is_incomplete, list_of_incomplete_fields).
    """
    if not header_lines or len(header_lines) < HEADER_LINES:
        return True, ["No valid header found"]

    suffix = path.suffix.lower()
    style = _detect_comment_style(header_lines[0])
    incomplete_fields: List[str] = []

    for line in header_lines:
        clean_line = _strip_comment_prefix(line, style)

        for field in AUTO_POPULATED_FIELDS:
            if clean_line.startswith(field):
                value = clean_line[len(field) :].strip()

                # Check if the field has TODO
                if value == "TODO" or "TODO" in value:
                    # Verify if the file actually has the content that should be in this field
                    if field == "Key funcs:":
                        if _has_functions(path, suffix):
                            incomplete_fields.append(clean_line)
                    elif field == "Entrypoints:":
                        if _has_entrypoint(path, suffix):
                            incomplete_fields.append(clean_line)

                break

    return len(incomplete_fields) > 0, incomplete_fields


def _iter_files(args_files: List[str]) -> Iterable[Path]:
    """Iterate over files and directories."""
    for f in args_files:
        p = Path(f)
        if p.is_dir():
            for child in p.rglob("*"):
                if child.is_file():
                    yield child
        else:
            yield p


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Check code header files for incomplete auto-populated fields"
    )
    parser.add_argument("files", nargs="+", help="File(s) or directory(ies) to check")
    parser.add_argument(
        "--root", default=".", help="Repo root (used for relative paths)"
    )
    args = parser.parse_args(argv)

    root = Path(args.root)
    incomplete_files: List[Tuple[str, List[str]]] = []

    for path in _iter_files(args.files):
        if not path.exists() or not path.is_file():
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()

            header = _extract_header_lines(lines)
            if not header:
                continue  # No header, skip

            is_incomplete, issues = _check_header_incomplete(header, path)
            if is_incomplete:
                rel_path = path.resolve().relative_to(root.resolve()).as_posix()
                incomplete_files.append((rel_path, issues))
        except Exception as e:
            print(f"error: {path}: {e}", file=sys.stderr)

    # Output results
    if incomplete_files:
        print(f"Found {len(incomplete_files)} file(s) with incomplete headers:")
        print()
        for rel_path, issues in incomplete_files:
            print(f"{rel_path}:")
            for issue in issues:
                print(f"  - {issue}")
        print()
        print("To fix these files, run:")
        print("  python annotate_code_headers.py <files> --root <repo-root>")
        return 1
    else:
        print("All headers are complete!")
        return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
