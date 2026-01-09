#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as _dt
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


CODEX_MARKER = "@codex-header: v1"
DEFAULT_MAX_WIDTH = 120
HEADER_LINES = 20
MAX_INHERIT_EDGES = 6


@dataclass(frozen=True)
class CommentStyle:
    kind: str  # "line" | "block" | "py-docstring"
    line_prefix: str = ""
    block_start: str = ""
    block_line_prefix: str = ""
    block_end: str = ""
    docstring_quote: str = ""


COMMENT_STYLES_BY_SUFFIX = {
    # Python: keep module docstring semantics intact by using line comments (docstring, if present,
    # remains the first statement because comments are ignored by the parser).
    ".py": CommentStyle(kind="line", line_prefix="# "),
    ".pyi": CommentStyle(kind="line", line_prefix="# "),
    # Shell-like
    ".sh": CommentStyle(kind="line", line_prefix="# "),
    ".bash": CommentStyle(kind="line", line_prefix="# "),
    ".zsh": CommentStyle(kind="line", line_prefix="# "),
    ".fish": CommentStyle(kind="line", line_prefix="# "),
    ".ps1": CommentStyle(kind="line", line_prefix="# "),
    # Ruby / YAML
    ".rb": CommentStyle(kind="line", line_prefix="# "),
    ".yml": CommentStyle(kind="line", line_prefix="# "),
    ".yaml": CommentStyle(kind="line", line_prefix="# "),
    # SQL / Lua
    ".sql": CommentStyle(kind="line", line_prefix="-- "),
    ".lua": CommentStyle(kind="line", line_prefix="-- "),
    # C-like / JS-like (block comment)
    ".c": CommentStyle(
        kind="block", block_start="/*", block_line_prefix=" * ", block_end=" */"
    ),
    ".h": CommentStyle(
        kind="block", block_start="/*", block_line_prefix=" * ", block_end=" */"
    ),
    ".cc": CommentStyle(
        kind="block", block_start="/*", block_line_prefix=" * ", block_end=" */"
    ),
    ".cpp": CommentStyle(
        kind="block", block_start="/*", block_line_prefix=" * ", block_end=" */"
    ),
    ".hpp": CommentStyle(
        kind="block", block_start="/*", block_line_prefix=" * ", block_end=" */"
    ),
    ".cs": CommentStyle(
        kind="block", block_start="/*", block_line_prefix=" * ", block_end=" */"
    ),
    ".java": CommentStyle(
        kind="block", block_start="/*", block_line_prefix=" * ", block_end=" */"
    ),
    ".kt": CommentStyle(
        kind="block", block_start="/*", block_line_prefix=" * ", block_end=" */"
    ),
    ".swift": CommentStyle(
        kind="block", block_start="/*", block_line_prefix=" * ", block_end=" */"
    ),
    ".js": CommentStyle(
        kind="block", block_start="/*", block_line_prefix=" * ", block_end=" */"
    ),
    ".jsx": CommentStyle(
        kind="block", block_start="/*", block_line_prefix=" * ", block_end=" */"
    ),
    ".ts": CommentStyle(
        kind="block", block_start="/*", block_line_prefix=" * ", block_end=" */"
    ),
    ".tsx": CommentStyle(
        kind="block", block_start="/*", block_line_prefix=" * ", block_end=" */"
    ),
    ".go": CommentStyle(
        kind="block", block_start="/*", block_line_prefix=" * ", block_end=" */"
    ),
    ".rs": CommentStyle(
        kind="block", block_start="/*", block_line_prefix=" * ", block_end=" */"
    ),
    ".php": CommentStyle(
        kind="block", block_start="/*", block_line_prefix=" * ", block_end=" */"
    ),
    ".css": CommentStyle(
        kind="block", block_start="/*", block_line_prefix=" * ", block_end=" */"
    ),
    ".scss": CommentStyle(
        kind="block", block_start="/*", block_line_prefix=" * ", block_end=" */"
    ),
    ".less": CommentStyle(
        kind="block", block_start="/*", block_line_prefix=" * ", block_end=" */"
    ),
    # HTML/XML
    ".html": CommentStyle(
        kind="block", block_start="<!--", block_line_prefix="  ", block_end="-->"
    ),
    ".htm": CommentStyle(
        kind="block", block_start="<!--", block_line_prefix="  ", block_end="-->"
    ),
    ".xml": CommentStyle(
        kind="block", block_start="<!--", block_line_prefix="  ", block_end="-->"
    ),
    ".vue": CommentStyle(
        kind="block", block_start="<!--", block_line_prefix="  ", block_end="-->"
    ),
}


SKIP_SUFFIXES = {
    ".json",
    ".lock",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".zip",
    ".gz",
    ".bz2",
    ".xz",
    ".7z",
    ".jar",
    ".class",
    ".wasm",
}


def _detect_comment_style(path: Path) -> Optional[CommentStyle]:
    suffix = path.suffix.lower()
    if suffix in SKIP_SUFFIXES:
        return None
    return COMMENT_STYLES_BY_SUFFIX.get(suffix)


def _truncate(s: str, max_width: int) -> str:
    s = re.sub(r"\s+", " ", s.strip())
    if len(s) <= max_width:
        return s
    if max_width <= 1:
        return s[:max_width]
    return s[: max_width - 1].rstrip() + "…"


