# Examples and Anti-Examples

## Bad Example (Too Generic)

```
/* @codex-header: v1 | 20 lines | keep updated
 * Path: src/auth.ts
 * Purpose: Authentication module for user management
 * Key types: Data models, configuration classes, utility types
 * Inheritance: Extends base classes and implements interfaces
 * Key funcs: Authentication functions, validation helpers
 * Entrypoints: Main entry points for the module
 * Public API: Exports various functions and classes
 * Inputs/Outputs: TODO
 * Core flow: TODO
 * Dependencies: Uses external libraries and utilities
 * Error handling: TODO
 * Config/env: TODO
 * Side effects: TODO
 * Performance: TODO
 * Security: TODO
 * Tests: TODO
 * Known issues: TODO
 * Index: TODO
 * Last update: 2026-01-01 */
```

**Problems**:
- Generic descriptions ("data models", "authentication functions")
- No line numbers on any symbols
- Vague dependencies ("uses external libraries")
- Purpose is not specific
- Many TODO fields that could be filled

## Good Example (Concrete and Navigable)

```
/* @codex-header: v1 | 20 lines | keep updated
 * Path: src/auth.ts
 * Purpose: JWT-based authentication with refresh tokens and role-based access control
 * Key types: AuthConfig@L12, TokenPayload@L45, UserSession@L89
 * Inheritance: AuthHandler@L120->BaseHandler@L30, AuthService~>IAuthValidator@L200
 * Key funcs: generateToken@L234, validateToken@L267, refreshSession@L312
 * Entrypoints: login@L345, logout@L367, refreshToken@L389
 * Public API: AuthController class, createAuthMiddleware(), verifyToken()
 * Inputs/Outputs: Returns JWT tokens, accepts user credentials
 * Core flow: Validate credentials → Generate token → Set session → Return response
 * Dependencies: jsonwebtoken@2.5.0, bcrypt, node:crypto, lodash/get
 * Error handling: Throws InvalidCredentialsError, TokenExpiredError
 * Config/env: JWT_SECRET env var, TOKEN_EXPIRY=1h, REFRESH_EXPIRY=7d
 * Side effects: Updates user.last_login in DB, writes to auth_logs
 * Performance: Token validation <5ms, cached DB lookups
 * Security: Bcrypt hashing, HTTPS only, token expiration enforced
 * Tests: login.test.ts, token.test.ts, middleware.test.ts (coverage 95%)
 * Known issues: Token refresh fails when clock sync >30s off
 * Index: Imports@L1-10; Config@L12-30; Types@L45-88; Handlers@L120-210; Functions@L234-340; Entrypoints@L345-400
 * Last update: 2026-01-01 */
```

**Strengths**:
- All concrete symbols with exact line numbers
- Specific dependencies with version numbers
- Purpose is actionable and specific
- Most fields filled (only 1 TODO in Index)
- Clear relationship notation in Inheritance
- Detailed side effects and constraints

## Field-by-Field Comparison

| Field | Bad | Good |
|--------|-----|------|
| **Purpose** | "Authentication module" | "JWT-based authentication with refresh tokens and role-based access control" |
| **Key types** | "Data models, utility types" | "AuthConfig@L12, TokenPayload@L45, UserSession@L89" |
| **Inheritance** | "Extends base classes" | "AuthHandler@L120->BaseHandler@L30, AuthService~>IAuthValidator@L200" |
| **Key funcs** | "Authentication functions" | "generateToken@L234, validateToken@L267, refreshSession@L312" |
| **Dependencies** | "Uses external libraries" | "jsonwebtoken@2.5.0, bcrypt, node:crypto, lodash/get" |
| **Public API** | "Exports functions and classes" | "AuthController class, createAuthMiddleware(), verifyToken()" |

## Language-Specific Examples

### Python

