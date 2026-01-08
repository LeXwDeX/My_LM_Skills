---
name: code-header-annotator
description: Add or refresh a fixed 20-line file-header comment that summarizes a source file and indexes key classes/functions with line-number addresses. Use when annotating large codebases for fast navigation, onboarding, refactors, or when you want LLMs/humans to locate relevant symbols quickly without reading entire files.
---

# Code Header Annotator

Maintain a **fixed 20-line header region** per code file (marked by `@codex-header: v1`) that captures the file’s purpose and a compact index of key symbols (with line addresses).

## Workflow (per file)

1. **Preserve prolog lines**
   - Keep any required "must-be-first" lines intact (e.g. shebang, Python encoding cookie, Go build tags, XML declaration, Rust `#![...]` inner attributes).
2. **Ensure the header exists and is exactly 20 lines**
   - Insert a new header if missing; otherwise update the existing one.
   - Always keep the marker `@codex-header: v1` in the header.
3. **Scan the file in sections**
   - Imports/includes → configuration/constants → types/classes → main functions/methods → entrypoints → side effects/I/O.
4. **Populate the header with compact, lossless essentials**
   - Prefer precise names + line addresses over prose.
   - If unsure, write `TODO` (never hallucinate line numbers or APIs).
5. **Verify addresses**
   - Ensure every `Name@L123` points to the correct definition line in the updated file.

## Completion Verification (required)

After processing all files, **always run the verification step** to ensure all auto-populated fields are complete:

`python code-header-annotator/scripts/check_incomplete_headers.py <files-or-dirs> --root <repo-root>`

This script checks for incomplete auto-populated fields (Key types, Key funcs, Entrypoints, Index) that should have been filled by the annotation script but weren't (e.g., due to tool crashes or interruptions).

If incomplete files are found, re-process them:
`python code-header-annotator/scripts/annotate_code_headers.py <incomplete-files> --root <repo-root>`

Then re-run the verification until all headers are complete.

## Use The Header As The Primary Index (reading mode)

When exploring a large repo, **prefer reading headers first** and only open full file bodies when a header indicates relevance.

- Find annotated files: `rg "@codex-header: v1"`
- For a candidate file, read its 20-line header and decide:
  - Does `Purpose` match the task?
  - Do `Key types` / `Key funcs` contain the symbol you need?
  - Does `Inheritance` show the parent/base you need?
  - Does `Index` give the section anchor to jump to?

### Treat headers as a navigable graph (critical for LLM use)

When this skill is available, assume the codebase may already contain enough signal in headers to navigate **without reading full files**:

- Use `Key types` / `Key funcs` to locate the concrete symbol you’re working on.
- Use `Inheritance` to jump “up” (base classes / interfaces / mixins) and “sideways” (siblings sharing the same base).
- If an `Inheritance` edge points to another file (e.g. `Base@pkg/base.py#L42`), open **that file’s header first** and repeat.
- If a referenced parent isn’t annotated yet, annotate it so the chain becomes cheap to traverse.

## Upward Reasoning (inheritance / parent objects)

Use the header to “walk upward” from a concrete type to its parents:

1. Start at the child’s header `Inheritance:` (e.g. `Child@L120->Base@L30`).
2. If the base has an in-file address (`Base@L..`), jump there.
3. If the base is external, prefer a cross-file pointer when available (e.g. `Base@path/to/base.ts#L30`) and jump to that file’s header first.
4. If the base is external and has no pointer, use `Dependencies:` / `Public API:` hints, then search the repo for the base definition (e.g. `rg "class Base\\b"` / `rg "interface Base\\b"`), and **annotate the base file too** so it becomes indexable.
5. Repeat until you reach the framework root / stable abstract base (or the registry/factory entrypoint).

### Relationship notation (best-effort)

Use compact edges so the model can reliably follow relationships:

- `Child@L..->Base...` means “extends / inherits from”
- `Child@L..~>Iface...` means “implements / conforms to”
- `Child@L..+Mixin...` means “secondary base / mixin (language-dependent)”

## Header Content Rules

- **Fixed size**: The header region is always **20 lines** for every file.
- **High-signal**: One-line fields; compress lists; truncate long text.
- **Indexing first**: Include the most “findable” info: exported/public API, key types, key functions, entrypoints.
- **Addresses**: Use `Name@L<line>` for key symbols. Prefer:
  - Base class / interface declarations
  - Subclasses / concrete implementations
  - Public functions and constructors
  - Factories/builders and registry lookups
  - CLI/web handlers and job entrypoints
- **Section map**: Use `Index:` as a coarse table-of-contents with section anchors (e.g. `Imports@L..; Types@L..; API@L..; Main@L..`).

## What To Capture (priority order)

1. **Purpose**: What this file is responsible for (one sentence).
2. **Public surface**: What other files import/call/instantiate from here.
3. **Key symbols + addresses**: Classes/interfaces, factories, handlers, main functions.
4. **Inheritance & extension points**: Base classes, subclasses, registries, plugin hooks.
5. **Side effects / I-O**: DB/filesystem/network, global state, caches.
6. **Constraints**: Important invariants, error modes, performance or security notes.

## Automation (recommended)

Use the bundled script to insert/update headers and pre-fill symbol indexes (then refine the summary lines):

`python code-header-annotator/scripts/annotate_code_headers.py <files-or-dirs> --root <repo-root> --resolve-parents`

**Always run verification after processing** to ensure all auto-populated fields are complete:

`python code-header-annotator/scripts/check_incomplete_headers.py <files-or-dirs> --root <repo-root>`

Or use the `--verify` flag to run verification automatically:

`python code-header-annotator/scripts/annotate_code_headers.py <files-or-dirs> --root <repo-root> --resolve-parents --verify`

Notes:
- Skips file types without reliable comments (e.g. `.json`).
- Python uses `# ...` line comments so a real module docstring can remain the first statement.
- Best-effort symbol extraction for common languages (Python/JS/TS/Go/Rust/Java/etc).
- The verification script intelligently checks if files have incomplete auto-populated fields by analyzing the actual file content.

## References

- `code-header-annotator/references/header-format.md` (canonical header fields + goals)