def _relpath_for_header(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def _split_prolog(lines: List[str], *, suffix: str) -> Tuple[List[str], List[str]]:
    """
    Return (prolog_lines, rest_lines).

    Prolog lines are those that must remain at the very top to preserve semantics:
    - shebang lines (#!...)
    - Python encoding cookie
    - Go build tags
    - XML declaration
    - Rust inner attributes (#![...])
    """
    if not lines:
        return [], []

    prolog: List[str] = []
    i = 0

    # Shebang must be the first line.
    if lines[0].startswith("#!"):
        prolog.append(lines[0])
        i = 1

    # XML declaration should remain first non-shebang.
    if i < len(lines) and lines[i].lstrip().startswith("<?xml"):
        prolog.append(lines[i])
        i += 1

    # Python encoding cookie (PEP 263) must be in first/second line (ignoring shebang).
    if suffix in {".py", ".pyi"}:
        if i < len(lines) and re.match(r"^#.*coding[:=]\s*[-\w.]+", lines[i]):
            prolog.append(lines[i])
            i += 1

    # Go build tags must be at the top of file before other content.
    # Keep consecutive build-tag lines and ensure there is a blank line after them.
    if i < len(lines) and (
        lines[i].startswith("//go:build") or lines[i].startswith("// +build")
    ):
        while i < len(lines) and (
            lines[i].startswith("//go:build") or lines[i].startswith("// +build")
        ):
            prolog.append(lines[i])
            i += 1
        if i < len(lines) and lines[i].strip() == "":
            prolog.append(lines[i])
            i += 1
        else:
            prolog.append("\n")

    # Rust inner attributes should remain before module items.
    if i < len(lines) and lines[i].lstrip().startswith("#!["):
        while i < len(lines) and lines[i].lstrip().startswith("#!["):
            prolog.append(lines[i])
            i += 1
        if i < len(lines) and lines[i].strip() == "":
            prolog.append(lines[i])
            i += 1

    return prolog, lines[i:]


def _split_existing_codex_header(
    rest: List[str], path: Path
) -> Tuple[Optional[List[str]], List[str], bool]:
    """
    If an existing 20-line Codex header is present at the start of `rest`, return:
      (header_lines, rest_without_header, True)

    Otherwise return:
      (None, rest, False)
    """
    max_scan = min(len(rest), 60)
    scan_lines = rest[:max_scan]
    scan = "".join(scan_lines)
    if CODEX_MARKER not in scan:
        return None, rest, False

    # If marker is present, only accept the invariant "header is the first 20 lines of rest".
    if len(rest) < HEADER_LINES:
        raise ValueError(
            f"found {CODEX_MARKER} but file is shorter than {HEADER_LINES} lines"
        )

    if any(CODEX_MARKER in ln for ln in rest[:HEADER_LINES]):
        return rest[:HEADER_LINES], rest[HEADER_LINES:], True

    # Marker exists near top but not where we expect -> refuse to avoid duplicating headers.
    raise ValueError(
        f"found {CODEX_MARKER} near top but header is not the first {HEADER_LINES} lines; "
        f"manually normalize the header in {path}"
    )


# ============================================================================
# AGENTS.md Generation Functions
# ============================================================================

AGENTS_MD_TEMPLATE = """# Code Navigation Guide

> **IMPORTANT**: This project uses codex-header annotations (20-line file headers) for efficient AI navigation.
> **DO NOT** read entire files at once. Follow the pattern below to reduce context bloat.

## Reading Pattern (MUST FOLLOW)

When you need to understand or modify any source file:

1. **READ FIRST 20 LINES ONLY** - Contains file overview, purpose, key types, functions, and inheritance
2. **USE LINE REFERENCES** - Jump directly to specific locations using `@L<line-number>` syntax
3. **READ FULL FILE ONLY WHEN**: You need to see implementation details for the specific function/class you're working on

## Example Workflow

**Instead of reading**:
```
User: "How does authentication work?"
AI: [reads entire auth.py file - 500 lines]
```

**Do this**:
```
User: "How does authentication work?"
AI: [reads first 20 lines of auth.py]
   → Sees "Key types: AuthService@L45, TokenHandler@L89"
   → Reads AuthService@L45 to understand the main class
   → Reads TokenHandler@L89 if needed
```

## File Structure Overview

```
project-root/
├── src/                  # Source code
├── tests/                # Test files
├── scripts/              # Build/utility scripts
└── AGENTS.md            # This file - DO NOT REMOVE
```

## Navigation Syntax Reference

- `ClassName@L45` - Jump to line 45 (class definition)
- `function_name@L123` - Jump to line 123 (function definition)
- `Child@L..->Base@L..` - Inheritance relationship
- `Type@path/to/file.py#L..` - Cross-file reference

## Why This Format?

- **Faster context building**: 20 lines vs 500+ lines
- **Better accuracy**: Focus on structure before details
- **Efficient updates**: Headers stay in sync with code
- **Team readable**: Human developers can also use this pattern

---

*Last updated: {date}*
*Generated by: code-header-annotator skill*
"""


def _generate_agents_md_index(
    annotated_files: List[Tuple[Path, str, str, str]], root: Path
) -> str:
    """Generate the index table for AGENTS.md"""
    if not annotated_files:
        return ""

    lines = []
    for path, purpose, types, funcs in sorted(annotated_files, key=lambda x: str(x[0])):
        relpath = _relpath_for_header(path, root)

        # Truncate long purposes
        purpose_short = _truncate(purpose, 60) if purpose else "TODO"

        # Build key content summary
        key_content = []
        if types and types != "TODO":
            key_content.append(f"Types: {types}")
        if funcs and funcs != "TODO":
            key_content.append(f"Funcs: {funcs}")
        key_content_str = "; ".join(key_content) if key_content else "-"

        lines.append(f"| `{relpath}` | {purpose_short} | {key_content_str} |")

    return "\n".join(lines)


def _update_agents_md(
    root: Path, annotated_files: List[Tuple[Path, str, str, str]]
) -> bool:
    """
    Update AGENTS.md with indexed files.
    Returns True if file was created/updated, False otherwise.
    """
    agents_md_path = root / "AGENTS.md"

    # Generate index content
    index_content = _generate_agents_md_index(annotated_files, root)

    if index_content:
        marker_start = "<!-- CODEX_HEADER_INDEX_START -->"
        marker_end = "<!-- CODEX_HEADER_INDEX_END -->"

        # If file exists, try to preserve content before the markers
        existing_pre_content = ""
        existing_post_content = ""

        if agents_md_path.exists():
            existing_content = agents_md_path.read_text(encoding="utf-8")
            if marker_start in existing_content and marker_end in existing_content:
                # Split around the markers
                pre_match = existing_content.split(marker_start)[0]
                post_match = existing_content.split(marker_end)[1]
                existing_pre_content = pre_match
                existing_post_content = post_match

        # Build new content
        today = _dt.date.today().isoformat()
        new_content = AGENTS_MD_TEMPLATE.format(date=today)

        # If we have existing content, preserve the structure
        if existing_pre_content or existing_post_content:
            # Keep everything before marker_start
            final_content = existing_pre_content + marker_start + "\n"
            final_content += (
                "<!-- This section is auto-generated by code-header-annotator -->\n"
            )
            final_content += "<!-- DO NOT EDIT MANUALLY -->\n\n"
            final_content += "| File | Purpose | Key Content |\n"
            final_content += "|------|---------|-------------|\n"
            final_content += index_content + "\n"
            final_content += marker_end + existing_post_content
        else:
            # New file - just use the template with index inserted
            # Insert index before the "## File Structure Overview" section
            section_marker = "## File Structure Overview"
            if section_marker in new_content:
                index_section = "\n## Annotated Files Index\n\n"
                index_section += "<!-- CODEX_HEADER_INDEX_START -->\n"
                index_section += (
                    "<!-- This section is auto-generated by code-header-annotator -->\n"
                )
                index_section += "<!-- DO NOT EDIT MANUALLY -->\n\n"
                index_section += "| File | Purpose | Key Content |\n"
                index_section += "|------|---------|-------------|\n"
                index_section += index_content + "\n"
                index_section += "<!-- CODEX_HEADER_INDEX_END -->\n"
                new_content = new_content.replace(
                    section_marker, index_section + section_marker
                )

        # Write the file
        agents_md_path.write_text(new_content, encoding="utf-8")
        return True

    return False


_HEADER_FIELD_PREFIXES: Tuple[str, ...] = (
    "Path:",
    "Purpose:",
    "Key types:",
    "Inheritance:",
    "Key funcs:",
    "Entrypoints:",
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
    "Index:",
    "Last update:",
)

_RE_HEADER_PREFIX = re.compile(r"^\s*(?:/\*+|<!--)?\s*(?:\*+\s*)?(?:#|//|--)?\s*")
_RE_HEADER_SUFFIX = re.compile(r"\s*(?:\*/|-->)\s*$")


def _strip_header_comment_syntax(line: str) -> str:
    s = line.rstrip("\n").rstrip("\r")
    s = _RE_HEADER_SUFFIX.sub("", s)
    s = _RE_HEADER_PREFIX.sub("", s)
    return s.strip()


def _parse_existing_header_fields(header_lines: List[str]) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    for ln in header_lines:
        clean = _strip_header_comment_syntax(ln)
        for prefix in _HEADER_FIELD_PREFIXES:
            if clean.startswith(prefix):
                key = prefix[:-1]  # drop trailing ':'
                fields[key] = clean[len(prefix) :].strip()
                break
    return fields


def _is_placeholder(value: Optional[str]) -> bool:
    if value is None:
        return True
    v = value.strip()
    if not v:
        return True
    if v == "TODO":
        return True
    if v.startswith("TODO "):
        return True
    if v.startswith("TODO:"):
        return True
    if v.startswith("TODO;"):
        return True
    return False


def _peek_py_module_docstring(lines: List[str]) -> Optional[str]:
    """
    Read (but do not remove) the module docstring if it's the first statement.
    This runs on content *after prolog*.
    """
    i = 0
    while i < len(lines) and lines[i].strip() == "":
        i += 1
    if i >= len(lines):
        return None

    opener = lines[i].lstrip()
    quote = None
    if opener.startswith('"""'):
        quote = '"""'
    elif opener.startswith("'''"):
        quote = "'''"
    if quote is None:
        return None

    # Single-line docstring.
    if opener.count(quote) >= 2 and opener.strip() != quote:
        content = opener.split(quote, 2)[1]
        return _truncate(content, 300)

    collected: List[str] = []
    for idx in range(i + 1, min(len(lines), i + 2000)):
        ln = lines[idx]
        if quote in ln:
            return _truncate("\n".join(collected), 300)
        collected.append(ln.rstrip("\n"))
    return None


_RE_PY_DEF = re.compile(r"^\s*def\s+([A-Za-z_]\w*)\s*\(")
_RE_PY_CLASS = re.compile(r"^\s*class\s+([A-Za-z_]\w*)\s*[\(:]")
_RE_PY_INHERIT = re.compile(r"^\s*class\s+([A-Za-z_]\w*)\s*\(([^)]*)\)\s*:")
_RE_JS_CLASS = re.compile(
    r"^\s*export\s+default\s+class\s+([A-Za-z_$][\w$]*)\b|^\s*export\s+class\s+([A-Za-z_$][\w$]*)\b|^\s*class\s+([A-Za-z_$][\w$]*)\b"
)
_RE_JS_INHERIT = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+([A-Za-z_$][\w$]*)\s+extends\s+([A-Za-z_$][\w$]*)"
)
_RE_TS_CLASS = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+([A-Za-z_$][\w$]*)\b"
)
_RE_TS_INTERFACE = re.compile(r"^\s*(?:export\s+)?interface\s+([A-Za-z_$][\w$]*)\b")
_RE_TS_ENUM = re.compile(r"^\s*(?:export\s+)?enum\s+([A-Za-z_$][\w$]*)\b")
_RE_TS_TYPE_ALIAS = re.compile(r"^\s*(?:export\s+)?type\s+([A-Za-z_$][\w$]*)\b")
_RE_TS_IMPLEMENTS = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+([A-Za-z_$][\w$]*)\b(?:\s+extends\s+[A-Za-z_$][\w$]*)?\s+implements\s+([^{]+)"
)
_RE_JS_FN = re.compile(
    r"^\s*export\s+function\s+([A-Za-z_$][\w$]*)\s*\(|^\s*function\s+([A-Za-z_$][\w$]*)\s*\(|^\s*export\s+const\s+([A-Za-z_$][\w$]*)\s*=\s*\(|^\s*const\s+([A-Za-z_$][\w$]*)\s*=\s*\("
)
_RE_GO_TYPE = re.compile(r"^\s*type\s+([A-Za-z_]\w*)\s+(struct|interface)\b")
_RE_GO_FUNC = re.compile(r"^\s*func\s+\(?[A-Za-z_*\w]*\)?\s*([A-Za-z_]\w*)\s*\(")
_RE_RS_ITEM = re.compile(r"^\s*(?:pub\s+)?(struct|enum|trait)\s+([A-Za-z_]\w*)\b")
_RE_RS_FN = re.compile(r"^\s*(?:pub\s+)?fn\s+([A-Za-z_]\w*)\s*\(")
_RE_RS_IMPL_FOR = re.compile(
    r"^\s*impl\s+(?:<[^>]+>\s+)?([A-Za-z_]\w*)\s+for\s+([A-Za-z_]\w*)\b"
)
_RE_JAVA_TYPE = re.compile(
    r"^\s*(?:public|protected|private)?\s*(?:abstract|final)?\s*(class|interface|enum)\s+([A-Za-z_]\w*)\b"
)
_RE_JAVA_INHERIT = re.compile(
    r"^\s*(?:public|protected|private)?\s*(?:abstract|final)?\s*class\s+([A-Za-z_]\w*)\s+extends\s+([A-Za-z_]\w*)\b"
)
_RE_JAVA_IMPLEMENTS = re.compile(
    r"^\s*(?:public|protected|private)?\s*(?:abstract|final)?\s*class\s+([A-Za-z_]\w*)\b(?:\s+extends\s+[A-Za-z_]\w*)?\s+implements\s+([^{]+)"
)
_RE_JAVA_INTERFACE_EXTENDS = re.compile(
    r"^\s*(?:public|protected|private)?\s*interface\s+([A-Za-z_]\w*)\s+extends\s+([^{]+)"
)
_RE_CS_INHERIT = re.compile(
    r"^\s*(?:public|protected|private|internal)?\s*(?:abstract|sealed|static|partial)?\s*class\s+([A-Za-z_]\w*)\s*:\s*([A-Za-z_]\w*)"
)
_RE_CS_SUPERTYPES = re.compile(
    r"^\s*(?:public|protected|private|internal)?\s*(?:abstract|sealed|static|partial)?\s*(class|interface|struct)\s+([A-Za-z_]\w*)\s*:\s*([^{]+)"
)
_RE_KT_INHERIT = re.compile(
    r"^\s*(?:public|protected|private|internal)?\s*(?:open|abstract|sealed|data)?\s*class\s+([A-Za-z_]\w*)\s*:\s*([A-Za-z_]\w*)"
)
_RE_KT_SUPERTYPES = re.compile(
    r"^\s*(?:public|protected|private|internal)?\s*(?:open|abstract|sealed|data)?\s*(class|interface)\s+([A-Za-z_]\w*)\s*:\s*([^{]+)"
)
_RE_C_LIKE_FN = re.compile(r"^\s*[A-Za-z_][\w\s\*]+\s+([A-Za-z_]\w*)\s*\([^;]*\)\s*\{")


