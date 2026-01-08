# 20-line Code Header Format (Codex)

This skill maintains a **fixed 20-line header region** per code file, marked by:

- `@codex-header: v1`

## Goals

- Provide a quick "what/where/how" summary without reading the whole file.
- Provide **addresses** (line numbers) for key classes/types/functions/entrypoints.
- Keep a stable, machine-detectable header for update/refresh.

## Header Fields (one line each)

1. Marker/version + invariants
2. `Path: ...` (repo-relative if possible)
3. `Purpose: ...` (one sentence)
4. `Key types: Name@L.., ...`
5. `Inheritance: Child@L..->Base@L.., Child@L..~>Iface@L.., Child@L..+Mixin@L.., ...` (best-effort; parent may be external)
6. `Key funcs: name@L.., ...`
7. `Entrypoints: ...`
8. `Public API: ...`
9. `Inputs/Outputs: ...`
10. `Core flow: ...`
11. `Dependencies: ...`
12. `Error handling: ...`
13. `Config/env: ...`
14. `Side effects: ...`
15. `Performance: ...`
16. `Security: ...`
17. `Tests: ...`
18. `Known issues: ...`
19. `Index: Section@L..; ...` (coarse section map)
20. `Last update: YYYY-MM-DD` (for block-style comments, the closer shares this line)

## Comment Styles (best-effort)

- Python: line comments (`# ...`) so a real module docstring can remain the first statement
- Many C/JS-like languages: `/* ... */`
- Shell/Ruby/YAML: `# ...`
- SQL/Lua: `-- ...`
- HTML/XML: `<!-- ... -->`

Files without a comment syntax (e.g. JSON) should be skipped or handled separately.

## Relationship Notation

- `->` means “extends / inherits from”
- `~>` means “implements / conforms to” (interfaces/traits/protocols)
- `+` means “secondary base / mixin” (language-dependent)

## Cross-file addresses (optional)

When a parent type lives in another file and can be resolved, use:

- `Base@path/to/file.ext#L123`

Keep `Name@L123` for in-file addresses.
