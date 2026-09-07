# Email-only auth (drop `username`) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the `username` column/concept from Abogadazo entirely — login and registration become email + password (+ name), fixing a registration bug where an email address can never pass the username validation pattern.

**Architecture:** Drop `User.username` from the SQLAlchemy model and add an Alembic migration to drop the column; change `LoginRequest`/`RegisterRequest`/`UserPublic` Pydantic schemas and the `/auth/login` and `/auth/register` routes to key on `email` instead; update every frontend file that sends or displays `username`/`usuario` to use `email` directly, with no new field added to any form.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pydantic (backend); React (frontend). No new dependencies.

**Spec:** `docs/superpowers/specs/2026-09-06-email-only-auth-design.md`

## Global Constraints

- Password minimum length: 12 → 8 characters (`RegisterRequest.password`, `ProfileUpdate.password`).
- JWT subject stays `str(user.id)` — do not touch `app/core/security.py`.
- Do not touch `database/schema.sql` (stale legacy document, out of scope per spec).
- Do not touch `userService.deleteUser` (pre-existing stub, out of scope per spec).
- **Known environment issue:** in this environment, any Bash command containing the token `uv` (e.g. `uv run pytest`, `uv run alembic upgrade head`) is currently blocked by a stuck Semgrep Guardian plugin bug, unrelated to this feature. If a verification step below fails with "Not logged into Semgrep Guardian", stop and ask the user to run that exact command themselves in their own terminal, then paste back the output before continuing.

---

### Task 1: Backend — drop `username`, key auth on email

**Files:**
- Modify: `backend/app/models/domain.py` (the `User` class, currently line 23 has the `username` column)
- Create: `backend/migrations/versions/20260906_02_drop_username.py`
- Modify: `backend/app/schemas/api.py` (`RegisterRequest`, `LoginRequest`, `UserPublic`, `ProfileUpdate`)
- Modify: `backend/app/api/routes.py` (`register`, `login`)
- Modify: `backend/tests/test_api.py`

**Interfaces:**
- Produces: `POST /api/v1/auth/register` body `{username, first_name, last_name, email, password}` → `{first_name, last_name, email, password}` (no `username`).
- Produces: `POST /api/v1/auth/login` body `{username, password}` → `{email, password}`.
- Produces: `UserPublic` response no longer has a `username` field.
- Consumes: nothing from other tasks (this task is backend-only and self-contained).

- [ ] **Step 1: Update the tests to the new email-based contract (red)**

Edit `backend/tests/test_api.py` in full — replace its contents with:

```python
from app.core.security import create_access_token, hash_password
from app.models.domain import AuthorizedAgent, Consultation, LegalResponse, User, UserRole


def register(client, email="ana@example.com"):
    return client.post("/api/v1/auth/register", json={"first_name": "Ana", "last_name": "López", "email": email, "password": "a secure password"})


def auth_headers(client):
    login = client.post("/api/v1/auth/login", json={"email": "ana@example.com", "password": "a secure password"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_health(client):
    http, _ = client
    assert http.get("/api/v1/health").json() == {"status": "ok"}


def test_registration_login_and_no_self_assigned_admin(client):
    http, _ = client
    result = register(http)
    assert result.status_code == 201
    assert result.json()["role"] == "user"
    assert "username" not in result.json()
    assert http.post("/api/v1/auth/login", json={"email": "ana@example.com", "password": "wrong"}).status_code == 401
    assert http.post("/api/v1/auth/login", json={"email": "ana@example.com", "password": "a secure password"}).status_code == 200
    assert http.get("/api/v1/admin/users", headers=auth_headers(http)).status_code == 403


def test_registration_rejects_duplicate_email(client):
    http, _ = client
    assert register(http).status_code == 201
    duplicate = register(http)
    assert duplicate.status_code == 409


def test_registration_rejects_short_password(client):
    http, _ = client
    response = http.post("/api/v1/auth/register", json={"first_name": "Ana", "last_name": "López", "email": "short@example.com", "password": "short1"})
    assert response.status_code == 422


def test_profile_requires_authentication_and_can_be_updated(client):
    http, _ = client
    assert http.get("/api/v1/users/me").status_code == 401
    register(http)
    response = http.patch("/api/v1/users/me", headers=auth_headers(http), json={"first_name": "Ana María"})
    assert response.status_code == 200
    assert response.json()["first_name"] == "Ana María"


def test_agent_lookup_is_authenticated_and_recorded(client):
    http, factory = client
    register(http)
    with factory() as db:
        db.add(AuthorizedAgent(plate="ABC123", name="Oficial Ejemplo"))
        db.commit()
    assert http.get("/api/v1/agents/ABC123").status_code == 401
    response = http.get("/api/v1/agents/abc123", headers=auth_headers(http))
    assert response.status_code == 200
    assert response.json()["plate"] == "ABC123"


def test_feedback_only_for_response_owner_and_valid_rating(client):
    http, factory = client
    register(http)
    register(http, "other@example.com")
    with factory() as db:
        owner = db.query(User).filter_by(email="ana@example.com").one()
        consultation = Consultation(user_id=owner.id, question="Pregunta")
        db.add(consultation); db.flush()
        response = LegalResponse(consultation_id=consultation.id, text="Respuesta", category="general")
        db.add(response); db.commit(); response_id = response.id
    other_login = http.post("/api/v1/auth/login", json={"email": "other@example.com", "password": "a secure password"}).json()
    headers = {"Authorization": f"Bearer {other_login['access_token']}"}
    assert http.put(f"/api/v1/legal-responses/{response_id}/feedback", headers=headers, json={"response_id": response_id, "rating": 5}).status_code == 403
    assert http.put(f"/api/v1/legal-responses/{response_id}/feedback", headers=auth_headers(http), json={"response_id": response_id, "rating": 6}).status_code == 422
    assert http.put(f"/api/v1/legal-responses/{response_id}/feedback", headers=auth_headers(http), json={"response_id": response_id, "rating": 5}).status_code == 204
```

- [ ] **Step 2: Run the tests to confirm they fail**

Run (from `backend/`): `uv run pytest -v`
Expected: failures — `register()` posts no `username` but `RegisterRequest` still requires it (422), and `login()` posts `email` but `LoginRequest` still expects `username` (422). If this command is blocked by the Semgrep Guardian issue described in Global Constraints, ask the user to run it and paste the output.

- [ ] **Step 3: Drop `username` from the `User` model**

In `backend/app/models/domain.py`, remove this line from the `User` class:

```python
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
```

- [ ] **Step 4: Write the migration**

Create `backend/migrations/versions/20260906_02_drop_username.py`:

```python
"""drop username from users

Revision ID: 20260906_02
Revises: 20260727_01
Create Date: 2026-09-06
"""
from alembic import op
import sqlalchemy as sa

revision = "20260906_02"
down_revision = "20260727_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_users_username", table_name="users")
    op.drop_constraint("users_username_key", "users", type_="unique")
    op.drop_column("users", "username")


def downgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(100), nullable=True))
    op.create_unique_constraint("users_username_key", "users", ["username"])
    op.create_index("ix_users_username", "users", ["username"])
```

Note: `users_username_key` is Postgres's default auto-generated name for the
unnamed `UniqueConstraint("username")` in the initial migration
(`<table>_<column>_key`). If `upgrade()` fails on the `drop_constraint` line,
find the real name with:
`docker exec abogadazo-postgres psql -U abogadazo -d abogadazo -c "\d users"`
and use that name instead.

- [ ] **Step 5: Update the Pydantic schemas**

In `backend/app/schemas/api.py`, replace:

```python
class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100, pattern=r"^[A-Za-z0-9_.-]+$")
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str
```

with:

```python
class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
```

Then remove `username: str` from `UserPublic`:

```python
class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime
```

And lower `ProfileUpdate.password`'s minimum:

```python
    password: str | None = Field(default=None, min_length=8, max_length=128)
```