def _clean_base_name(s: str) -> str:
    s = s.strip()
    if not s:
        return ""
    # Strip generics / calls like Base<T> or Base().
    s = re.split(r"[<(]", s, maxsplit=1)[0].strip()
    # Strip module prefix like pkg.Base -> Base
    if "." in s:
        s = s.rsplit(".", 1)[-1]
    return s


def _split_supertype_list(raw: str) -> List[str]:
    # Stop at common delimiters (opening brace, where-clause, etc.) and split by commas.
    raw = raw.strip()
    raw = raw.split("{", 1)[0].strip()
    raw = raw.split("where", 1)[0].strip()
    if not raw:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]


def _resolve_type_ref(
    name: str,
    *,
    type_line_by_name: dict[str, int],
    type_index: Optional[dict[str, List[Tuple[str, int]]]],
) -> str:
    in_file_ln = type_line_by_name.get(name)
    if in_file_ln is not None:
        return f"{name}@L{in_file_ln}"

    if type_index is None:
        return name

    matches = type_index.get(name) or []
    if len(matches) != 1:
        return name

    relpath, ln = matches[0]
    return f"{name}@{relpath}#L{ln}"


def _extract_inheritance(
    path: Path,
    body_lines: List[str],
    final_body_offset: int,
    *,
    type_index: Optional[dict[str, List[Tuple[str, int]]]] = None,
) -> List[str]:
    suffix = path.suffix.lower()

    # Map of type name -> line number (final-file line numbers)
    type_line_by_name: dict[str, int] = {}
    for idx, line in enumerate(body_lines, start=1):
        if suffix in {".py", ".pyi"}:
            m = _RE_PY_CLASS.match(line)
            if m:
                type_line_by_name[m.group(1)] = final_body_offset + idx
        elif suffix in {".js", ".jsx", ".ts", ".tsx"}:
            if suffix in {".ts", ".tsx"}:
                m = (
                    _RE_TS_CLASS.match(line)
                    or _RE_TS_INTERFACE.match(line)
                    or _RE_TS_ENUM.match(line)
                    or _RE_TS_TYPE_ALIAS.match(line)
                )
                if m:
                    type_line_by_name[m.group(1)] = final_body_offset + idx
            else:
                m = _RE_JS_CLASS.match(line)
                if m:
                    name = next((g for g in m.groups() if g), None)
                    if name:
                        type_line_by_name[name] = final_body_offset + idx
        elif suffix in {".java", ".kt"}:
            m = _RE_JAVA_TYPE.match(line)
            if m:
                type_line_by_name[m.group(2)] = final_body_offset + idx
        elif suffix == ".cs":
            # Best-effort: capture basic type declarations.
            m = re.match(
                r"^\s*(?:public|protected|private|internal)?\s*(?:abstract|sealed|static|partial)?\s*(?:class|interface|struct|enum)\s+([A-Za-z_]\w*)\b",
                line,
            )
            if m:
                type_line_by_name[m.group(1)] = final_body_offset + idx

    edges: List[str] = []
    for idx, line in enumerate(body_lines, start=1):
        child = ""
        bases: List[Tuple[str, str]] = []  # (rel, parent_name)
        if suffix in {".py", ".pyi"}:
            m = _RE_PY_INHERIT.match(line)
            if m:
                child = m.group(1)
                raw_bases = [
                    _clean_base_name(p) for p in _split_supertype_list(m.group(2))
                ]
                raw_bases = [b for b in raw_bases if b]
                if raw_bases:
                    bases.append(("->", raw_bases[0]))
                    for extra in raw_bases[1:]:
                        bases.append(("+", extra))
        elif suffix in {".js", ".jsx", ".ts", ".tsx"}:
            m = _RE_JS_INHERIT.match(line)
            if m:
                child = m.group(1)
                bases.append(("->", _clean_base_name(m.group(2))))
            m = _RE_TS_IMPLEMENTS.match(line)
            if m:
                child = m.group(1)
                for iface in [
                    _clean_base_name(p) for p in _split_supertype_list(m.group(2))
                ]:
                    if iface:
                        bases.append(("~>", iface))
        elif suffix == ".java":
            m = _RE_JAVA_INHERIT.match(line)
            if m:
                child = m.group(1)
                bases.append(("->", _clean_base_name(m.group(2))))
            m = _RE_JAVA_IMPLEMENTS.match(line)
            if m:
                child = m.group(1)
                for iface in [
                    _clean_base_name(p) for p in _split_supertype_list(m.group(2))
                ]:
                    if iface:
                        bases.append(("~>", iface))
            m = _RE_JAVA_INTERFACE_EXTENDS.match(line)
            if m:
                child = m.group(1)
                for parent in [
                    _clean_base_name(p) for p in _split_supertype_list(m.group(2))
                ]:
                    if parent:
                        bases.append(("->", parent))
        elif suffix == ".kt":
            m = _RE_KT_SUPERTYPES.match(line)
            if m:
                kind = m.group(1)
                child = m.group(2)
                raw = _split_supertype_list(m.group(3))
                if kind == "interface":
                    for parent in [_clean_base_name(p) for p in raw]:
                        if parent:
                            bases.append(("->", parent))
                else:
                    # Kotlin classes can list a single superclass call and multiple interfaces.
                    raw_clean: List[Tuple[str, str]] = []
                    for p in raw:
                        rel = "~>"
                        if "(" in p and ")" in p:
                            rel = "->"
                        raw_clean.append((rel, _clean_base_name(p)))
                    # Prefer the first "->" as the superclass; treat the rest as "~>".
                    if any(rel == "->" for rel, _ in raw_clean):
                        used_super = False
                        for rel, parent in raw_clean:
                            if not parent:
                                continue
                            if rel == "->" and not used_super:
                                bases.append(("->", parent))
                                used_super = True
                            else:
                                bases.append(("~>", parent))
                    else:
                        for j, (_, parent) in enumerate(raw_clean):
                            if not parent:
                                continue
                            bases.append(("->" if j == 0 else "~>", parent))
        elif suffix == ".cs":
            m = _RE_CS_SUPERTYPES.match(line)
            if m:
                kind = m.group(1)
                child = m.group(2)
                raw = [_clean_base_name(p) for p in _split_supertype_list(m.group(3))]
                raw = [b for b in raw if b]
                if kind == "interface":
                    for parent in raw:
                        bases.append(("->", parent))
                elif kind == "struct":
                    for parent in raw:
                        bases.append(("~>", parent))
                else:
                    if raw:
                        bases.append(("->", raw[0]))
                        for iface in raw[1:]:
                            bases.append(("~>", iface))
        elif suffix == ".rs":
            m = _RE_RS_IMPL_FOR.match(line)
            if m:
                trait = _clean_base_name(m.group(1))
                impl_for = _clean_base_name(m.group(2))
                # Only record edges for local types so `Child@L..` points at an actual definition.
                if impl_for and trait and impl_for in type_line_by_name:
                    child = impl_for
                    bases.append(("~>", trait))

        if not child or not bases:
            continue

        child_ln = final_body_offset + idx
        child_decl_ln = type_line_by_name.get(child, child_ln)
        child_ref = f"{child}@L{child_decl_ln}"
        for rel, parent in bases:
            if not parent:
                continue
            parent_ref = _resolve_type_ref(
                parent, type_line_by_name=type_line_by_name, type_index=type_index
            )
            edges.append(f"{child_ref}{rel}{parent_ref}")
            if len(edges) >= MAX_INHERIT_EDGES:
                return edges

    return edges


