---
name: code-header-annotator
description: Add or refresh a fixed 20-line file-header comment that summarizes a source file and indexes key classes/functions with line-number addresses. Use when annotating large codebases for fast navigation, onboarding, refactors, or when you want LLMs/humans to locate relevant symbols quickly without reading entire files.
---

# Code Header Annotator

Maintain a **fixed 20-line header region** per code file (marked by `@codex-header: v1`) that captures the file's purpose and a compact index of key symbols (with line addresses).

## Workflow (per file)

1. **Preserve prolog lines** - Keep required first lines (shebang, encoding cookie, build tags, etc.)
2. **Ensure 20-line header** - Insert new or update existing, always keep `@codex-header: v1` marker
3. **Scan file sections** - Imports → config → types → functions → entrypoints → side effects
4. **Populate header** - Use precise names + line addresses, write `TODO` when unsure
5. **Verify addresses** - Ensure every `Name@L123` points to correct definition

## Navigation

When exploring large repos, **read headers first**, only open full files when relevant:

- Find annotated files: `rg "@codex-header: v1"`
- Check `Purpose`, `Key types`, `Key funcs`, `Inheritance` for relevance
- Use `Inheritance` to jump "up" (bases) and "sideways" (siblings)
- If parent is external (e.g., `Base@pkg/base.py#L42`), open that file's header first

**Relationship notation**: `->` inherits, `~>` implements, `+` mixin

### Upward Reasoning (inheritance / parent objects)

Use the header to "walk upward" from a concrete type to its parents:

1. Start at the child's header `Inheritance:` (e.g., `Child@L120->Base@L30`).
2. If the base has an in-file address (`Base@L..`), jump there.
3. If the base is external, prefer a cross-file pointer when available (e.g., `Base@path/to/base.ts#L30`) and jump to that file's header first.
4. If the base is external and has no pointer, use `Dependencies:` / `Public API:` hints, then search the repo for the base definition (e.g., `rg "class Base\\b"` / `rg "interface Base\\b"`), and **annotate the base file too** so it becomes indexable.
5. Repeat until you reach the framework root / stable abstract base (or the registry/factory entrypoint).

## Verification (required)

After processing all files, **always run verification** to ensure all auto-populated fields are complete:

```bash
python code-header-annotator/scripts/check_incomplete_headers.py <files-or-dirs> --root <repo-root>
```

This script checks for incomplete auto-populated fields (Key types, Key funcs, Entrypoints, Index) that should have been filled by the annotation script but weren't (e.g., due to tool crashes or interruptions).

If incomplete files are found, re-process them:

```bash
python code-header-annotator/scripts/annotate_code_headers.py <incomplete-files> --root <repo-root>
```

Then re-run verification until all headers are complete.

## What to Capture (priority order)

1. **Purpose** - What this file is responsible for (one sentence)
2. **Public surface** - What other files import/call/instantiate from here
3. **Key symbols + addresses** - Classes/interfaces, factories, handlers, main functions
4. **Inheritance & extension points** - Base classes, subclasses, registries, plugin hooks
5. **Side effects / I-O** - DB/filesystem/network, global state, caches
6. **Constraints** - Important invariants, error modes, performance or security notes

## Automation

Use bundled script to insert/update headers:

```bash
python code-header-annotator/scripts/annotate_code_headers.py <files-or-dirs> --root <repo-root> --resolve-parents
```

**Always verify** after processing:

```bash
python code-header-annotator/scripts/check_incomplete_headers.py <files-or-dirs> --root <repo-root>
```

Or use `--verify` flag for automatic verification:

```bash
python code-header-annotator/scripts/annotate_code_headers.py <files-or-dirs> --root <repo-root> --resolve-parents --verify
```

**Key options**:
- `--refresh` - Rebuild header from scratch (resets manual fields to TODO)
- `--resolve-parents` - Resolve external parents to cross-file references
- Default is non-destructive: preserves existing non-TODO manual fields

## Core Rules

- **Fixed size**: Always 20 lines per file
- **High-signal**: One-line fields, compress lists, truncate long text
- **Indexing first**: Include exported/public API, key types, key functions, entrypoints
- **Addresses**: Use `Name@L<line>` for all concrete symbols
- **Concrete names only**: Never use abstract descriptions like "data models"

## References

- **Field guidelines**: See [guidelines.md](references/guidelines.md) for detailed requirements per field
- **Examples**: See [examples.md](references/examples.md) for good vs bad patterns
- **Format spec**: See [header-format.md](references/header-format.md) for canonical field structure
