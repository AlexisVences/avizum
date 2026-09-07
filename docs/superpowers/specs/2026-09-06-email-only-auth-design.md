# Email-only auth (drop `username`)

## Problem

Registration is broken today: the signup form has no real "usuario" field, so
it always falls back to sending the raw email address as `username`
(`usuario: formData.usuario || formData.email` in `Singin.js`). The backend's
`RegisterRequest.username` requires `^[A-Za-z0-9_.-]+$`, which an email
address (containing `@`) can never satisfy — every registration attempt has
always failed validation with a confusing, unrelated-looking error.

Separately, `password` requires a 12-character minimum with no client-side
hint, so users also hit a length error with no warning before submitting.

The `username` concept is otherwise unused: the admin user-management page
already treats "usuario" as a synonym for email everywhere it appears
(`editData.usuario = user.email`), and the JWT subject is the user's `id`,
never the username. It's dead weight that actively causes a bug.

## Decision

Drop `username` as a concept entirely. Login and registration become
email + password (+ first/last name for registration). Lower the password
minimum from 12 to 8 characters, and show the requirement in the form before
submit. Existing local dev accounts do not need to be preserved (confirmed
with the user) — the migration only drops a column, so no other user data is
lost regardless.

## Backend changes

**`app/models/domain.py`** — remove `User.username` (the `unique=True,
index=True` column). `email` remains the unique, indexed identifier.

**New Alembic migration** (`backend/migrations/versions/`) — `DROP COLUMN
username` on `users`. Single, reversible `op.drop_column` /
`op.add_column` pair in `upgrade`/`downgrade`. This is the second migration
in the project (first is `20260727_01_initial_modular_monolith.py`).

**`app/schemas/api.py`**:
- `RegisterRequest`: remove the `username` field entirely.
- `LoginRequest`: replace `username: str` with `email: EmailStr`.
- `UserPublic`: remove `username` from the response.
- `RegisterRequest.password` / `ProfileUpdate.password`: `min_length=12` →
  `min_length=8`.

**`app/api/routes.py`**:
- `register`: duplicate-check becomes `select(User.id).where(User.email ==
  str(payload.email))` only (no more OR'd username check). Construct `User(...)`
  without `username=`.
- `login`: look up `select(User).where(User.email == payload.email)` instead
  of matching on `username`. `create_access_token(str(user.id))` is unchanged
  — the JWT subject was never the username, so no token/security-module
  changes are needed anywhere.

`database/schema.sql` is not touched — it already documents the legacy
pre-FastAPI `usuario`/`consulta` schema (per `CLAUDE.md`, superseded and not
auto-mirrored), so it's already out of sync with the real models and out of
scope here.

## Frontend changes

- **`services/authService.js`** — `login(credentials)` posts `{ email:
  credentials.email, password: credentials.password }` instead of
  `{ username, password }`.
- **`pages/Login.js`** — rename the `username` state field/id to `email`
  (`type="email"`). No visible change — the label already read "Correo
  electrónico".
- **`pages/Singin.js`** — delete the `usuario` field from `formData` and the
  `usuario: formData.usuario || formData.email` fallback in `handleSubmit`;
  `createUser` is called with just `{ nombre, apellido, email, password }`.
  Add a visible hint under the password field ("Mínimo 8 caracteres").
- **`services/userService.js`** — `createUser` stops sending `username:
  userData.usuario` in the request body. `getAllUsers` stops mapping
  `usuario: user.username` (field no longer exists in the API response).
- **`pages/AdministrarUsuarios.js`** — replace the now-nonexistent `.usuario`
  references (delete-by-identifier, edit-form prefill) with `.email`, which
  is what they already held in practice.

## Tests

**`backend/tests/test_api.py`**:
- `register()` helper drops the `username` parameter.
- All `{"username": ...}` login payloads become `{"email": ...}`.
- The ownership test's `db.query(User).filter_by(username="ana")` becomes
  `.filter_by(email="ana@example.com")`.
- Add/confirm coverage: duplicate-email registration still returns 409;
  login by email with correct/incorrect password still returns 200/401.

Run `uv run pytest` after the change (per `CLAUDE.md`) — the user runs this
themselves, since `uv` invocations are currently blocked in this session by
an unrelated, unresolved Semgrep Guardian plugin bug.

## Out of scope

- No changes to JWT/token handling — confirmed unaffected.
- No OAuth/"login with Google" — mentioned by the user as a possible later
  addition, not part of this change.
- No changes to `database/schema.sql` (already-stale legacy document).
- No fix to `userService.deleteUser` (already a stub that throws
  "not available" — unrelated pre-existing gap, not touched here).