def _extract_symbols(
    path: Path, body_lines: List[str], final_body_offset: int
) -> Tuple[List[str], List[str], List[str]]:
    """
    Return (types, funcs, entrypoints) as compact strings like `Name@L123`.
    `final_body_offset` is the number of lines before body in the final file.
    """
    suffix = path.suffix.lower()

    types: List[Tuple[str, int]] = []
    funcs: List[Tuple[str, int]] = []
    entrypoints: List[Tuple[str, int]] = []

    for idx, line in enumerate(body_lines, start=1):
        # Fast path: skip long lines that are obviously data.
        if len(line) > 5000:
            continue

        if suffix in {".py", ".pyi"}:
            m = _RE_PY_CLASS.match(line)
            if m:
                types.append((m.group(1), final_body_offset + idx))
                continue
            m = _RE_PY_DEF.match(line)
            if m:
                name = m.group(1)
                funcs.append((name, final_body_offset + idx))
                continue
            if line.startswith("if __name__") and "__main__" in line:
                entrypoints.append(("__main__", final_body_offset + idx))
        elif suffix in {".js", ".jsx", ".ts", ".tsx"}:
            if suffix in {".ts", ".tsx"}:
                m = (
                    _RE_TS_CLASS.match(line)
                    or _RE_TS_INTERFACE.match(line)
                    or _RE_TS_ENUM.match(line)
                    or _RE_TS_TYPE_ALIAS.match(line)
                )
                if m:
                    types.append((m.group(1), final_body_offset + idx))
                    continue
            else:
                m = _RE_JS_CLASS.match(line)
                if m:
                    name = next((g for g in m.groups() if g), None)
                    if name:
                        types.append((name, final_body_offset + idx))
                    continue
            m = _RE_JS_FN.match(line)
            if m:
                name = next((g for g in m.groups() if g), None)
                if name:
                    funcs.append((name, final_body_offset + idx))
                continue
        elif suffix == ".go":
            m = _RE_GO_TYPE.match(line)
            if m:
                types.append((m.group(1), final_body_offset + idx))
                continue
            m = _RE_GO_FUNC.match(line)
            if m:
                funcs.append((m.group(1), final_body_offset + idx))
                continue
        elif suffix == ".rs":
            m = _RE_RS_ITEM.match(line)
            if m:
                types.append((m.group(2), final_body_offset + idx))
                continue
            m = _RE_RS_FN.match(line)
            if m:
                funcs.append((m.group(1), final_body_offset + idx))
                continue
        elif suffix in {".java", ".kt"}:
            m = _RE_JAVA_TYPE.match(line)
            if m:
                types.append((m.group(2), final_body_offset + idx))
                continue
        elif suffix == ".cs":
            m = re.match(
                r"^\s*(?:public|protected|private|internal)?\s*(?:abstract|sealed|static|partial)?\s*(?:class|interface|struct|enum)\s+([A-Za-z_]\w*)\b",
                line,
            )
            if m:
                types.append((m.group(1), final_body_offset + idx))
                continue
        else:
            m = _RE_C_LIKE_FN.match(line)
            if m:
                funcs.append((m.group(1), final_body_offset + idx))

    def fmt(pairs: List[Tuple[str, int]], limit: int) -> List[str]:
        out: List[str] = []
        seen = set()
        for name, ln in pairs:
            if name in seen:
                continue
            seen.add(name)
            out.append(f"{name}@L{ln}")
            if len(out) >= limit:
                break
        return out

    return fmt(types, 4), fmt(funcs, 6), fmt(entrypoints, 2)