- [ ] **Step 6: Update the register/login routes**

In `backend/app/api/routes.py`, replace:

```python
@router.post("/auth/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: DbSession) -> User:
    exists = db.scalar(select(User.id).where((User.username == payload.username) | (User.email == str(payload.email))))
    if exists:
        raise HTTPException(status_code=409, detail="Username or email is already registered")
    user = User(username=payload.username, first_name=payload.first_name, last_name=payload.last_name, email=str(payload.email), password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    user = db.scalar(select(User).where(User.username == payload.username))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token(str(user.id)), user=user)
```

with:

```python
@router.post("/auth/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: DbSession) -> User:
    exists = db.scalar(select(User.id).where(User.email == str(payload.email)))
    if exists:
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = User(first_name=payload.first_name, last_name=payload.last_name, email=str(payload.email), password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == str(payload.email)))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token(str(user.id)), user=user)
```

- [ ] **Step 7: Run the tests to confirm they pass**

Run (from `backend/`): `uv run pytest -v`
Expected: all tests PASS, including the two new ones (`test_registration_rejects_duplicate_email`, `test_registration_rejects_short_password`).

- [ ] **Step 8: Apply the migration to the local dev database**

Run (from `backend/`): `uv run alembic upgrade head`
Expected: migration `20260906_02` applies with no errors. (This drops the `username` column from the real dev `users` table — any existing local accounts keep their id/email/name/password, per the approved spec.)

- [ ] **Step 9: Commit**

```bash
git add backend/app/models/domain.py backend/migrations/versions/20260906_02_drop_username.py backend/app/schemas/api.py backend/app/api/routes.py backend/tests/test_api.py
git commit -m "feat: drop username, key auth on email

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 2: Frontend — email-only login/register forms

**Files:**
- Modify: `frontend/src/services/authService.js`
- Modify: `frontend/src/services/userService.js`
- Modify: `frontend/src/pages/Login.js`
- Modify: `frontend/src/pages/Singin.js`
- Modify: `frontend/src/pages/AdministrarUsuarios.js`
- Modify: `frontend/src/pages/GestionarPerfil.js`

**Interfaces:**
- Consumes: the Task 1 backend contract — `POST /auth/login` takes `{email, password}`; `POST /auth/register` takes `{first_name, last_name, email, password}`; `UserPublic`/admin list responses have no `username` field.
- Produces: nothing consumed by a later task (this is the last task).

- [ ] **Step 1: `authService.js` — send `email` on login**

In `frontend/src/services/authService.js`, replace:

```javascript
    const response = await axios.post(`${API_URL}/auth/login`, { username: credentials.username, password: credentials.password });
```

with:

```javascript
    const response = await axios.post(`${API_URL}/auth/login`, { email: credentials.email, password: credentials.password });
```

- [ ] **Step 2: `userService.js` — stop sending/reading `username`**

In `frontend/src/services/userService.js`, replace:

```javascript
    body: JSON.stringify({ username: userData.usuario, first_name: userData.nombre, last_name: userData.apellido, email: userData.email, password: userData.password }),
```

with:

```javascript
    body: JSON.stringify({ first_name: userData.nombre, last_name: userData.apellido, email: userData.email, password: userData.password }),
```

And replace:

```javascript
  return { clientes: users.map((user) => ({ ...user, usuario: user.username, nombre: user.first_name, apellido: user.last_name, rol: user.role })) };
```

with:

```javascript
  return { clientes: users.map((user) => ({ ...user, nombre: user.first_name, apellido: user.last_name, rol: user.role })) };
```

- [ ] **Step 3: `Login.js` — rename the `username` field to `email`**

In `frontend/src/pages/Login.js`, replace:

```javascript
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
```

with:

```javascript
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
```

And replace the email `Input`:

```javascript
              <Input
                label="Correo electrónico"
                id="username"
                type="text"
                value={formData.username}
                onChange={handleChange}
                required
                className="tw-mb-4"
              />
```

with:

```javascript
              <Input
                label="Correo electrónico"
                id="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                required
                className="tw-mb-4"
              />
