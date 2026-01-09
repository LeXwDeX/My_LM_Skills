# Field Guidelines

## Core Principles

- **Concrete names only**: Always use specific type/function/variable names, NEVER abstract descriptions
- **Addresses required**: All concrete symbols must include `@L<line>` line numbers
- **High-signal**: One-line fields, compress lists, truncate long text
- **Always maintain index**: Update headers immediately after any file modification

## Index Maintenance (MANDATORY)

When this skill is active, you MUST maintain the header index **every time you modify a file**.

### When to Update

| Action | Update Required |
|--------|-----------------|
| Add new class/function | Add to `Key types` / `Key funcs` with `@L<line>` |
| Delete class/function | Remove from header fields |
| Rename symbol | Update name in all relevant header fields |
| Move code (line shifts) | Recalculate and update all `@L<line>` addresses |
| Change file responsibility | Update `Purpose` field |
| Change exports | Update `Public API` field |
| Change inheritance | Update `Inheritance` field |
| Add new source file | Create new 20-line header |

### How to Update

1. **In the same edit** as code changes, update the header
2. **Verify line numbers** by checking the actual line positions in the file
3. **Run verification** after batch changes:
   ```bash
   python scripts/check_incomplete_headers.py <files> --root .
   ```

### Anti-Pattern: Stale Indexes

**NEVER**:
- Modify code without updating the header
- Leave `TODO` in fields that are now known
- Ignore line number drift after refactoring
- Add new files without headers

**ALWAYS**:
- Update header immediately after code changes
- Verify addresses point to correct lines
- Run `check_incomplete_headers.py` after modifications
- Treat headers as live, accurate documentation

### Quality Checklist Addition

- [ ] **Index accuracy**: All `@L<line>` addresses point to correct definitions
- [ ] **No stale entries**: Deleted symbols removed from header
- [ ] **New symbols added**: All new types/functions included
- [ ] **Line drift fixed**: Addresses updated after code movement

## Header Fields Priority

1. **Purpose** - What this file is responsible for (one sentence)
2. **Public surface** - What other files import/call/instantiate from here
3. **Key symbols + addresses** - Classes/interfaces, factories, handlers, main functions
4. **Inheritance & extension points** - Base classes, subclasses, registries, plugin hooks
5. **Side effects / I-O** - DB/filesystem/network, global state, caches
6. **Constraints** - Important invariants, error modes, performance or security notes

## Key types

**MUST use concrete type names with line numbers**

**WRONG**:
```
* Key types: Data models, utility functions, configuration objects
```

**RIGHT**:
```
* Key types: User@L15, Message@L42, Config@L89
```

**Why**: Abstract descriptions are useless for navigation. Concrete names allow `rg "class User"` or jumping to `L15` directly.

## Dependencies

**MUST list specific external dependencies**

**WRONG**:
```
* Dependencies: Uses external libraries and frameworks
```

**RIGHT**:
```
* Dependencies: React, lodash, axios, node:fs, @types/node
```

**For intra-file dependencies**: Use the Inheritance field or include inline references like `uses BaseHandler@L30`.

### What to include

1. **External packages/libraries** - List actual package names from import statements
   - Python: `import pandas as pd`, `from sklearn.metrics import accuracy_score` → `pandas, scikit-learn`
   - JS/TS: `import React from 'react'`, `import { AxiosInstance } from 'axios'` → `React, axios`
   - Node.js built-ins: `node:fs`, `node:path`, `node:http`

2. **Framework-specific dependencies**
   - React components: `React, react-dom, @types/react`
   - Node.js APIs: `express, node:fs, node:http`
   - Database: `mongoose, pg, sequelize`

3. **Type-only imports** (important for TS)
   - `import type { User } from './types'` → `type: ./types/User`

4. **Intra-file dependencies**
   - Use line references: `uses BaseValidator@L45, imports Config from './config'`

### How to extract

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

## Public API

**MUST specify exact exported symbols**

**WRONG**:
```
* Public API: Exports functions and classes
```

**RIGHT**:
```
* Public API: createUser(), getUserById(), User class, Config object
```

## Purpose

**MUST be specific, not generic**

**WRONG**:
```
* Purpose: Implements utility functions for data processing
```

**RIGHT**:
```
* Purpose: Handles user authentication and session management with JWT tokens
```

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

## Common Anti-Patterns

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