def _scan_type_pairs(
    path: Path, body_lines: List[str], final_body_offset: int
) -> List[Tuple[str, int]]:
    """
    Return all type-like declarations as (name, final_line_number).
    This is used for cross-file parent resolution and should not be aggressively limited.
    """
    suffix = path.suffix.lower()
    out: List[Tuple[str, int]] = []

    for idx, line in enumerate(body_lines, start=1):
        if len(line) > 5000:
            continue

        if suffix in {".py", ".pyi"}:
            m = _RE_PY_CLASS.match(line)
            if m:
                out.append((m.group(1), final_body_offset + idx))
        elif suffix in {".js", ".jsx", ".ts", ".tsx"}:
            if suffix in {".ts", ".tsx"}:
                m = (
                    _RE_TS_CLASS.match(line)
                    or _RE_TS_INTERFACE.match(line)
                    or _RE_TS_ENUM.match(line)
                    or _RE_TS_TYPE_ALIAS.match(line)
                )
                if m:
                    out.append((m.group(1), final_body_offset + idx))
            else:
                m = _RE_JS_CLASS.match(line)
                if m:
                    name = next((g for g in m.groups() if g), None)
                    if name:
                        out.append((name, final_body_offset + idx))
        elif suffix == ".go":
            m = _RE_GO_TYPE.match(line)
            if m:
                out.append((m.group(1), final_body_offset + idx))
        elif suffix == ".rs":
            m = _RE_RS_ITEM.match(line)
            if m:
                out.append((m.group(2), final_body_offset + idx))
        elif suffix in {".java", ".kt"}:
            m = _RE_JAVA_TYPE.match(line)
            if m:
                out.append((m.group(2), final_body_offset + idx))
        elif suffix == ".cs":
            m = re.match(
                r"^\s*(?:public|protected|private|internal)?\s*(?:abstract|sealed|static|partial)?\s*(?:class|interface|struct|enum)\s+([A-Za-z_]\w*)\b",
                line,
            )
            if m:
                out.append((m.group(1), final_body_offset + idx))

    return out


