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
- **Indexing first**: Include the most "findable" info: exported/public API, key types, key functions, entrypoints.
- **Addresses**: Use `Name@L<line>` for key symbols. Prefer:
  - Base class / interface declarations
  - Subclasses / concrete implementations
  - Public functions and constructors
  - Factories/builders and registry lookups
  - CLI/web handlers and job entrypoints
- **Section map**: Use `Index:` as a coarse table-of-contents with section anchors (e.g. `Imports@L..; Types@L..; API@L..; Main@L..`).
- **Concrete names only**: Always use specific type/function/variable names, NEVER abstract descriptions.

## What To Capture (priority order)

1. **Purpose**: What this file is responsible for (one sentence).
2. **Public surface**: What other files import/call/instantiate from here.
3. **Key symbols + addresses**: Classes/interfaces, factories, handlers, main functions.
4. **Inheritance & extension points**: Base classes, subclasses, registries, plugin hooks.
5. **Side effects / I-O**: DB/filesystem/network, global state, caches.
6. **Constraints**: Important invariants, error modes, performance or security notes.

## Critical Field Guidelines

### Key types (MUST use concrete type names)

**WRONG** - Abstract descriptions:
```
* Key types: Data models, utility functions, configuration objects
```

**RIGHT** - Concrete type names with line numbers:
```
* Key types: User@L15, Message@L42, Config@L89
```

**Why**: Abstract descriptions are useless for navigation. Concrete names allow `rg "class User"` or jumping to `L15` directly.

### Dependencies (MUST list specific external dependencies)

**WRONG** - Generic description:
```
* Dependencies: Uses external libraries and frameworks
```

**RIGHT** - Specific dependency list:
```
* Dependencies: React, lodash, axios, node:fs, @types/node
```

**For intra-file dependencies**: Use the Inheritance field or include inline references like `uses BaseHandler@L30`.

### Public API (MUST specify exact exported symbols)

**WRONG** - Vague description:
```
* Public API: Exports functions and classes
```

**RIGHT** - Exact export list:
```
* Public API: createUser(), getUserById(), User class, Config object
```

### Purpose (MUST be specific, not generic)

**WRONG** - Generic description:
```
* Purpose: Implements utility functions for data processing
```

**RIGHT** - Specific responsibility:
```
* Purpose: Handles user authentication and session management with JWT tokens
```

## Examples and Anti-Examples

### Bad Example (GLM4.7 style - too generic):
```
* @codex-header: v1
* Path: src/auth.ts
* Purpose: Authentication module for user management
* Key types: Data models, configuration classes, utility types
* Inheritance: Extends base classes and implements interfaces
* Key funcs: Authentication functions, validation helpers
* Entrypoints: Main entry points for the module
* Public API: Exports various functions and classes
* Dependencies: Uses external libraries and utilities
```

### Good Example (GPT5 style - concrete and navigable):
```
* @codex-header: v1
* Path: src/auth.ts
* Purpose: JWT-based authentication with refresh tokens and role-based access control
* Key types: AuthConfig@L12, TokenPayload@L45, UserSession@L89
* Inheritance: AuthHandler@L120->BaseHandler@L30, AuthService~>IAuthValidator@L200
* Key funcs: generateToken@L234, validateToken@L267, refreshSession@L312
* Entrypoints: login@L345, logout@L367, refreshToken@L389
* Public API: AuthController class, createAuthMiddleware(), verifyToken()
* Dependencies: jsonwebtoken@2.5.0, bcrypt, node:crypto, lodash/get
```

## Dependency Extraction Guidelines

### What to include in Dependencies field

1. **External packages/libraries**: List actual package names from import statements
   - Python: `import pandas as pd`, `from sklearn.metrics import accuracy_score` → `pandas, scikit-learn`
   - JS/TS: `import React from 'react'`, `import { AxiosInstance } from 'axios'` → `React, axios`
   - Node.js built-ins: `node:fs`, `node:path`, `node:http`

2. **Framework-specific dependencies**:
   - React components: `React, react-dom, @types/react`
   - Node.js APIs: `express, node:fs, node:http`
   - Database: `mongoose, pg, sequelize`

3. **Type-only imports** (important for TS):
   - `import type { User } from './types'` → indicate this is a type dependency

4. **Intra-file dependencies**:
   - Use line references: `uses BaseValidator@L45, imports Config from './config'`

### How to extract dependencies

Scan the import/include section of the file and extract:
- Package names (not just module paths)
- Framework dependencies
- Platform-specific APIs

**Example extraction process**:
```typescript
import React from 'react'              → React
import { useState, useEffect } from 'react'  → React
import axios from 'axios'               → axios
import { useRouter } from 'next/router'    → next/router
import type { User } from './types'     → type: ./types/User
import { Logger } from '../utils/logger'  → uses Logger@../utils/logger#L20
```

Result: `Dependencies: React, axios, next/router, type: ./types/User, uses Logger@../utils/logger#L20`

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
- By default, re-running the script is **non-destructive** for manually/LLM-filled fields (e.g. `Purpose`, `Public API`): it preserves existing non-`TODO` values. Use `--refresh` to forcibly rebuild the header from scratch (may reset manual fields back to `TODO`).

## References

- `code-header-annotator/references/header-format.md` (canonical header fields + goals)

## Quality Checklist

Before finalizing a header, verify:

- [ ] **Key types**: Lists concrete type names (e.g., `User@L15`), NOT abstract descriptions (e.g., "data models")
- [ ] **Key funcs**: Lists concrete function names (e.g., `login@L234`), NOT generic descriptions (e.g., "authentication functions")
- [ ] **Dependencies**: Lists specific package names and external dependencies, NOT "uses external libraries"
- [ ] **Public API**: Specifies exact exported symbols, NOT "exports functions and classes"
- [ ] **Purpose**: Is specific and actionable, NOT generic like "utility module"
- [ ] **Inheritance**: Uses relationship notation (`->`, `~>`, `+`) with concrete names, NOT "extends base classes"
- [ ] **Addresses**: All named symbols include `@L<line>` line numbers
- [ ] **Completeness**: No fields contain "TODO" that could have been filled from the file content
- [ ] **Accuracy**: Line numbers actually point to the correct definitions
- [ ] **Brevity**: Each field is concise (truncated if too long, not verbose prose)

## Common Anti-Patterns to Avoid

1. **Generic descriptions**: "handles data", "utility functions", "business logic"
   - **Fix**: Be specific: "manages user CRUD operations", "validates JWT tokens", "processes payment transactions"

2. **Missing line numbers**: `User` instead of `User@L15`
   - **Fix**: Always add `@L<line>` for all concrete symbols

3. **Vague dependencies**: "uses external libraries", "framework dependencies"
   - **Fix**: List actual packages: "React, axios, lodash, node:fs"

4. **Abstract type names**: "DataModel", "Helper", "Manager"
   - **Fix**: Use actual type names from the code: "User", "AuthService", "PaymentProcessor"

5. **Prose in summary fields**: "The purpose of this file is to implement authentication functionality"
   - **Fix**: One-line summary: "JWT-based authentication with refresh tokens"