```
# @codex-header: v1 | 20 lines | keep updated
# Path: src/user_service.py
# Purpose: Manages user CRUD operations with PostgreSQL and SQLAlchemy ORM
# Key types: User@L15, UserService@L45, UserRepository@L89
# Inheritance: UserService@L45->BaseService@L10
# Key funcs: create_user@L120, get_user_by_id@L145, update_user@L167, delete_user@L189
# Entrypoints: main@L210, init_db@L225
# Public API: UserService class, get_user_session()
# Dependencies: sqlalchemy, psycopg2-binary, pydantic, python-dotenv
# Side effects: Writes to users table, logs to file, sends emails
# Error handling: Raises UserNotFoundError, DuplicateUserError, ValidationError
# Config/env: DATABASE_URL, SMTP_HOST, SMTP_PORT
# Security: Passwords hashed with bcrypt, input validation with pydantic
# Tests: test_user_service.py (pytest, coverage 92%)
# Index: Imports@L1-12; Models@L15-42; Service@L45-118; Functions@L120-205
# Last update: 2026-01-01
```

### JavaScript/TypeScript

```
/* @codex-header: v1 | 20 lines | keep updated
 * Path: src/api/routes.ts
 * Purpose: Express REST API routes for product catalog with caching
 * Key types: Product@L12, ProductController@L45, RouteHandler@L89
 * Inheritance: ProductController@L45->BaseController@L20
 * Key funcs: getProducts@L120, getProductById@L145, createProduct@L167, updateProduct@L189
 * Entrypoints: router@L210, initializeRoutes@L225
 * Public API: router instance, middleware functions
 * Dependencies: express, redis, node:cache-manager, zod
 * Side effects: Reads from PostgreSQL, writes to Redis cache, logs to stdout
 * Error handling: Returns 404 for missing products, 400 for validation errors
 * Config/env: PORT=3000, REDIS_URL, CACHE_TTL=300
 * Performance: <50ms response time (p95), cached responses <5ms
 * Security: Rate limiting (100 req/min), input sanitization with zod
 * Tests: routes.test.ts (jest, coverage 88%)
 * Index: Imports@L1-10; Types@L12-42; Controller@L45-118; Routes@L120-205
 * Last update: 2026-01-01 */
```

### Go

```
/* @codex-header: v1 | 20 lines | keep updated
 * Path: handlers/auth.go
 * Purpose: HTTP handlers for JWT authentication with middleware
 * Key types: AuthHandler@L15, Claims@L45, TokenResponse@L89
 * Key funcs: LoginHandler@L120, RefreshHandler@L145, LogoutHandler@L167
 * Entrypoints: main@L189
 * Public API: LoginHandler, RefreshHandler, LogoutHandler
 * Dependencies: github.com/golang-jwt/jwt/v5, golang.org/x/crypto/bcrypt
 * Side effects: Writes to auth_tokens table, invalidates cache
 * Error handling: Returns 401 for invalid tokens, 400 for malformed requests
 * Config/env: JWT_SECRET, TOKEN_EXPIRY
 * Security: Bcrypt cost=12, token expiration enforced
 * Tests: auth_test.go (go test, coverage 90%)
 * Index: Imports@L1-12; Types@L15-42; Handlers@L120-165
 * Last update: 2026-01-01 */
```

## Common Mistakes to Avoid

### 1. Mixing Abstract and Concrete

**Don't do this**:
```
* Key types: User, Data models, utility classes
```

**Do this instead**:
```
* Key types: User@L15, UserService@L45, UserRepository@L89
```

### 2. Incomplete Addresses

**Don't do this**:
```
* Key types: User@L15, Message@L??, Config
```

**Do this instead**:
```
* Key types: User@L15, Message@L42, Config@L89
```

### 3. Wrong Relationship Notation

**Don't do this**:
```
* Inheritance: AuthHandler extends BaseHandler, implements Validator
```

**Do this instead**:
```
* Inheritance: AuthHandler@L120->BaseHandler@L30, AuthService~>IAuthValidator@L200
```

### 4. Verbose Prose in Fields

**Don't do this**:
```
* Purpose: The purpose of this file is to handle all authentication-related functionality including login, logout, and token management
```

**Do this instead**:
```
* Purpose: JWT-based authentication with login/logout and token management
```

### 5. TODO When Information Exists

**Don't do this** (when file has clear dependencies):
```
* Dependencies: TODO
```

**Do this instead**:
```
* Dependencies: jsonwebtoken, bcrypt, node:crypto
```