def _render_header_lines(
    *,
    style: CommentStyle,
    fields: Sequence[str],
    max_width: int,
) -> List[str]:
    fields = list(fields)

    # Ensure exactly 20 lines for block style by placing start on line 1 and end on line 20.
    if style.kind == "block":
        if len(fields) > HEADER_LINES:
            # Preserve the tail (Last update) and truncate earlier fields if needed.
            fields = fields[: HEADER_LINES - 1] + [fields[-1]]
        if len(fields) < HEADER_LINES:
            # Pad with blank lines before the final "Last update" line so the footer stays stable.
            pad = HEADER_LINES - len(fields)
            fields = fields[:-1] + ([""] * pad) + fields[-1:]

        rendered: List[str] = []
        rendered.append(f"{style.block_start} {_truncate(fields[0], max_width)}")
        for f in fields[1:-1]:
            rendered.append(style.block_line_prefix + _truncate(f, max_width))
        rendered.append(
            style.block_line_prefix
            + _truncate(fields[-1], max_width)
            + f" {style.block_end}"
        )
        return rendered

    # line comment style: 20 lines with prefix
    rendered = [style.line_prefix + _truncate(f, max_width) for f in fields]
    if len(rendered) > HEADER_LINES:
        rendered = rendered[:HEADER_LINES]
    while len(rendered) < HEADER_LINES:
        rendered.append(style.line_prefix.rstrip() + "")
    return rendered