```

- [ ] **Step 4: `Singin.js` — remove the `usuario` field and add a password hint**

In `frontend/src/pages/Singin.js`, replace:

```javascript
    const [formData, setFormData] = useState({
        usuario: '',
        nombre: '',
        apellido: '',
        email: '',
        password: '',
        confirmPassword: '',
        rol: 'usuario'
    });
```

with:

```javascript
    const [formData, setFormData] = useState({
        nombre: '',
        apellido: '',
        email: '',
        password: '',
        confirmPassword: '',
        rol: 'usuario'
    });
```

Replace:

```javascript
            // Usamos el servicio importado en lugar de fetch directo
            await createUser({
                ...formData,
                usuario: formData.usuario || formData.email
            });
```

with:

```javascript
            // Usamos el servicio importado en lugar de fetch directo
            await createUser(formData);
```

Add a password-length hint — replace:

```javascript
                            <Input
                                label="Contraseña"
                                id="password"
                                type="password"
                                value={formData.password}
                                onChange={handleChange}
                                required
                                className="tw-mb-4"
                            />
```

with:

```javascript
                            <Input
                                label="Contraseña"
                                id="password"
                                type="password"
                                value={formData.password}
                                onChange={handleChange}
                                required
                                minLength={8}
                                className="tw-mb-1"
                            />
                            <p className="tw-text-xs tw-text-ink-soft tw-mt-0 tw-mb-4">
                                Mínimo 8 caracteres.
                            </p>
```

- [ ] **Step 5: `AdministrarUsuarios.js` — use `.email` instead of `.usuario`**

Replace:

```javascript
        await deleteUser(userToDelete.usuario); // Asegúrate que este campo es el identificador
        setUsers(users.filter((u) => u.usuario !== userToDelete.usuario));
```

with:

```javascript
        await deleteUser(userToDelete.email); // Asegúrate que este campo es el identificador
        setUsers(users.filter((u) => u.email !== userToDelete.email));
```

Replace:

```javascript
    setEditData({ usuario:user.email, nombre: user.nombre, apellido: user.apellido, email: user.email, rol: user.rol });
```

with:

```javascript
    setEditData({ nombre: user.nombre, apellido: user.apellido, email: user.email, rol: user.rol });
```

Replace:

```javascript
                        onChange={(e) => setEditData({ ...editData, email: e.target.value ,usuario: e.target.value})}
```

with:

```javascript
                        onChange={(e) => setEditData({ ...editData, email: e.target.value })}
```

- [ ] **Step 6: `GestionarPerfil.js` — drop the dead `usuario` field**

In `frontend/src/pages/GestionarPerfil.js`, replace:

```javascript
            const updatedData = {             
                usuario: storedUser.correo,
                nombre: inputs.nombre,
                apellido: inputs.apellido,
                rol: storedUser.rol,
                email: storedUser.correo
            };
```

with:

```javascript
            const updatedData = {
                nombre: inputs.nombre,
                apellido: inputs.apellido,
                rol: storedUser.rol,
                email: storedUser.correo
            };
```

- [ ] **Step 7: Verify manually**

The frontend has no automated tests for these pages. With the Task 1 backend running (`uv run uvicorn app.main:app --reload`) and the frontend dev server up (`npm start`):
1. Go to `/Sing-in`, register a new account with a password of 8-11 characters (something that used to fail). Expect success, no `username`-pattern error.
2. Go to `/Login`, log in with that same email/password. Expect redirect to `/Bienvenida`.
3. As an admin user, open `/AdministrarUsuario` and confirm the user list and edit modal still show the right email with no console errors (open devtools console).

If any of these fail, report the exact error text before moving on — do not guess a fix blind.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/services/authService.js frontend/src/services/userService.js frontend/src/pages/Login.js frontend/src/pages/Singin.js frontend/src/pages/AdministrarUsuarios.js frontend/src/pages/GestionarPerfil.js
git commit -m "feat: switch frontend auth forms to email-only

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```