def annotate_file(
    path: Path,
    *,
    root: Path,
    purpose: str,
    index_hint: str,
    max_width: int,
    dry_run: bool,
    refresh: bool,
    type_index: Optional[dict[str, List[Tuple[str, int]]]] = None,
) -> Tuple[bool, str]:
    style = _detect_comment_style(path)
    if style is None:
        return False, f"skip (unsupported): {path}"

    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = raw.splitlines(keepends=True)

    suffix = path.suffix.lower()
    prolog, rest = _split_prolog(lines, suffix=suffix)

    # For Python, use the module docstring (if any) as a hint, but keep it in place.
    existing_doc_hint = ""
    if suffix in {".py", ".pyi"} and not purpose:
        doc = _peek_py_module_docstring(rest)
        if doc:
            existing_doc_hint = doc

    existing_header, rest_wo_header, removed = _split_existing_codex_header(rest, path)
    existing_fields = (
        _parse_existing_header_fields(existing_header) if existing_header else {}
    )

    final_body_offset = len(prolog) + HEADER_LINES
    types, funcs, entrypoints = _extract_symbols(
        path, rest_wo_header, final_body_offset
    )
    inheritance = _extract_inheritance(
        path, rest_wo_header, final_body_offset, type_index=type_index
    )

    relpath = _relpath_for_header(path, root)
    today = _dt.date.today().isoformat()

    if refresh:
        final_purpose = purpose or existing_doc_hint or "TODO"
        public_api = "TODO"
        inputs_outputs = "TODO"
        core_flow = "TODO"
        dependencies = "TODO"
        error_handling = "TODO"
        config_env = "TODO"
        side_effects = "TODO"
        performance = "TODO"
        security = "TODO"
        tests = "TODO"
        known_issues = "TODO"
        index_value = index_hint or "TODO"
        last_update = today
    else:
        if purpose:
            final_purpose = purpose
        else:
            existing_purpose = existing_fields.get("Purpose")
            final_purpose = (
                existing_purpose
                if not _is_placeholder(existing_purpose)
                else (existing_doc_hint or "TODO")
            )

        def keep_or_todo(key: str) -> str:
            v = existing_fields.get(key)
            return v if v is not None and not _is_placeholder(v) else "TODO"

        public_api = keep_or_todo("Public API")
        inputs_outputs = keep_or_todo("Inputs/Outputs")
        core_flow = keep_or_todo("Core flow")
        dependencies = keep_or_todo("Dependencies")
        error_handling = keep_or_todo("Error handling")
        config_env = keep_or_todo("Config/env")
        side_effects = keep_or_todo("Side effects")
        performance = keep_or_todo("Performance")
        security = keep_or_todo("Security")
        tests = keep_or_todo("Tests")
        known_issues = keep_or_todo("Known issues")

        if index_hint:
            index_value = index_hint
        else:
            existing_index = existing_fields.get("Index")
            index_value = (
                existing_index if not _is_placeholder(existing_index) else "TODO"
            )

        existing_last_update = existing_fields.get("Last update")
        last_update = (
            existing_last_update if not _is_placeholder(existing_last_update) else today
        )

    header_fields = [
        f"{CODEX_MARKER} | 20 lines | keep updated",
        f"Path: {relpath}",
        f"Purpose: {final_purpose or 'TODO'}",
        f"Key types: {', '.join(types) if types else 'TODO'}",
        f"Inheritance: {', '.join(inheritance) if inheritance else 'TODO'}",
        f"Key funcs: {', '.join(funcs) if funcs else 'TODO'}",
        f"Entrypoints: {', '.join(entrypoints) if entrypoints else 'TODO'}",
        f"Public API: {public_api}",
        f"Inputs/Outputs: {inputs_outputs}",
        f"Core flow: {core_flow}",
        f"Dependencies: {dependencies}",
        f"Error handling: {error_handling}",
        f"Config/env: {config_env}",
        f"Side effects: {side_effects}",
        f"Performance: {performance}",
        f"Security: {security}",
        f"Tests: {tests}",
        f"Known issues: {known_issues}",
        f"Index: {index_value}",
        f"Last update: {last_update}",
    ]

    header = _render_header_lines(
        style=style, fields=header_fields, max_width=max_width
    )

    new_lines = []
    new_lines.extend(prolog)
    new_lines.extend([ln if ln.endswith("\n") else ln + "\n" for ln in header])
    new_lines.extend(rest_wo_header)

    new_raw = "".join(new_lines)
    if not refresh and existing_header and new_raw != raw and last_update != today:
        # Only bump Last update when we actually changed something else.
        header_fields[-1] = f"Last update: {today}"
        header = _render_header_lines(
            style=style, fields=header_fields, max_width=max_width
        )
        new_lines = []
        new_lines.extend(prolog)
        new_lines.extend([ln if ln.endswith("\n") else ln + "\n" for ln in header])
        new_lines.extend(rest_wo_header)
        new_raw = "".join(new_lines)
    if new_raw == raw:
        return False, f"no-op: {path}"

    if not dry_run:
        path.write_text(new_raw, encoding="utf-8")

    return True, ("updated" if removed else "inserted") + f": {path}"


def _iter_files(args_files: Sequence[str]) -> Iterable[Path]:
    for f in args_files:
        p = Path(f)
        if p.is_dir():
            for child in p.rglob("*"):
                if child.is_file():
                    yield child
        else:
            yield p


def _build_type_index(
    paths: Sequence[Path], *, root: Path
) -> dict[str, List[Tuple[str, int]]]:
    """
    Best-effort index: type name -> [(relpath, final_line_number), ...].
    Line numbers are computed as if the file has the fixed 20-line header in place.
    """
    index: dict[str, List[Tuple[str, int]]] = {}
    for path in paths:
        style = _detect_comment_style(path)
        if style is None:
            continue

        raw = path.read_text(encoding="utf-8", errors="replace")
        lines = raw.splitlines(keepends=True)
        suffix = path.suffix.lower()
        prolog, rest = _split_prolog(lines, suffix=suffix)
        _, rest_wo_header, _ = _split_existing_codex_header(rest, path)

        final_body_offset = len(prolog) + HEADER_LINES
        type_pairs = _scan_type_pairs(path, rest_wo_header, final_body_offset)

        rel = _relpath_for_header(path, root)
        for name, ln in type_pairs:
            if name:
                index.setdefault(name, []).append((rel, ln))

    return index


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Insert/update a fixed 20-line file-header comment (@codex-header: v1) to help index code. "
            "For Python, uses line comments so a real module docstring can remain the first statement."
        )
    )
    parser.add_argument("files", nargs="+", help="File(s) or directory(ies) to process")
    parser.add_argument(
        "--root", default=".", help="Repo root used to compute relative Path in header"
    )
    parser.add_argument(
        "--purpose",
        default="",
        help="Override Purpose line (otherwise best-effort from existing docstring)",
    )
    parser.add_argument(
        "--index-hint",
        default="",
        help="Override Index line (e.g. Imports@L..; Types@L..; ...)",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Rewrite header from scratch (may reset non-TODO manual fields back to TODO)",
    )
    parser.add_argument(
        "--resolve-parents",
        action="store_true",
        help="Try to resolve external parents as Name@path#L.. in Inheritance",
    )
    parser.add_argument(
        "--max-width",
        type=int,
        default=DEFAULT_MAX_WIDTH,
        help="Truncate each header line to this width",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Do not write; only print actions"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Run verification after completion (checks for incomplete auto-populated fields)",
    )
    parser.add_argument(
        "--update-agents-md",
        action="store_true",
        help="Update AGENTS.md with indexed files after annotation (reduces context bloat for AI)",
    )
    args = parser.parse_args(argv)

    root = Path(args.root)

    input_paths: List[Path] = []
    for p in _iter_files(args.files):
        if not p.exists() or not p.is_file():
            print(f"skip (missing): {p}", file=sys.stderr)
            continue
        input_paths.append(p)
    type_index = (
        _build_type_index(input_paths, root=root) if args.resolve_parents else None
    )

    changed = 0
    annotated_files: List[Tuple[Path, str, str, str]] = []
    for path in input_paths:
        try:
            did_change, msg = annotate_file(
                path,
                root=root,
                purpose=args.purpose,
                index_hint=args.index_hint,
                max_width=args.max_width,
                dry_run=args.dry_run,
                refresh=args.refresh,
                type_index=type_index,
            )
            print(msg)
            if did_change:
                changed += 1
                # Collect file info for AGENTS.md
                existing_fields = {}
                style = _detect_comment_style(path)
                if style:
                    try:
                        raw = path.read_text(encoding="utf-8", errors="replace")
                        lines = raw.splitlines(keepends=True)
                        suffix = path.suffix.lower()
                        prolog, rest = _split_prolog(lines, suffix=suffix)
                        existing_header, _, _ = _split_existing_codex_header(rest, path)
                        if existing_header:
                            existing_fields = _parse_existing_header_fields(
                                existing_header
                            )
                    except Exception:
                        pass

                purpose = existing_fields.get("Purpose", "TODO")
                types = existing_fields.get("Key types", "TODO")
                funcs = existing_fields.get("Key funcs", "TODO")
                annotated_files.append((path, purpose, types, funcs))
        except Exception as e:
            print(f"error: {path}: {e}", file=sys.stderr)

    if args.dry_run:
        print(f"dry-run: {changed} file(s) would change", file=sys.stderr)
    else:
        print(f"done: {changed} file(s) changed", file=sys.stderr)

    if args.update_agents_md and not args.dry_run and changed > 0:
        print("\nUpdating AGENTS.md...", file=sys.stderr)
        if _update_agents_md(root, annotated_files):
            print(
                f"updated: AGENTS.md with {len(annotated_files)} file(s)",
                file=sys.stderr,
            )
        else:
            print("no changes: AGENTS.md", file=sys.stderr)

    # Run verification if requested
    if args.verify and not args.dry_run and changed > 0:
        print("\nRunning verification...", file=sys.stderr)
        from importlib import resources
        import subprocess

        # Import and run check_incomplete_headers.py
        check_script = Path(__file__).parent / "check_incomplete_headers.py"
        if check_script.exists():
            cmd = [sys.executable, str(check_script), *args.files, "--root", args.root]
            result = subprocess.run(cmd, capture_output=True, text=True)
            print(result.stdout, end="")
            if result.stderr:
                print(result.stderr, end="", file=sys.stderr)
            return result.returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
