# Fase 0 — Datos oficiales: plan de implementación

> **Estado: COMPLETADO el 2026-10-09** (commits `c71800b`..`767ee9d`). Las desviaciones respecto a este plan (Reglamento desde la SSC, acuerdo descargado de la SSC con `pages: [2, 28]`, cadena TLS completa, sin entrada del decreto 30-jun-2026, correcciones de la revisión final) están en el spec maestro §15. No volver a ejecutarlo.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** registrar las fuentes legales oficiales vigentes (con hash y versión) y reconstruir el registro de agentes facultados a partir del Acuerdo 30/2026, con búsqueda por placa o por nombre aproximado y el link a la fuente oficial siempre visible.

**Architecture:** una tabla `official_sources` versiona cada documento oficial (URL, SHA-256, fecha de reforma y bandera `is_current`). Un manifiesto `data/sources.json` declara las fuentes; `scripts.fetch_sources` las descarga con TLS estricto y las registra. `scripts.import_agents` extrae el texto del PDF del acuerdo, lo parsea con un parser puro y validado por conteos, y reemplaza `authorized_agents`. `GET /api/v1/agents/search` busca por placa exacta o por nombre con `pg_trgm`, y el frontend muestra el tipo de autorización y la fuente.

**Tech Stack:** FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 16 (imagen `pgvector/pgvector:pg16`, extensión `pg_trgm`), PyMuPDF (solo scripts offline, grupo `ingest`), React 19 + Tailwind (prefijo `tw-`), Jest/RTL.

**Spec:** `docs/superpowers/specs/2026-10-08-asistente-legal-design.md` (§3, §5 `official_sources` y `authorized_agents`, §9 `GET /agents/search`, §10 `ConsultarAgenteTransito`, §13 Fase 0).

## Global Constraints

- La información de agentes proviene **solo** de la Gaceta Oficial (Acuerdo 30/2026). Nada de notas de prensa. La corporación y las alcaldías se llenan solo si el texto oficial las da por elemento.
- Slug estable de la fuente de agentes: `acuerdo-agentes-transito`. Conteos esperados del Acuerdo 30/2026: `via_publica` = 717 y `sistemas_tecnologicos` = 570. La importación falla si no cuadran.
- Redacción: "No aparece en la lista vigente". **Nunca** afirmar que un policía es falso.
- Si el registro no está cargado (no hay fuente vigente), **nunca** decir "no aparece"; decir que el registro no está disponible.
- La verificación TLS **nunca** se desactiva (nada de `verify=False`, `curl -k` ni `CERT_NONE` en código).
- Las pruebas no tocan la red.
- Python ≥ 3.11, ruff `line-length = 100`, handlers finos y lógica en `app/services/`.
- UI en español, clases Tailwind con prefijo `tw-`.
- Commits en formato Conventional Commits, terminados con `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- `legal_ai.py`, `consultations`, `legal_responses` y `feedback` **no** se tocan en esta fase (se reemplazan en la Fase 2).

## Review Focus

1. **Registro vacío o no importado:** la API devuelve `source: null` y la UI dice "registro no disponible", nunca "no aparece" (pruebas en las Tasks 2 y 3).
2. **Nombres con acentos o ñ y placas con espacios o guiones:** "Yáñez Gómez" encuentra "YAÑEZ GOMEZ VANESSA"; "1151 407" encuentra la placa 1151407 (Tasks 1 y 2).
3. **Ruido del PDF:** números de página que coinciden con el número de fila esperado, encabezados "GACETA OFICIAL…" y nombres partidos en dos líneas (Task 5).
4. **Re-ejecución:** volver a correr `fetch_sources` con el mismo archivo no crea versión nueva, y `import_agents` reemplaza en lugar de duplicar (Tasks 4 y 6).
5. **Misma placa en ambas listas:** se devuelven dos resultados, cada uno con su propia etiqueta (Tasks 2 y 3).

---

## Mapa de archivos

| Archivo | Responsabilidad |
|---|---|
| `docker-compose.yml` | Imagen `pgvector/pgvector:pg16` (incluye `pg_trgm`) |
| `backend/app/models/domain.py` | `OfficialSource`, `AuthorizationType`, `AuthorizedAgent` reconstruido |
| `backend/migrations/versions/20261008_03_official_sources_and_agents.py` | Esquema de la fase |
| `backend/app/services/agents_registry.py` | Normalización, búsqueda de agentes y slug de la fuente |
| `backend/app/services/sources.py` | Manifiesto, hash y versionado de fuentes (sin red) |
| `backend/app/services/acuerdo_parser.py` | Parser puro del texto del acuerdo + validación de conteos |
| `backend/app/services/agents_import.py` | Reemplazo transaccional de `authorized_agents` |
| `backend/scripts/fetch_sources.py` | Descarga con TLS estricto y registro de fuentes |
| `backend/scripts/certs/lets-encrypt-yr2.pem` | Intermedio público que el servidor de la Consejería no envía |
| `backend/scripts/import_agents.py` | PDF → parser → reemplazo |
| `backend/app/schemas/api.py`, `backend/app/api/routes.py` | `GET /agents/search` |
| `data/sources.json` | Manifiesto de fuentes oficiales |
| `frontend/src/services/agentesService.js` | `buscarAgentes(consulta)` |
| `frontend/src/components/agentes/ResultadoBusquedaAgentes.js` | Render compartido de resultados y fuente |
| `frontend/src/pages/ConsultarAgenteTransito.js`, `frontend/src/pages/Home.js` | Usan el nuevo servicio y el componente |

---

### Task 0: Base de datos local limpia con pgvector

**Files:**
- Modify: `docker-compose.yml`
- Modify (local, no versionado): `backend/.env`

**Interfaces:**
- Produces: Postgres local con credenciales `avizum` / `change-me`, base `avizum`, imagen con `pg_trgm` y `vector` disponibles.

- [ ] **Step 1: Cambiar la imagen**

En `docker-compose.yml`, reemplaza `image: postgres:16-alpine` por:

```yaml
    image: pgvector/pgvector:pg16
```

- [ ] **Step 2: Retirar el contenedor viejo y su volumen (el cliente autorizó borrar todos los datos)**

```bash
docker inspect abogadazo-postgres --format '{{range .Mounts}}{{.Name}}{{end}}'   # anota el volumen
docker stop abogadazo-postgres && docker rm abogadazo-postgres
docker volume rm <volumen-anotado>
```

- [ ] **Step 3: Levantar la base nueva y apuntar `.env`**

```bash
cd /home/alexis/Projects/abogadazo && docker compose up -d db
sed -i 's#^DATABASE_URL=.*#DATABASE_URL=postgresql+psycopg://avizum:change-me@localhost:5432/avizum#' backend/.env
cd backend && uv run alembic upgrade head && uv run pytest -q
```

Expected: las migraciones corren y las pruebas actuales pasan.

- [ ] **Step 4: Commit**

```bash
git add docker-compose.yml
git commit -m "chore: switch local Postgres image to pgvector/pgvector:pg16

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Avísale al cliente que debe registrarse de nuevo y correr `uv run python -m scripts.promote_admin <correo>`.

---

### Task 1: Esquema de fuentes oficiales y registro de agentes

**Files:**
- Modify: `backend/app/models/domain.py`
- Modify: `backend/app/db/base.py`
- Create: `backend/migrations/versions/20261008_03_official_sources_and_agents.py`
- Create: `backend/app/services/agents_registry.py`
- Modify: `backend/tests/conftest.py`
- Create: `backend/tests/factories.py`
- Create: `backend/tests/test_agents_registry.py`
- Modify: `backend/app/api/routes.py` (quitar `GET /agents/{plate}`)
- Modify: `backend/app/schemas/api.py` (quitar `AgentPublic` viejo)
- Modify: `backend/tests/test_api.py` (quitar las 2 pruebas del endpoint viejo)

**Interfaces:**
- Produces:
  - `OfficialSource(id, slug, title, kind, url, sha256, last_reform_date: date | None, retrieved_at, is_current: bool)`
  - `AuthorizationType.VIA_PUBLICA = "via_publica"`, `AuthorizationType.SISTEMAS_TECNOLOGICOS = "sistemas_tecnologicos"`
  - `AuthorizedAgent(id, plate, full_name, name_search, authorization_type, corporation: str | None, alcaldias: list[str] | None, source_id)`
  - `agents_registry.AGENTS_SOURCE_SLUG = "acuerdo-agentes-transito"`, `normalize_name(value: str) -> str`, `normalize_plate(value: str) -> str`
  - `tests/factories.py`: `add_agents_source(db, *, slug=AGENTS_SOURCE_SLUG, sha256="a"*64, is_current=True) -> OfficialSource` y `add_agent(db, source, plate, full_name, authorization_type=AuthorizationType.VIA_PUBLICA) -> AuthorizedAgent`

- [ ] **Step 1: Pruebas de normalización y de restricciones (fallan)**

`backend/tests/test_agents_registry.py`:

```python
import pytest
from sqlalchemy.exc import IntegrityError

from app.models.domain import AuthorizationType
from app.services.agents_registry import normalize_name, normalize_plate
from tests.factories import add_agent, add_agents_source


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("YAÑEZ GOMEZ VANESSA", "yanez gomez vanessa"),
        ("  Yáñez   Gómez ", "yanez gomez"),
        ("AGUSTÍN CRUZ SANTIAGO", "agustin cruz santiago"),
        ("O'HARA-LÓPEZ", "o hara lopez"),
    ],
)
def test_normalize_name(raw, expected):
    assert normalize_name(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("1151 407", "1151407"), (" 57196 ", "57196"), ("abc-123", "ABC123")],
)
def test_normalize_plate(raw, expected):
    assert normalize_plate(raw) == expected


def test_same_plate_can_appear_once_per_authorization_type(client):
    _, factory = client
    with factory() as db:
        source = add_agents_source(db)
        add_agent(db, source, "1151407", "ABARCA CASTRO YANELI")
        add_agent(db, source, "1151407", "ABARCA CASTRO YANELI", AuthorizationType.SISTEMAS_TECNOLOGICOS)
        db.commit()
        add_agent(db, source, "1151407", "ABARCA CASTRO YANELI")
        with pytest.raises(IntegrityError):
            db.commit()


def test_only_one_current_version_per_source_slug(client):
    _, factory = client
    with factory() as db:
        add_agents_source(db, sha256="a" * 64)
        db.commit()
        add_agents_source(db, sha256="b" * 64)
        with pytest.raises(IntegrityError):
            db.commit()
```

`backend/tests/factories.py`:

```python
from datetime import date

from sqlalchemy.orm import Session

from app.models.domain import AuthorizationType, AuthorizedAgent, OfficialSource
from app.services.agents_registry import AGENTS_SOURCE_SLUG, normalize_name


def add_agents_source(
    db: Session, *, slug: str = AGENTS_SOURCE_SLUG, sha256: str = "a" * 64, is_current: bool = True
) -> OfficialSource:
    source = OfficialSource(
        slug=slug,
        title="Acuerdo 30/2026 (GOCDMX 10-jun-2026)",
        kind="acuerdo",
        url="https://data.consejeria.cdmx.gob.mx/acuerdo-30-2026.pdf",
        sha256=sha256,
        last_reform_date=date(2026, 6, 10),
        is_current=is_current,
    )
    db.add(source)
    db.flush()
    return source


def add_agent(
    db: Session,
    source: OfficialSource,
    plate: str,
    full_name: str,
    authorization_type: AuthorizationType = AuthorizationType.VIA_PUBLICA,
) -> AuthorizedAgent:
    agent = AuthorizedAgent(
        plate=plate,
        full_name=full_name,
        name_search=normalize_name(full_name),
        authorization_type=authorization_type,
        source_id=source.id,
    )
    db.add(agent)
    db.flush()
    return agent
```

- [ ] **Step 2: Correrlas y verificar que fallan**

Run: `cd backend && uv run pytest tests/test_agents_registry.py -v`
Expected: FAIL con `ImportError` (no existen `AuthorizationType` ni `agents_registry`).

- [ ] **Step 3: Modelos**

En `backend/app/models/domain.py`, actualiza los imports:

```python
import enum
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column
```

Reemplaza la clase `AuthorizedAgent` completa por:

```python
class AuthorizationType(str, enum.Enum):
    VIA_PUBLICA = "via_publica"
    SISTEMAS_TECNOLOGICOS = "sistemas_tecnologicos"


class OfficialSource(Base):
    """One downloaded version of an official document; exactly one version per slug is current."""

    __tablename__ = "official_sources"
    __table_args__ = (
        UniqueConstraint("slug", "sha256", name="uq_official_sources_slug_sha256"),
        Index("uq_official_sources_current_slug", "slug", unique=True, postgresql_where=text("is_current")),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(String(300))
    kind: Mapped[str] = mapped_column(String(20))
    url: Mapped[str] = mapped_column(String(1000))
    sha256: Mapped[str] = mapped_column(String(64))
    last_reform_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_current: Mapped[bool] = mapped_column(default=True, server_default=text("true"), nullable=False)


class AuthorizedAgent(Timestamped, Base):
    __tablename__ = "authorized_agents"
    __table_args__ = (
        UniqueConstraint("plate", "authorization_type", name="uq_authorized_agents_plate_type"),
        Index(
            "ix_authorized_agents_name_search_trgm",
            "name_search",
            postgresql_using="gin",
            postgresql_ops={"name_search": "gin_trgm_ops"},
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    plate: Mapped[str] = mapped_column(String(50), index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    name_search: Mapped[str] = mapped_column(String(255))
    authorization_type: Mapped[AuthorizationType] = mapped_column(
        Enum(AuthorizationType, name="agent_authorization_type", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    corporation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    alcaldias: Mapped[list[str] | None] = mapped_column(ARRAY(String(100)), nullable=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("official_sources.id"), nullable=False, index=True)
```

En `backend/app/db/base.py`:

```python
from app.models.domain import AgentLookup, AuthorizedAgent, Consultation, Feedback, LegalResponse, OfficialSource, User

__all__ = ["User", "OfficialSource", "AuthorizedAgent", "AgentLookup", "Consultation", "LegalResponse", "Feedback"]
```

- [ ] **Step 4: Normalización**

`backend/app/services/agents_registry.py`:

```python
"""Authorized-agents registry: normalization and lookup against the official Gaceta list."""
import re
import unicodedata

AGENTS_SOURCE_SLUG = "acuerdo-agentes-transito"


def normalize_name(value: str) -> str:
    """Lowercase, strip accents (ñ → n) and punctuation, collapse whitespace."""
    decomposed = unicodedata.normalize("NFKD", value)
    without_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    letters_only = re.sub(r"[^a-z\s]", " ", without_accents.lower())
    return " ".join(letters_only.split())


def normalize_plate(value: str) -> str:
    return re.sub(r"[\s\-]", "", value).upper()
```

- [ ] **Step 5: Extensión `pg_trgm` en las pruebas**

En `backend/tests/conftest.py`, dentro del fixture `client`, justo antes de `Base.metadata.create_all(engine)`:

```python
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
```

- [ ] **Step 6: Quitar el endpoint viejo**

- En `backend/app/api/routes.py`, borra la función `lookup_agent` con su decorador `@router.get("/agents/{plate}", ...)`. Quita `AuthorizedAgent` del import de `app.models.domain` y `AgentPublic` del import de `app.schemas.api`.
- En `backend/app/schemas/api.py`, borra la clase `AgentPublic`.
- En `backend/tests/test_api.py`, borra `test_agent_lookup_is_public_and_records_anonymous_and_authenticated_lookups` y `test_agent_lookup_ignores_invalid_token_instead_of_rejecting`, y quita `AuthorizedAgent` del import de la línea 2 (`AgentLookup` se queda si `grep -n AgentLookup tests/test_api.py` aún lo muestra en uso; si no, quítalo también).

- [ ] **Step 7: Migración**

`backend/migrations/versions/20261008_03_official_sources_and_agents.py`:

```python
"""official sources registry and authorized agents rebuilt from Acuerdo 30/2026

Revision ID: 20261008_03
Revises: 20260906_02
Create Date: 2026-10-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261008_03"
down_revision = "20260906_02"
branch_labels = None
depends_on = None

authorization_type = postgresql.ENUM("via_publica", "sistemas_tecnologicos", name="agent_authorization_type", create_type=False)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.create_table(
        "official_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("last_reform_date", sa.Date(), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("slug", "sha256", name="uq_official_sources_slug_sha256"),
    )
    op.create_index("ix_official_sources_slug", "official_sources", ["slug"])
    op.create_index("uq_official_sources_current_slug", "official_sources", ["slug"], unique=True, postgresql_where=sa.text("is_current"))

    # The legacy registry (Acuerdo 40/2024, no source tracking) is discarded; lookups keep their history.
    op.drop_constraint("agent_lookups_agent_id_fkey", "agent_lookups", type_="foreignkey")
    op.execute("UPDATE agent_lookups SET agent_id = NULL")
    op.drop_index("ix_authorized_agents_plate", table_name="authorized_agents")
    op.drop_table("authorized_agents")

    bind = op.get_bind()
    postgresql.ENUM("via_publica", "sistemas_tecnologicos", name="agent_authorization_type").create(bind, checkfirst=True)
    op.create_table(
        "authorized_agents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plate", sa.String(50), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("name_search", sa.String(255), nullable=False),
        sa.Column("authorization_type", authorization_type, nullable=False),
        sa.Column("corporation", sa.String(100), nullable=True),
        sa.Column("alcaldias", postgresql.ARRAY(sa.String(100)), nullable=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("official_sources.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("plate", "authorization_type", name="uq_authorized_agents_plate_type"),
    )
    op.create_index("ix_authorized_agents_plate", "authorized_agents", ["plate"])
    op.create_index("ix_authorized_agents_source_id", "authorized_agents", ["source_id"])
    op.create_index(
        "ix_authorized_agents_name_search_trgm", "authorized_agents", ["name_search"],
        postgresql_using="gin", postgresql_ops={"name_search": "gin_trgm_ops"},
    )
    op.create_foreign_key("agent_lookups_agent_id_fkey", "agent_lookups", "authorized_agents", ["agent_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    op.drop_constraint("agent_lookups_agent_id_fkey", "agent_lookups", type_="foreignkey")
    op.execute("UPDATE agent_lookups SET agent_id = NULL")
    op.drop_table("authorized_agents")
    postgresql.ENUM(name="agent_authorization_type").drop(op.get_bind(), checkfirst=True)
    op.drop_table("official_sources")
    op.create_table(
        "authorized_agents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plate", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("plate"),
    )
    op.create_index("ix_authorized_agents_plate", "authorized_agents", ["plate"])
    op.create_foreign_key("agent_lookups_agent_id_fkey", "agent_lookups", "authorized_agents", ["agent_id"], ["id"], ondelete="SET NULL")
```

- [ ] **Step 8: Correr las pruebas y la migración de ida y vuelta**

```bash
cd backend && uv run pytest -q
uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head
```

Expected: todas las pruebas pasan y la migración funciona en ambos sentidos.

- [ ] **Step 9: Commit**

```bash
git add backend/app backend/migrations backend/tests
git commit -m "feat: version official sources and rebuild authorized agents schema

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Búsqueda de agentes por placa o nombre (`GET /agents/search`)

**Files:**
- Modify: `backend/app/services/agents_registry.py`
- Modify: `backend/app/schemas/api.py`
- Modify: `backend/app/api/routes.py`
- Create: `backend/tests/test_agents_search.py`

**Interfaces:**
- Consumes: `normalize_name`, `normalize_plate`, `AGENTS_SOURCE_SLUG`, los modelos de la Task 1 y `tests/factories.py`.
- Produces:
  - `search_agents(db: Session, query: str) -> AgentSearch`
  - `AgentSearch(matches: list[AgentMatch], source: OfficialSource | None, matched_by: Literal["plate", "name"])`
  - `AgentMatch(agent: AuthorizedAgent, score: float)`
  - `current_agents_source(db) -> OfficialSource | None`
  - Respuesta HTTP:

```json
{
  "query": "string",
  "matched_by": "plate | name",
  "results": [
    {"plate": "string", "full_name": "string", "authorization_type": "via_publica | sistemas_tecnologicos",
     "corporation": "string | null", "alcaldias": ["string"] | null}
  ],
  "source": {"title": "string", "url": "string", "last_reform_date": "YYYY-MM-DD | null"} | null
}
```

- [ ] **Step 1: Pruebas (fallan)**

`backend/tests/test_agents_search.py`:

```python
from app.models.domain import AgentLookup, AuthorizationType, User
from tests.factories import add_agent, add_agents_source
from tests.test_api import auth_headers, register

URL = "/api/v1/agents/search"


def seed(factory):
    with factory() as db:
        source = add_agents_source(db)
        add_agent(db, source, "1168287", "ZAVALA TOVAR KARLA PAOLA")
        add_agent(db, source, "885312", "YAÑEZ GOMEZ VANESSA")
        add_agent(db, source, "1151298", "ZAVALA MATEHUALA MARLENE", AuthorizationType.SISTEMAS_TECNOLOGICOS)
        add_agent(db, source, "730249", "ZENIL OJEDA RICARDO")
        add_agent(db, source, "730249", "ZENIL OJEDA RICARDO", AuthorizationType.SISTEMAS_TECNOLOGICOS)
        db.commit()


def test_plate_search_is_public_and_includes_the_official_source(client):
    http, factory = client
    seed(factory)
    body = http.get(URL, params={"q": "1168287"}).json()
    assert body["matched_by"] == "plate"
    assert [r["full_name"] for r in body["results"]] == ["ZAVALA TOVAR KARLA PAOLA"]
    assert body["results"][0]["authorization_type"] == "via_publica"
    assert body["source"] == {
        "title": "Acuerdo 30/2026 (GOCDMX 10-jun-2026)",
        "url": "https://data.consejeria.cdmx.gob.mx/acuerdo-30-2026.pdf",
        "last_reform_date": "2026-06-10",
    }


def test_plate_search_tolerates_spaces_and_dashes(client):
    http, factory = client
    seed(factory)
    assert http.get(URL, params={"q": " 1168 287 "}).json()["results"][0]["plate"] == "1168287"
    assert http.get(URL, params={"q": "1168-287"}).json()["results"][0]["plate"] == "1168287"


def test_plate_in_both_lists_returns_one_result_per_authorization(client):
    http, factory = client
    seed(factory)
    results = http.get(URL, params={"q": "730249"}).json()["results"]
    assert sorted(r["authorization_type"] for r in results) == ["sistemas_tecnologicos", "via_publica"]


def test_name_search_handles_typos_partial_names_and_accents(client):
    http, factory = client
    seed(factory)
    def names(q):
        body = http.get(URL, params={"q": q}).json()
        assert body["matched_by"] == "name"
        return [r["full_name"] for r in body["results"]]
    assert names("zabala tobar karla")[0] == "ZAVALA TOVAR KARLA PAOLA"
    assert names("karla zavala")[0] == "ZAVALA TOVAR KARLA PAOLA"
    assert names("Yáñez Gómez") == ["YAÑEZ GOMEZ VANESSA"]
    assert names("juan perez") == []


def test_unknown_agent_returns_empty_results_with_source(client):
    http, factory = client
    seed(factory)
    body = http.get(URL, params={"q": "999999"}).json()
    assert body["results"] == []
    assert body["source"] is not None


def test_empty_registry_reports_missing_source_instead_of_not_found(client):
    http, _ = client
    body = http.get(URL, params={"q": "1168287"}).json()
    assert body["results"] == []
    assert body["source"] is None


def test_non_current_source_versions_are_not_reported(client):
    http, factory = client
    with factory() as db:
        add_agents_source(db, is_current=False)
        db.commit()
    assert http.get(URL, params={"q": "1168287"}).json()["source"] is None


def test_query_length_is_validated(client):
    http, _ = client
    assert http.get(URL, params={"q": "a"}).status_code == 422
    assert http.get(URL, params={"q": "a" * 101}).status_code == 422
    assert http.get(URL).status_code == 422


def test_lookups_are_recorded_for_anonymous_authenticated_and_invalid_tokens(client):
    http, factory = client
    seed(factory)
    register(http)
    assert http.get(URL, params={"q": "1168287"}).status_code == 200
    assert http.get(URL, params={"q": "1168287"}, headers=auth_headers(http)).status_code == 200
    invalid = http.get(URL, params={"q": "999999"}, headers={"Authorization": "Bearer not-a-real-token"})
    assert invalid.status_code == 200
    with factory() as db:
        user = db.query(User).filter_by(email="ana@example.com").one()
        lookups = db.query(AgentLookup).order_by(AgentLookup.id).all()
        assert [l.user_id for l in lookups] == [None, user.id, None]
        assert lookups[0].agent_id is not None
        assert lookups[2].agent_id is None


def test_legacy_plate_endpoint_is_gone(client):
    http, factory = client
    seed(factory)
    assert http.get("/api/v1/agents/1168287").status_code == 404
```

- [ ] **Step 2: Correrlas y verificar que fallan**

Run: `cd backend && uv run pytest tests/test_agents_search.py -v`
Expected: FAIL (404 en todas, porque la ruta no existe).

- [ ] **Step 3: Servicio de búsqueda**

Agrega a `backend/app/services/agents_registry.py`:

```python
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.domain import AuthorizedAgent, OfficialSource

PLATE_PATTERN = re.compile(r"[A-Z0-9]*\d[A-Z0-9]*")
# greatest(similarity, word_similarity) >= 0.45 keeps typos ("zabala tobar karla" = 0.50) and
# partial names ("karla zavala" = 0.67) while dropping unrelated names ("juan perez" ≈ 0.09).
NAME_MATCH_THRESHOLD = 0.45
MAX_RESULTS = 10


@dataclass(frozen=True)
class AgentMatch:
    agent: AuthorizedAgent
    score: float


@dataclass(frozen=True)
class AgentSearch:
    matches: list[AgentMatch]
    source: OfficialSource | None
    matched_by: Literal["plate", "name"]


def current_agents_source(db: Session) -> OfficialSource | None:
    return db.scalar(
        select(OfficialSource).where(OfficialSource.slug == AGENTS_SOURCE_SLUG, OfficialSource.is_current)
    )


def search_agents(db: Session, query: str) -> AgentSearch:
    source = current_agents_source(db)
    plate = normalize_plate(query)
    if PLATE_PATTERN.fullmatch(plate):
        agents = db.scalars(
            select(AuthorizedAgent)
            .where(AuthorizedAgent.plate == plate)
            .order_by(AuthorizedAgent.authorization_type)
        ).all()
        return AgentSearch([AgentMatch(agent, 1.0) for agent in agents], source, "plate")

    name = normalize_name(query)
    if not name:
        return AgentSearch([], source, "name")
    score = func.greatest(
        func.similarity(AuthorizedAgent.name_search, name),
        func.word_similarity(name, AuthorizedAgent.name_search),
    )
    rows = db.execute(
        select(AuthorizedAgent, score)
        .where(score >= NAME_MATCH_THRESHOLD)
        .order_by(score.desc(), AuthorizedAgent.full_name)
        .limit(MAX_RESULTS)
    ).all()
    return AgentSearch([AgentMatch(agent, float(s)) for agent, s in rows], source, "name")
```

Mueve los imports nuevos arriba, junto a `import re` e `import unicodedata`.

- [ ] **Step 4: Schemas**

En `backend/app/schemas/api.py`: agrega `from datetime import date, datetime` (reemplaza el import de `datetime`), `from typing import Literal`, importa `AuthorizationType` desde `app.models.domain` y agrega:

```python
class OfficialSourcePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: str
    url: str
    last_reform_date: date | None


class AgentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    plate: str
    full_name: str
    authorization_type: AuthorizationType
    corporation: str | None
    alcaldias: list[str] | None


class AgentSearchResponse(BaseModel):
    query: str
    matched_by: Literal["plate", "name"]
    results: list[AgentPublic]
    source: OfficialSourcePublic | None
```

- [ ] **Step 5: Ruta fina**

En `backend/app/api/routes.py`: agrega `from typing import Annotated`, `Query` al import de `fastapi`, `AgentPublic`, `AgentSearchResponse` y `OfficialSourcePublic` al import de schemas, y `from app.services.agents_registry import search_agents`. Donde estaba la ruta vieja:

```python
@router.get("/agents/search", response_model=AgentSearchResponse)
def search_authorized_agents(
    user: OptionalUser, db: DbSession, q: Annotated[str, Query(min_length=2, max_length=100)]
) -> AgentSearchResponse:
    search = search_agents(db, q)
    top_agent_id = search.matches[0].agent.id if search.matches else None
    db.add(AgentLookup(user_id=user.id if user else None, agent_id=top_agent_id))
    db.commit()
    return AgentSearchResponse(
        query=q,
        matched_by=search.matched_by,
        results=[AgentPublic.model_validate(match.agent) for match in search.matches],
        source=OfficialSourcePublic.model_validate(search.source) if search.source else None,
    )
```

- [ ] **Step 6: Correr las pruebas**

Run: `cd backend && uv run pytest -q`
Expected: todo pasa. Si alguna aserción de nombres falla por el umbral, ajusta solo `NAME_MATCH_THRESHOLD` (y su comentario) con valores medidos; no cambies las pruebas.

- [ ] **Step 7: Commit**

```bash
git add backend/app backend/tests
git commit -m "feat: search authorized agents by plate or fuzzy name with official source

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Frontend — verificación por placa o nombre, con la fuente siempre visible

**Files:**
- Modify: `frontend/src/services/agentesService.js`
- Create: `frontend/src/components/agentes/ResultadoBusquedaAgentes.js`
- Modify: `frontend/src/pages/ConsultarAgenteTransito.js`
- Modify: `frontend/src/pages/Home.js`
- Create: `frontend/src/components/agentes/__tests__/ResultadoBusquedaAgentes.test.js`
- Create: `frontend/src/pages/__tests__/ConsultarAgenteTransito.test.js`

**Interfaces:**
- Consumes: la respuesta `GET /agents/search` de la Task 2.
- Produces: `buscarAgentes(consulta: string) -> Promise<AgentSearchResponse>`, que lanza `Error` con mensaje en español si `!response.ok`. Componente `<ResultadoBusquedaAgentes resultado={AgentSearchResponse} />`.

- [ ] **Step 1: Pruebas del componente (fallan)**

`frontend/src/components/agentes/__tests__/ResultadoBusquedaAgentes.test.js`:

```javascript
import React from 'react';
import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import ResultadoBusquedaAgentes from '../ResultadoBusquedaAgentes';

jest.mock('react-router-dom', () => ({
    Link: ({ to, children, ...rest }) => <a href={to} {...rest}>{children}</a>,
}));

const fuente = { title: 'Acuerdo 30/2026 (GOCDMX 10-jun-2026)', url: 'https://gaceta.example/30-2026.pdf', last_reform_date: '2026-06-10' };

test('shows each authorization with its own label and the official source link', () => {
    render(<ResultadoBusquedaAgentes resultado={{ query: '730249', matched_by: 'plate', source: fuente, results: [
        { plate: '730249', full_name: 'ZENIL OJEDA RICARDO', authorization_type: 'via_publica', corporation: null, alcaldias: null },
        { plate: '730249', full_name: 'ZENIL OJEDA RICARDO', authorization_type: 'sistemas_tecnologicos', corporation: null, alcaldias: null },
    ] }} />);
    expect(screen.getByText('Vía pública')).toBeInTheDocument();
    expect(screen.getByText('Fotocívicas')).toBeInTheDocument();
    expect(screen.getByText(/infraccionar en la vía pública/i)).toBeInTheDocument();
    expect(screen.getByText(/sistemas tecnológicos/i)).toBeInTheDocument();
    const link = screen.getByRole('link', { name: fuente.title });
    expect(link).toHaveAttribute('href', fuente.url);
    expect(link).toHaveAttribute('target', '_blank');
});

test('shows corporation and alcaldías only when the official list provides them', () => {
    render(<ResultadoBusquedaAgentes resultado={{ query: 'x', matched_by: 'name', source: fuente, results: [
        { plate: '1', full_name: 'PEREZ LOPEZ ANA', authorization_type: 'via_publica', corporation: 'Policía Auxiliar', alcaldias: ['Cuauhtémoc', 'Iztapalapa'] },
    ] }} />);
    expect(screen.getByText(/Policía Auxiliar/)).toBeInTheDocument();
    expect(screen.getByText(/Cuauhtémoc, Iztapalapa/)).toBeInTheDocument();
});

test('not found: says "no aparece en la lista vigente" with guidance, never calls the officer fake', () => {
    render(<ResultadoBusquedaAgentes resultado={{ query: '999999', matched_by: 'plate', source: fuente, results: [] }} />);
    expect(screen.getByText(/no aparece en la lista vigente/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /asuntos internos/i })).toHaveAttribute('href', 'https://www.ssc.cdmx.gob.mx/organizacion-policial/direcciones-generales/direccion-general-de-asuntos-internos');
    expect(screen.getByRole('link', { name: /multas y fotocívicas/i })).toHaveAttribute('href', '/guia/multas-y-fotocivicas');
    expect(screen.getByRole('link', { name: fuente.title })).toBeInTheDocument();
    expect(screen.queryByText(/falso/i)).not.toBeInTheDocument();
});

test('registry unavailable: never claims the officer is missing from the list', () => {
    render(<ResultadoBusquedaAgentes resultado={{ query: '1', matched_by: 'plate', source: null, results: [] }} />);
    expect(screen.getByText(/registro oficial de agentes no está disponible/i)).toBeInTheDocument();
    expect(screen.queryByText(/no aparece/i)).not.toBeInTheDocument();
});
```

- [ ] **Step 2: Correrlas y verificar que fallan**

Run: `cd frontend && CI=true npx react-scripts test --watchAll=false src/components/agentes`
Expected: FAIL (no existe el módulo).

- [ ] **Step 3: Servicio**

Reemplaza todo `frontend/src/services/agentesService.js`:

```javascript
import { API_URL, authHeaders, extractErrorMessage } from './api';

export async function buscarAgentes(consulta) {
    const response = await fetch(`${API_URL}/agents/search?q=${encodeURIComponent(consulta.trim())}`, {
        headers: { ...authHeaders() },
    });
    const data = await response.json().catch(() => null);
    if (!response.ok) {
        throw new Error(extractErrorMessage(data, 'No pudimos consultar el registro de agentes. Intenta de nuevo.'));
    }
    return data;
}
```

- [ ] **Step 4: Componente de resultados**

`frontend/src/components/agentes/ResultadoBusquedaAgentes.js`:

```javascript
import React from 'react';
import { Link } from 'react-router-dom';
import Badge from '../ui/Badge';

const ASUNTOS_INTERNOS_URL = 'https://www.ssc.cdmx.gob.mx/organizacion-policial/direcciones-generales/direccion-general-de-asuntos-internos';

const AUTORIZACION = {
    via_publica: {
        etiqueta: 'Vía pública',
        variante: 'verified',
        texto: 'está facultado para infraccionar en la vía pública de la CDMX con equipo electrónico portátil.',
    },
    sistemas_tecnologicos: {
        etiqueta: 'Fotocívicas',
        variante: 'neutral',
        texto: 'está autorizado para firmar boletas emitidas mediante sistemas tecnológicos (fotocívicas).',
    },
};

const linkClase = 'tw-text-azul hover:tw-text-magenta tw-font-semibold';

const Fuente = ({ source }) => (
    <p className="tw-text-[0.78rem] tw-text-ink-soft tw-mt-3 tw-mb-0">
        Fuente oficial:{' '}
        <a href={source.url} target="_blank" rel="noopener noreferrer" className={linkClase}>
            {source.title}
        </a>
    </p>
);

const ResultadoBusquedaAgentes = ({ resultado }) => {
    const { results, source } = resultado;

    if (!source) {
        return (
            <div className="tw-bg-azul/5 tw-border tw-border-azul/20 tw-rounded tw-px-4 tw-py-3.5 tw-text-sm tw-text-ink-soft tw-leading-relaxed">
                El registro oficial de agentes no está disponible en este momento. Consulta directamente la
                Gaceta Oficial de la Ciudad de México.
            </div>
        );
    }

    if (results.length === 0) {
        return (
            <div className="tw-bg-azul/5 tw-border tw-border-azul/20 tw-rounded tw-px-4 tw-py-3.5 tw-text-sm tw-text-ink-soft tw-leading-relaxed">
                <p className="tw-m-0 tw-mb-2">
                    <strong className="tw-text-ink">No aparece en la lista vigente.</strong> Solo el personal
                    publicado en la Gaceta Oficial puede expedir y firmar boletas de tránsito.
                </p>
                <p className="tw-m-0 tw-mb-2">
                    Pide al agente su identificación y número de placa, y no entregues documentos sin que te
                    expida una boleta. Puedes reportar irregularidades ante{' '}
                    <a href={ASUNTOS_INTERNOS_URL} target="_blank" rel="noopener noreferrer" className={linkClase}>
                        Asuntos Internos de la SSC
                    </a>.
                </p>
                <p className="tw-m-0">
                    Si ya te impusieron una boleta, revisa cómo impugnarla en{' '}
                    <Link to="/guia/multas-y-fotocivicas" className={linkClase}>Multas y fotocívicas</Link>.
                </p>
                <Fuente source={source} />
            </div>
        );
    }

    return (
        <div>
            <ul className="tw-list-none tw-p-0 tw-m-0 tw-space-y-3">
                {results.map((agente) => {
                    const autorizacion = AUTORIZACION[agente.authorization_type];
                    return (
                        <li key={`${agente.plate}-${agente.authorization_type}`} className="tw-border tw-border-rule tw-rounded tw-p-4">
                            <div className="tw-flex tw-items-center tw-justify-between tw-mb-2">
                                <span className="tw-font-mono tw-text-lg tw-font-bold tw-text-ink tw-tracking-wider">{agente.plate}</span>
                                <Badge variant={autorizacion.variante}>{autorizacion.etiqueta}</Badge>
                            </div>
                            <p className="tw-text-ink-soft tw-text-sm tw-m-0">
                                <strong className="tw-text-ink">{agente.full_name}</strong> {autorizacion.texto}
                            </p>
                            {agente.corporation && (
                                <p className="tw-text-ink-soft tw-text-sm tw-mt-1 tw-mb-0">Corporación: {agente.corporation}</p>
                            )}
                            {agente.alcaldias && agente.alcaldias.length > 0 && (
                                <p className="tw-text-ink-soft tw-text-sm tw-mt-1 tw-mb-0">Alcaldías: {agente.alcaldias.join(', ')}</p>
                            )}
                        </li>
                    );
                })}
            </ul>
            <Fuente source={source} />
        </div>
    );
};

export default ResultadoBusquedaAgentes;
```

- [ ] **Step 5: Correr las pruebas del componente**

Run: `cd frontend && CI=true npx react-scripts test --watchAll=false src/components/agentes`
Expected: PASS.

- [ ] **Step 6: Prueba de la página (falla)**

`frontend/src/pages/__tests__/ConsultarAgenteTransito.test.js`:

```javascript
import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ConsultarAgenteTransito from '../ConsultarAgenteTransito';
import { buscarAgentes } from '../../services/agentesService';

jest.mock('react-router-dom', () => ({
    Link: ({ to, children, ...rest }) => <a href={to} {...rest}>{children}</a>,
    useSearchParams: () => [new URLSearchParams('')],
}));
jest.mock('../../components/NavBar2', () => () => null);
jest.mock('../../components/Footer', () => () => null);
jest.mock('../../services/agentesService', () => ({ buscarAgentes: jest.fn() }));

beforeEach(() => jest.clearAllMocks());

test('searches by name and renders results', async () => {
    buscarAgentes.mockResolvedValue({ query: 'karla zavala', matched_by: 'name', source: { title: 'Acuerdo 30/2026', url: 'https://g.example/a.pdf', last_reform_date: '2026-06-10' }, results: [
        { plate: '1168287', full_name: 'ZAVALA TOVAR KARLA PAOLA', authorization_type: 'via_publica', corporation: null, alcaldias: null },
    ] });
    render(<ConsultarAgenteTransito />);
    fireEvent.change(screen.getByLabelText('Placa o nombre del agente'), { target: { value: 'karla zavala' } });
    fireEvent.click(screen.getByRole('button', { name: 'Buscar' }));
    await waitFor(() => expect(screen.getByText('ZAVALA TOVAR KARLA PAOLA')).toBeInTheDocument());
    expect(buscarAgentes).toHaveBeenCalledWith('karla zavala');
});

test('asks for at least two characters without calling the API', () => {
    render(<ConsultarAgenteTransito />);
    fireEvent.change(screen.getByLabelText('Placa o nombre del agente'), { target: { value: 'a' } });
    fireEvent.click(screen.getByRole('button', { name: 'Buscar' }));
    expect(screen.getByText(/escribe una placa o al menos dos letras/i)).toBeInTheDocument();
    expect(buscarAgentes).not.toHaveBeenCalled();
});

test('shows the service error message', async () => {
    buscarAgentes.mockRejectedValue(new Error('No pudimos consultar el registro de agentes. Intenta de nuevo.'));
    render(<ConsultarAgenteTransito />);
    fireEvent.change(screen.getByLabelText('Placa o nombre del agente'), { target: { value: '1168287' } });
    fireEvent.click(screen.getByRole('button', { name: 'Buscar' }));
    await waitFor(() => expect(screen.getByText(/no pudimos consultar el registro/i)).toBeInTheDocument());
});
```

Run: `cd frontend && CI=true npx react-scripts test --watchAll=false src/pages/__tests__/ConsultarAgenteTransito.test.js`
Expected: FAIL (la etiqueta y el servicio todavía no existen).

- [ ] **Step 7: Página `ConsultarAgenteTransito`**

En `frontend/src/pages/ConsultarAgenteTransito.js`:
- Import: `import { buscarAgentes } from "../services/agentesService";` y `import ResultadoBusquedaAgentes from "../components/agentes/ResultadoBusquedaAgentes";`. Quita el import de `Badge`.
- Renombra el estado: `placaBusqueda` → `consulta` (inicializado con `searchParams.get('placa') || searchParams.get('q') || ''`) y `agenteEncontrado` → `resultado`.
- Handler:

```javascript
    const handleBuscarAgente = async () => {
        if (consulta.trim().length < 2) {
            setResultado(null);
            setErrorBusqueda('Escribe una placa o al menos dos letras del nombre del agente.');
            return;
        }
        setCargando(true);
        setErrorBusqueda(null);
        setResultado(null);
        try {
            setResultado(await buscarAgentes(consulta));
        } catch (error) {
            setErrorBusqueda(error.message);
        } finally {
            setCargando(false);
        }
    };
```

- Párrafo introductorio: "Ingresa el número de placa o el nombre del agente para confirmar si aparece en la lista oficial de personal autorizado para infraccionar en la CDMX."
- Input: quita `inputMode="numeric"`; `placeholder="Placa o nombre"`; `aria-label="Placa o nombre del agente"`; `value={consulta}`; `onChange={(e) => setConsulta(e.target.value)}`.
- Reemplaza el bloque `{!cargando && agenteEncontrado && (...)}` por `{!cargando && resultado && <ResultadoBusquedaAgentes resultado={resultado} />}`.
- Condición del texto vacío: `!cargando && !errorBusqueda && !resultado`, con el texto "Ingresa una placa o un nombre para verificar al agente."

- [ ] **Step 8: Widget de `Home`**

En `frontend/src/pages/Home.js`:
- Reemplaza `import { consultarAgente } ...` por `import { buscarAgentes } from '../services/agentesService';` y agrega `import ResultadoBusquedaAgentes from '../components/agentes/ResultadoBusquedaAgentes';`. Quita `Badge` si ya no se usa.
- Cambia `agenteEncontrado`/`setAgenteEncontrado` por `resultado`/`setResultado`. La validación es `placa.trim().length < 2`, con el mensaje "Escribe una placa o al menos dos letras del nombre del agente."; la llamada es `setResultado(await buscarAgentes(placa))`.
- Encabezado del widget: "Verificar agente por placa o nombre". Input: quita `inputMode="numeric"`, `placeholder="Placa o nombre"`, `aria-label="Placa o nombre del agente"`.
- En el bloque de error, borra el link "Verificar manualmente en el listado oficial →" (la fuente ahora va en el resultado).
- Reemplaza el bloque `{!cargando && agenteEncontrado && (...)}` por `{!cargando && resultado && <div className="tw-mt-3 tw-animate-fade-in-up"><ResultadoBusquedaAgentes resultado={resultado} /></div>}`.
- `AGENTES_OFICIAL_URL` se queda por ahora (lo usa la lista de documentos); se actualiza en la Task 6.

- [ ] **Step 9: Correr todas las pruebas del frontend**

Run: `cd frontend && CI=true npx react-scripts test --watchAll=false`
Expected: PASS.

- [ ] **Step 10: Commit**

```bash
git add frontend/src
git commit -m "feat: verify agents by plate or name and always show the official source

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Manifiesto de fuentes y descarga con TLS estricto

**Files:**
- Create: `data/sources.json`
- Create: `backend/app/services/sources.py`
- Create: `backend/scripts/fetch_sources.py`
- Create: `backend/scripts/certs/lets-encrypt-yr2.pem`
- Create: `backend/tests/test_sources.py`
- Modify: `.gitignore`
- Delete: `data/legal-sources/*.pdf` (nombres viejos), `data/legal-sources/uncategorized/`, `data/legal-embeddings/`

**Interfaces:**
- Consumes: `OfficialSource` (Task 1).
- Produces:
  - `SourceSpec(slug, title, kind, url, last_reform_date: date | None, manual: bool = False, expected_counts: dict[str, int] | None = None, pages: tuple[int, int] | None = None)`
  - `load_manifest(path: Path) -> list[SourceSpec]` (lanza `ValueError` si el manifiesto es inválido)
  - `sha256_of(path: Path) -> str`
  - `local_path(spec: SourceSpec, directory: Path) -> Path` (devuelve `directory / f"{spec.slug}.pdf"`)
  - `register_source(db: Session, spec: SourceSpec, sha256: str) -> tuple[OfficialSource, bool]` (el `bool` indica si cambió la versión vigente; no hace commit)
  - Constantes del script: `REPO_ROOT`, `MANIFEST`, `SOURCES_DIR`

- [ ] **Step 1: Pruebas (fallan)**

`backend/tests/test_sources.py`:

```python
import json
from datetime import date

import pytest
from sqlalchemy import select

from app.models.domain import OfficialSource
from app.services.sources import SourceSpec, load_manifest, register_source, sha256_of

SPEC = SourceSpec(
    slug="ley-movilidad", title="Ley de Movilidad", kind="ley",
    url="https://data.consejeria.cdmx.gob.mx/images/leyes/leyes/LEY_DE_MOVILIDAD_DE_LA_CDMX_3.2.pdf",
    last_reform_date=date(2021, 12, 27),
)


def write_manifest(tmp_path, sources):
    path = tmp_path / "sources.json"
    path.write_text(json.dumps({"sources": sources}), encoding="utf-8")
    return path


def entry(**overrides):
    base = {"slug": "ley-movilidad", "title": "Ley de Movilidad", "kind": "ley",
            "url": "https://example.gob.mx/ley.pdf", "last_reform_date": "2021-12-27"}
    return {**base, **overrides}


def test_load_manifest_parses_optional_fields(tmp_path):
    path = write_manifest(tmp_path, [entry(slug="acuerdo-agentes-transito", kind="acuerdo", manual=True,
                                           expected_counts={"via_publica": 717, "sistemas_tecnologicos": 570},
                                           pages=[10, 40], last_reform_date=None)])
    [spec] = load_manifest(path)
    assert spec.manual is True
    assert spec.expected_counts == {"via_publica": 717, "sistemas_tecnologicos": 570}
    assert spec.pages == (10, 40)
    assert spec.last_reform_date is None


@pytest.mark.parametrize("bad", [
    entry(slug="Ley Movilidad"),
    entry(kind="blog"),
    entry(url="http://example.gob.mx/ley.pdf"),
    entry(last_reform_date="27/12/2021"),
    entry(pages=[40, 10]),
])
def test_load_manifest_rejects_invalid_entries(tmp_path, bad):
    with pytest.raises(ValueError):
        load_manifest(write_manifest(tmp_path, [bad]))


def test_load_manifest_rejects_duplicate_slugs(tmp_path):
    with pytest.raises(ValueError):
        load_manifest(write_manifest(tmp_path, [entry(), entry()]))


def test_sha256_of(tmp_path):
    f = tmp_path / "a.pdf"
    f.write_bytes(b"%PDF-1.4 hola")
    assert sha256_of(f) == "bc39ce0612bcde4063a33a16c57c873efbc5c908b15a747c801cb4bc0813688f"


def test_register_same_file_twice_keeps_one_version_and_refreshes_metadata(client):
    _, factory = client
    with factory() as db:
        first, changed = register_source(db, SPEC, "a" * 64)
        db.commit()
        assert changed is True
        renamed = SourceSpec(**{**SPEC.__dict__, "title": "Ley de Movilidad de la CDMX"})
        again, changed = register_source(db, renamed, "a" * 64)
        db.commit()
        assert changed is False
        assert again.id == first.id
        assert again.title == "Ley de Movilidad de la CDMX"
        assert len(db.scalars(select(OfficialSource)).all()) == 1


def test_new_file_creates_new_current_version(client):
    _, factory = client
    with factory() as db:
        old, _ = register_source(db, SPEC, "a" * 64)
        db.commit()
        new, changed = register_source(db, SPEC, "b" * 64)
        db.commit()
        assert changed is True
        db.refresh(old)
        assert old.is_current is False
        assert new.is_current is True


def test_reverting_to_previous_file_reactivates_that_version(client):
    _, factory = client
    with factory() as db:
        old, _ = register_source(db, SPEC, "a" * 64)
        db.commit()
        register_source(db, SPEC, "b" * 64)
        db.commit()
        back, changed = register_source(db, SPEC, "a" * 64)
        db.commit()
        assert changed is True
        assert back.id == old.id
        currents = db.scalars(select(OfficialSource).where(OfficialSource.is_current)).all()
        assert [s.sha256 for s in currents] == ["a" * 64]
```

Run: `cd backend && uv run pytest tests/test_sources.py -v`
Expected: FAIL con `ModuleNotFoundError: app.services.sources`.

- [ ] **Step 2: Servicio**

`backend/app/services/sources.py`:

```python
"""Official-source manifest and version registry. No network access lives here."""
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import OfficialSource

KINDS = {"ley", "reglamento", "codigo", "acuerdo", "decreto", "guia"}
SLUG_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


@dataclass(frozen=True)
class SourceSpec:
    slug: str
    title: str
    kind: str
    url: str
    last_reform_date: date | None
    manual: bool = False
    expected_counts: dict[str, int] | None = None
    pages: tuple[int, int] | None = None


def _parse_entry(raw: dict) -> SourceSpec:
    slug = raw["slug"]
    if not SLUG_PATTERN.fullmatch(slug):
        raise ValueError(f"Slug inválido: {slug!r}")
    if raw["kind"] not in KINDS:
        raise ValueError(f"Tipo inválido en {slug}: {raw['kind']!r}")
    if not raw["url"].startswith("https://"):
        raise ValueError(f"La URL de {slug} debe ser https")
    reform = raw.get("last_reform_date")
    pages = raw.get("pages")
    if pages is not None and not (len(pages) == 2 and 1 <= pages[0] <= pages[1]):
        raise ValueError(f"Rango de páginas inválido en {slug}: {pages!r}")
    return SourceSpec(
        slug=slug,
        title=raw["title"],
        kind=raw["kind"],
        url=raw["url"],
        last_reform_date=date.fromisoformat(reform) if reform else None,
        manual=bool(raw.get("manual", False)),
        expected_counts=raw.get("expected_counts"),
        pages=tuple(pages) if pages else None,
    )


def load_manifest(path: Path) -> list[SourceSpec]:
    specs = [_parse_entry(raw) for raw in json.loads(path.read_text(encoding="utf-8"))["sources"]]
    slugs = [spec.slug for spec in specs]
    if len(slugs) != len(set(slugs)):
        raise ValueError("Slugs duplicados en el manifiesto")
    return specs


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def local_path(spec: SourceSpec, directory: Path) -> Path:
    return directory / f"{spec.slug}.pdf"


def _apply_metadata(source: OfficialSource, spec: SourceSpec) -> None:
    source.title = spec.title
    source.kind = spec.kind
    source.url = spec.url
    source.last_reform_date = spec.last_reform_date


def register_source(db: Session, spec: SourceSpec, sha256: str) -> tuple[OfficialSource, bool]:
    """Make the file with `sha256` the current version of `spec.slug`. Caller commits."""
    current = db.scalar(
        select(OfficialSource).where(OfficialSource.slug == spec.slug, OfficialSource.is_current)
    )
    if current is not None and current.sha256 == sha256:
        _apply_metadata(current, spec)
        return current, False
    if current is not None:
        current.is_current = False
        db.flush()
    source = db.scalar(
        select(OfficialSource).where(OfficialSource.slug == spec.slug, OfficialSource.sha256 == sha256)
    )
    if source is None:
        source = OfficialSource(slug=spec.slug, sha256=sha256, is_current=True)
        db.add(source)
    source.is_current = True
    _apply_metadata(source, spec)
    db.flush()
    return source, True
```

Run: `cd backend && uv run pytest tests/test_sources.py -v`
Expected: PASS.

- [ ] **Step 3: Certificado intermedio**

El servidor de la Consejería envía una cadena equivocada: su hoja la emite Let's Encrypt YR2, pero manda la cadena de DigiCert. Los navegadores lo resuelven por AIA y Python no. Se agrega el intermedio público como ancla adicional; la verificación sigue siendo estricta.

```bash
cd backend && mkdir -p scripts/certs
curl -s http://yr2.i.lencr.org/ -o /tmp/yr2.der
openssl x509 -inform der -in /tmp/yr2.der -out scripts/certs/lets-encrypt-yr2.pem
openssl x509 -in scripts/certs/lets-encrypt-yr2.pem -noout -subject -issuer -enddate
```

Expected: `subject=C=US, O=Let's Encrypt, CN=YR2`, `issuer=C=US, O=ISRG, CN=Root YR`, vigencia hasta 2028.

- [ ] **Step 4: Script de descarga**

`backend/scripts/fetch_sources.py`:

```python
"""Download official sources listed in data/sources.json and register their current versions.

TLS is always verified. The Consejería server omits its Let's Encrypt intermediate, so that public
intermediate ships in scripts/certs and is added to the default trust store.
"""
import argparse
import ssl
import sys
import urllib.request
from pathlib import Path

from app.db.session import SessionLocal
from app.services.sources import SourceSpec, load_manifest, local_path, register_source, sha256_of

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = REPO_ROOT / "data" / "sources.json"
SOURCES_DIR = REPO_ROOT / "data" / "legal-sources"
EXTRA_CA = Path(__file__).resolve().parent / "certs" / "lets-encrypt-yr2.pem"


def ssl_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    context.load_verify_locations(cafile=str(EXTRA_CA))
    return context


def download(spec: SourceSpec, dest: Path, context: ssl.SSLContext) -> None:
    request = urllib.request.Request(spec.url, headers={"User-Agent": "Avizum source sync"})
    with urllib.request.urlopen(request, context=context, timeout=300) as response:
        data = response.read()
    if not data.startswith(b"%PDF"):
        raise ValueError(f"{spec.slug}: la respuesta no es un PDF")
    tmp = dest.with_suffix(".part")
    tmp.write_bytes(data)
    tmp.replace(dest)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="slug a procesar")
    parser.add_argument("--refresh", action="store_true", help="vuelve a descargar aunque exista el archivo")
    args = parser.parse_args()

    specs = [s for s in load_manifest(MANIFEST) if args.only in (None, s.slug)]
    if not specs:
        raise SystemExit(f"No hay fuentes con slug {args.only!r}")
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    context = ssl_context()
    missing: list[tuple[SourceSpec, Path]] = []
    with SessionLocal() as db:
        for spec in specs:
            path = local_path(spec, SOURCES_DIR)
            if not spec.manual and (args.refresh or not path.exists()):
                print(f"↓ {spec.slug}")
                download(spec, path, context)
            if not path.exists():
                missing.append((spec, path))
                continue
            source, changed = register_source(db, spec, sha256_of(path))
            print(f"{'✓ nueva versión' if changed else '= sin cambios'} {spec.slug} ({source.sha256[:12]})")
        db.commit()
    for spec, path in missing:
        print(f"✗ Falta {spec.slug}: descárgalo desde {spec.url} y guárdalo como {path}", file=sys.stderr)
    if missing:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Manifiesto**

`data/sources.json` (URLs verificadas el 2026-10-08 en el portal de la Consejería Jurídica; `last_reform_date` es la que declara cada PDF):

```json
{
  "sources": [
    {"slug": "reglamento-transito", "title": "Reglamento de Tránsito de la Ciudad de México", "kind": "reglamento",
     "url": "https://data.consejeria.cdmx.gob.mx/images/leyes/reglamentos/REGLAMENTO_DE_TRANSITO_DE_LA_CIUDAD_DE_MEXICO_6.1.pdf",
     "last_reform_date": "2024-11-26"},
    {"slug": "ley-movilidad", "title": "Ley de Movilidad de la Ciudad de México", "kind": "ley",
     "url": "https://data.consejeria.cdmx.gob.mx/images/leyes/leyes/LEY_DE_MOVILIDAD_DE_LA_CDMX_3.2.pdf",
     "last_reform_date": "2021-12-27"},
    {"slug": "ley-cultura-civica", "title": "Ley de Cultura Cívica de la Ciudad de México", "kind": "ley",
     "url": "https://data.consejeria.cdmx.gob.mx/images/leyes/leyes/LEY_DE_CULTURA_CIVICA_DE_LA_CIUDAD_DE_MEXICO_2.7.pdf",
     "last_reform_date": "2024-10-03"},
    {"slug": "ley-procedimiento-administrativo", "title": "Ley de Procedimiento Administrativo de la Ciudad de México", "kind": "ley",
     "url": "https://data.consejeria.cdmx.gob.mx/images/leyes/leyes/LEY_DE_PROCEDIMIENTO_ADMINISTRATIVO_DE_LA_CDMX_1.1.pdf",
     "last_reform_date": "2019-06-12"},
    {"slug": "ley-justicia-administrativa", "title": "Ley de Justicia Administrativa de la Ciudad de México", "kind": "ley",
     "url": "https://data.consejeria.cdmx.gob.mx/images/leyes/leyes/LEY_%20DE_JUSTICIA_ADMINISTRATIVA_DE_LA_CDMX_3.1.pdf",
     "last_reform_date": "2019-12-23"},
    {"slug": "codigo-fiscal", "title": "Código Fiscal de la Ciudad de México", "kind": "codigo",
     "url": "https://data.consejeria.cdmx.gob.mx/images/leyes/2025/2026/210126/CODIGO_FISCAL_DE_LA_CDMX_26.1.pdf",
     "last_reform_date": "2025-12-19"}
  ]
}
```

- [ ] **Step 6: Limpieza y `.gitignore`**

Los PDFs descargables no se versionan (el Código Fiscal pesa 157 MB); se reproducen con `fetch_sources`. Solo se versionan los de descarga manual, que se agregan en la Task 6.

```bash
cd /home/alexis/Projects/abogadazo
git rm -r -q data/legal-sources/cultura_civica.pdf data/legal-sources/ley_movilidad.pdf \
  data/legal-sources/procedimiento_administrativo.pdf data/legal-sources/reglamento_transito.pdf \
  data/legal-sources/uncategorized data/legal-embeddings
printf '\n# Official PDFs are reproducible with scripts.fetch_sources; manual ones are whitelisted\ndata/legal-sources/*.pdf\ndata/legal-sources/*.part\n' >> .gitignore
```

- [ ] **Step 7: Ejecutar la descarga real**

```bash
cd backend && uv run python -m scripts.fetch_sources
uv run python -m scripts.fetch_sources   # segunda corrida
```

Expected: la primera corrida muestra seis `✓ nueva versión`; la segunda, seis `= sin cambios`. Si alguna URL devuelve 404, avísale al cliente con la URL exacta; no la sustituyas por otra fuente sin su visto bueno.

- [ ] **Step 8: Pruebas y commit**

```bash
cd backend && uv run pytest -q
cd .. && git add .gitignore data/sources.json backend/app/services/sources.py backend/scripts backend/tests/test_sources.py
git commit -m "feat: register official legal sources from a manifest with strict TLS downloads

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Parser del acuerdo de agentes (puro, validado por conteos)

**Files:**
- Create: `backend/app/services/acuerdo_parser.py`
- Create: `backend/tests/test_acuerdo_parser.py`
- Modify: `backend/pyproject.toml` (grupo `ingest`)

**Interfaces:**
- Consumes: `AuthorizationType` (Task 1).
- Produces:
  - `AcuerdoParseError(ValueError)`
  - `AgentRow(number: int, plate: str, full_name: str)`
  - `ParsedSection(authorization_type: AuthorizationType, heading: str, rows: list[AgentRow])`
  - `parse_acuerdo(text: str) -> list[ParsedSection]`
  - `validate_counts(sections: list[ParsedSection], expected: dict[str, int]) -> None`

- [ ] **Step 1: Documentación de PyMuPDF (tecnología nueva, regla de `CLAUDE.md`)**

Consulta con Context7 la API vigente de PyMuPDF para abrir un documento y extraer texto por página (`pymupdf.open`, `page.get_text()`). Revisa si existe un plugin de Claude Code para PyMuPDF; si existe, solo menciónalo al cliente, sin instalar nada. Luego agrega a `backend/pyproject.toml`, en `[dependency-groups]`:

```toml
ingest = ["pymupdf>=1.24"]
```

y corre `cd backend && uv sync --group dev --group ingest`.

- [ ] **Step 2: Pruebas (fallan)**

`backend/tests/test_acuerdo_parser.py`, con un texto que reproduce la extracción real del Acuerdo 40/2024: tripletas `número / placa / nombre` en líneas separadas, encabezados de página intercalados, un número de página que coincide con el número de fila esperado y un nombre partido en dos líneas.

```python
import pytest

from app.models.domain import AuthorizationType
from app.services.acuerdo_parser import AcuerdoParseError, parse_acuerdo, validate_counts

SAMPLE = """
ACUERDO 30/2026 POR EL QUE SE DA A CONOCER EL NOMBRE COMPLETO Y NÚMERO DE PLACA DEL PERSONAL
POLICIAL ... EQUIPOS ELECTRÓNICOS PORTÁTILES, ASÍ COMO AQUELLAS EMITIDAS MEDIANTE SISTEMAS TECNOLÓGICOS
PRIMERO. Se da a conocer el nombre completo y número de placa del personal policial de la Secretaría de Seguridad
Ciudadana de la Ciudad de México, autorizado para que expida y firme las boletas de tránsito o recibos emitidos por
equipos electrónicos portátiles en vía pública, con motivo de infracciones, el cual se detalla a continuación:
NO.
PLACA
NOMBRE
1
1151407
ABARCA CASTRO YANELI
2
57196
ABUNDIO SANTOS CARMEN JULIA
3
1032742
ACOSTA LOPEZ ALEXIS JUAN
10 de junio de 2026
GACETA OFICIAL DE LA CIUDAD DE MÉXICO
4

4
885312
YAÑEZ GOMEZ VANESSA
5
730249
ZENIL OJEDA
RICARDO
SEGUNDO. Se da a conocer el nombre completo y número de placa del personal policial de la Secretaría de Seguridad
Ciudadana de la Ciudad de México, autorizado para que expida y firme las boletas de tránsito mediante sistemas
tecnológicos, con motivo de infracciones, el cual se detalla a continuación:
NO.
PLACA
NOMBRE
1
42006
AGATON HERNANDEZ URIEL
2
730249
ZENIL OJEDA RICARDO
TRANSITORIOS
PRIMERO. Publíquese en la Gaceta Oficial de la Ciudad de México.
"""


def test_parses_both_lists_ignoring_page_headers():
    via, tech = parse_acuerdo(SAMPLE)
    assert via.authorization_type is AuthorizationType.VIA_PUBLICA
    assert tech.authorization_type is AuthorizationType.SISTEMAS_TECNOLOGICOS
    assert [(r.number, r.plate) for r in via.rows] == [(1, "1151407"), (2, "57196"), (3, "1032742"), (4, "885312"), (5, "730249")]
    assert via.rows[3].full_name == "YAÑEZ GOMEZ VANESSA"
    assert [r.plate for r in tech.rows] == ["42006", "730249"]


def test_joins_names_wrapped_over_two_lines():
    via, _ = parse_acuerdo(SAMPLE)
    assert via.rows[4].full_name == "ZENIL OJEDA RICARDO"


def test_validate_counts_accepts_exact_counts():
    validate_counts(parse_acuerdo(SAMPLE), {"via_publica": 5, "sistemas_tecnologicos": 2})


@pytest.mark.parametrize("expected", [
    {"via_publica": 717, "sistemas_tecnologicos": 570},
    {"via_publica": 5},
])
def test_validate_counts_rejects_mismatches(expected):
    with pytest.raises(AcuerdoParseError, match="Conteos"):
        validate_counts(parse_acuerdo(SAMPLE), expected)


def test_validate_counts_rejects_duplicate_plates_within_a_list():
    text = SAMPLE.replace("57196", "1151407")
    with pytest.raises(AcuerdoParseError, match="duplicada"):
        validate_counts(parse_acuerdo(text), {"via_publica": 5, "sistemas_tecnologicos": 2})


def test_unknown_section_type_fails_loudly():
    text = SAMPLE.replace("mediante sistemas\ntecnológicos", "en recintos deportivos")
    with pytest.raises(AcuerdoParseError, match="no reconocida"):
        parse_acuerdo(text)


def test_missing_transitorios_fails():
    with pytest.raises(AcuerdoParseError, match="TRANSITORIOS"):
        parse_acuerdo(SAMPLE.split("TRANSITORIOS")[0])


def test_text_without_lists_fails():
    with pytest.raises(AcuerdoParseError):
        parse_acuerdo("Texto cualquiera\nTRANSITORIOS\n")
```

Run: `cd backend && uv run pytest tests/test_acuerdo_parser.py -v`
Expected: FAIL con `ModuleNotFoundError`.

- [ ] **Step 3: Parser**

`backend/app/services/acuerdo_parser.py`:

```python
"""Parse the SSC 'nombre completo y número de placa' acuerdo published in the Gaceta Oficial.

Extracted PDF text lists each officer as three lines (row number, plate, name) with page headers
interleaved. Rows are accepted only in strict sequence, so stray page numbers are skipped, and the
caller validates the totals against the counts the acuerdo declares.
"""
import re
from dataclasses import dataclass

from app.models.domain import AuthorizationType

SECTION_PATTERN = re.compile(r"(PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO)\.\s+Se da a conocer", re.IGNORECASE)
END_PATTERN = re.compile(r"\bTRANSITORIOS\b")
PLATE_PATTERN = re.compile(r"\d{3,8}")
NAME_PATTERN = re.compile(r"[A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ.'\- ]*\s[A-ZÁÉÍÓÚÜÑ.'\- ]+")
CONTINUATION_PATTERN = re.compile(r"[A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ.'\- ]*")


class AcuerdoParseError(ValueError):
    pass


@dataclass(frozen=True)
class AgentRow:
    number: int
    plate: str
    full_name: str


@dataclass(frozen=True)
class ParsedSection:
    authorization_type: AuthorizationType
    heading: str
    rows: list[AgentRow]


def _classify(heading: str) -> AuthorizationType:
    text = heading.lower()
    portable = "portátiles" in text or "portatiles" in text
    technological = "sistemas tecnológicos" in text or "sistemas tecnologicos" in text
    if portable == technological:
        raise AcuerdoParseError(f"Sección no reconocida: {heading[:200]}")
    return AuthorizationType.VIA_PUBLICA if portable else AuthorizationType.SISTEMAS_TECNOLOGICOS


def _is_continuation(line: str) -> bool:
    return bool(CONTINUATION_PATTERN.fullmatch(line)) and "GACETA OFICIAL" not in line


def _parse_rows(chunk: str) -> list[AgentRow]:
    lines = [line.strip() for line in chunk.splitlines() if line.strip()]
    rows: list[AgentRow] = []
    expected, i = 1, 0
    while i + 2 < len(lines):
        number, plate, name = lines[i], lines[i + 1], lines[i + 2]
        if number == str(expected) and PLATE_PATTERN.fullmatch(plate) and NAME_PATTERN.fullmatch(name):
            parts = [name]
            i += 3
            while i < len(lines) and lines[i] != str(expected + 1) and _is_continuation(lines[i]):
                parts.append(lines[i])
                i += 1
            rows.append(AgentRow(expected, plate, " ".join(" ".join(parts).split())))
            expected += 1
        else:
            i += 1
    return rows


def parse_acuerdo(text: str) -> list[ParsedSection]:
    end = END_PATTERN.search(text)
    if end is None:
        raise AcuerdoParseError("No se encontró la sección TRANSITORIOS")
    body = text[: end.start()]
    starts = list(SECTION_PATTERN.finditer(body))
    if not starts:
        raise AcuerdoParseError("No se encontraron listas ('PRIMERO. Se da a conocer…')")
    sections = []
    for index, match in enumerate(starts):
        stop = starts[index + 1].start() if index + 1 < len(starts) else len(body)
        chunk = body[match.start():stop]
        heading = " ".join(chunk[:700].split())
        rows = _parse_rows(chunk)
        if not rows:
            raise AcuerdoParseError(f"Sección sin registros: {heading[:120]}")
        sections.append(ParsedSection(_classify(heading), heading[:300], rows))
    return sections


def validate_counts(sections: list[ParsedSection], expected: dict[str, int]) -> None:
    got: dict[str, int] = {}
    for section in sections:
        key = section.authorization_type.value
        if key in got:
            raise AcuerdoParseError(f"Tipo de autorización repetido: {key}")
        got[key] = len(section.rows)
        plates = [row.plate for row in section.rows]
        duplicated = {plate for plate in plates if plates.count(plate) > 1}
        if duplicated:
            raise AcuerdoParseError(f"Placa duplicada en {key}: {sorted(duplicated)}")
    if got != expected:
        raise AcuerdoParseError(f"Conteos no coinciden: esperado {expected}, obtenido {got}")
```

Run: `cd backend && uv run pytest tests/test_acuerdo_parser.py -v`
Expected: PASS.

- [ ] **Step 4: Validación contra el PDF real del Acuerdo 40/2024**

Es la prueba de fuego del parser con un documento real de la misma plantilla. No se versiona: es verificación manual.

```bash
cd backend && curl -s -o /tmp/acuerdo-40-2024.pdf https://www.ssc.cdmx.gob.mx/storage/app/media/Transito/Actualizaciones/Acuedo-40-2024.pdf
uv run python - <<'EOF'
import csv, pymupdf
from app.services.acuerdo_parser import parse_acuerdo, validate_counts
text = "\n".join(p.get_text() for p in pymupdf.open("/tmp/acuerdo-40-2024.pdf"))
sections = parse_acuerdo(text)
validate_counts(sections, {"via_publica": 551, "sistemas_tecnologicos": 452})
via = {r.plate: r.full_name for r in sections[0].rows}
legacy = {r["placa"]: r["nombre_completo"] for r in csv.DictReader(open("../data/agents/agentes_procesados.csv"))}
print("ok 551/452; CSV ⊂ PDF:", set(legacy) <= set(via), "; nombres iguales:", sum(via[p] == n for p, n in legacy.items()), "/", len(legacy))
print("faltaba en el CSV:", {p: n for p, n in via.items() if p not in legacy})
EOF
```

Expected: `ok 551/452; CSV ⊂ PDF: True ; nombres iguales: 550 / 550` y el registro que el CSV había perdido. Si falla, corrige el parser y agrega una prueba que reproduzca el caso.

- [ ] **Step 5: Commit**

```bash
cd .. && git add backend/pyproject.toml backend/uv.lock backend/app/services/acuerdo_parser.py backend/tests/test_acuerdo_parser.py
git commit -m "feat: parse SSC authorized-agents acuerdo with sequence and count validation

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Importar el Acuerdo 30/2026 y retirar el registro viejo

**Files:**
- Create: `backend/app/services/agents_import.py`
- Create: `backend/scripts/import_agents.py`
- Create: `backend/tests/test_agents_import.py`
- Modify: `data/sources.json` (entradas manuales)
- Modify: `.gitignore` (lista blanca de PDFs manuales)
- Add: `data/legal-sources/acuerdo-agentes-transito.pdf`, `data/legal-sources/reforma-reglamento-transito-2026-06-30.pdf`
- Delete: `backend/scripts/seed_agents.py`, `data/agents/agentes_procesados.csv`
- Modify: `frontend/src/pages/Home.js`, `frontend/src/content/guia/articulos/marco-juridico.json` (link al 30/2026)
- Modify: `README.md`, `CLAUDE.md` (comandos)

**Interfaces:**
- Consumes: `parse_acuerdo`, `validate_counts`, `ParsedSection` (Task 5); `load_manifest`, `local_path`, `sha256_of`, `SourceSpec` (Task 4); `AGENTS_SOURCE_SLUG`, `normalize_name`, `normalize_plate`, `current_agents_source` (Tasks 1 y 2); `MANIFEST` y `SOURCES_DIR` (de `scripts.fetch_sources`).
- Produces: `replace_agents(db: Session, source: OfficialSource, sections: list[ParsedSection]) -> dict[str, int]` (no hace commit).

- [ ] **Step 1: Pruebas (fallan)**

`backend/tests/test_agents_import.py`:

```python
from sqlalchemy import select

from app.models.domain import AgentLookup, AuthorizationType, AuthorizedAgent
from app.services.acuerdo_parser import AgentRow, ParsedSection
from app.services.agents_import import replace_agents
from tests.factories import add_agent, add_agents_source

SECTIONS = [
    ParsedSection(AuthorizationType.VIA_PUBLICA, "PRIMERO", [
        AgentRow(1, "1168287", "ZAVALA TOVAR KARLA PAOLA"), AgentRow(2, "885312", "YAÑEZ GOMEZ VANESSA")]),
    ParsedSection(AuthorizationType.SISTEMAS_TECNOLOGICOS, "SEGUNDO", [AgentRow(1, "42006", "AGATON HERNANDEZ URIEL")]),
]


def test_replace_agents_swaps_the_whole_registry_and_keeps_lookup_history(client):
    _, factory = client
    with factory() as db:
        old_source = add_agents_source(db, sha256="a" * 64, is_current=False)
        old = add_agent(db, old_source, "999", "PEREZ LOPEZ ANA")
        db.add(AgentLookup(agent_id=old.id))
        new_source = add_agents_source(db, sha256="b" * 64)
        db.commit()

        counts = replace_agents(db, new_source, SECTIONS)
        db.commit()

        assert counts == {"via_publica": 2, "sistemas_tecnologicos": 1}
        agents = db.scalars(select(AuthorizedAgent).order_by(AuthorizedAgent.plate)).all()
        assert [(a.plate, a.authorization_type, a.source_id) for a in agents] == [
            ("1168287", AuthorizationType.VIA_PUBLICA, new_source.id),
            ("42006", AuthorizationType.SISTEMAS_TECNOLOGICOS, new_source.id),
            ("885312", AuthorizationType.VIA_PUBLICA, new_source.id),
        ]
        assert db.scalar(select(AuthorizedAgent.name_search).where(AuthorizedAgent.plate == "885312")) == "yanez gomez vanessa"
        lookup = db.scalar(select(AgentLookup))
        assert lookup is not None and lookup.agent_id is None


def test_replace_agents_is_idempotent(client):
    _, factory = client
    with factory() as db:
        source = add_agents_source(db)
        db.commit()
        replace_agents(db, source, SECTIONS)
        db.commit()
        replace_agents(db, source, SECTIONS)
        db.commit()
        assert len(db.scalars(select(AuthorizedAgent)).all()) == 3
```

Run: `cd backend && uv run pytest tests/test_agents_import.py -v`
Expected: FAIL con `ModuleNotFoundError`.

- [ ] **Step 2: Servicio**

`backend/app/services/agents_import.py`:

```python
"""Replace the authorized-agents registry with the lists parsed from an official acuerdo."""
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.domain import AuthorizedAgent, OfficialSource
from app.services.acuerdo_parser import ParsedSection
from app.services.agents_registry import normalize_name, normalize_plate


def replace_agents(db: Session, source: OfficialSource, sections: list[ParsedSection]) -> dict[str, int]:
    """Delete every agent and insert the parsed lists in the caller's transaction (no commit)."""
    db.execute(delete(AuthorizedAgent))
    db.add_all(
        AuthorizedAgent(
            plate=normalize_plate(row.plate),
            full_name=row.full_name,
            name_search=normalize_name(row.full_name),
            authorization_type=section.authorization_type,
            source_id=source.id,
        )
        for section in sections
        for row in section.rows
    )
    db.flush()
    return {section.authorization_type.value: len(section.rows) for section in sections}
```

Run: `cd backend && uv run pytest tests/test_agents_import.py -v`
Expected: PASS. El `ON DELETE SET NULL` de `agent_lookups.agent_id` conserva el historial.

- [ ] **Step 3: Script de importación**

`backend/scripts/import_agents.py`:

```python
"""Import the authorized-agents acuerdo registered under AGENTS_SOURCE_SLUG; safe to re-run."""
import pymupdf

from app.db.session import SessionLocal
from app.services.acuerdo_parser import parse_acuerdo, validate_counts
from app.services.agents_import import replace_agents
from app.services.agents_registry import AGENTS_SOURCE_SLUG, current_agents_source
from app.services.sources import load_manifest, local_path, sha256_of
from scripts.fetch_sources import MANIFEST, SOURCES_DIR


def main() -> None:
    spec = next((s for s in load_manifest(MANIFEST) if s.slug == AGENTS_SOURCE_SLUG), None)
    if spec is None or not spec.expected_counts:
        raise SystemExit(f"Falta la entrada {AGENTS_SOURCE_SLUG} con expected_counts en {MANIFEST}")
    path = local_path(spec, SOURCES_DIR)
    with SessionLocal() as db:
        source = current_agents_source(db)
        if source is None or source.sha256 != sha256_of(path):
            raise SystemExit("El PDF no está registrado o cambió; corre primero scripts.fetch_sources")
        document = pymupdf.open(path)
        first, last = spec.pages or (1, document.page_count)
        text = "\n".join(document[i].get_text() for i in range(first - 1, last))
        sections = parse_acuerdo(text)
        validate_counts(sections, spec.expected_counts)
        counts = replace_agents(db, source, sections)
        db.commit()
    print(f"Importados {counts} desde {source.title}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: ⚠️ PASO MANUAL DEL CLIENTE — descargar los documentos de la Gaceta**

El portal de la Gaceta no permite descarga automática confiable. Pídele al cliente:

1. Abrir en su navegador `https://data.consejeria.cdmx.gob.mx/index.php/gaceta`, buscar la **Gaceta Oficial del 10 de junio de 2026** y descargar el PDF que contiene el **Acuerdo 30/2026**. Guardarlo como `data/legal-sources/acuerdo-agentes-transito.pdf` y pasar la URL exacta de la descarga.
2. Descargar la **Gaceta Oficial del 30 de junio de 2026, No. 1891 Bis** (reforma al Reglamento de Tránsito sobre vehículos eléctricos). Guardarla como `data/legal-sources/reforma-reglamento-transito-2026-06-30.pdf` y pasar la URL.

Con los PDFs en mano, ábrelos y anota el **rango de páginas** del Acuerdo 30/2026 dentro de su Gaceta, porque la Gaceta trae otros documentos. Después agrega al arreglo `sources` de `data/sources.json`:

```json
    {"slug": "acuerdo-agentes-transito",
     "title": "Acuerdo 30/2026 por el que se da a conocer el personal policial autorizado para expedir y firmar boletas de tránsito (GOCDMX 10-jun-2026)",
     "kind": "acuerdo", "url": "<URL exacta que dio el cliente>", "last_reform_date": "2026-06-10",
     "manual": true, "expected_counts": {"via_publica": 717, "sistemas_tecnologicos": 570},
     "pages": [<primera>, <última>]},
    {"slug": "reforma-reglamento-transito-2026-06-30",
     "title": "Decreto de reforma al Reglamento de Tránsito de la Ciudad de México (GOCDMX 30-jun-2026, No. 1891 Bis)",
     "kind": "decreto", "url": "<URL exacta que dio el cliente>", "last_reform_date": "2026-06-30",
     "manual": true}
```

Si el texto del acuerdo tiene una **tercera lista** (por ejemplo Policía Auxiliar o PBI), el parser fallará con "Sección no reconocida". Eso es lo esperado: detente y muéstrale al cliente el encabezado de esa sección antes de decidir cómo modelarla (corporación y alcaldías, spec §3.2).

En `.gitignore`, debajo de `data/legal-sources/*.pdf`, agrega:

```
!data/legal-sources/acuerdo-agentes-transito.pdf
!data/legal-sources/reforma-reglamento-transito-2026-06-30.pdf
```

- [ ] **Step 5: Registrar e importar**

```bash
cd backend && uv run python -m scripts.fetch_sources
uv run python -m scripts.import_agents
uv run python -m scripts.import_agents   # segunda corrida: mismo resultado, sin duplicados
docker compose exec db psql -U avizum -d avizum -c "select authorization_type, count(*) from authorized_agents group by 1"
```

Expected: `Importados {'via_publica': 717, 'sistemas_tecnologicos': 570}` en ambas corridas y la consulta SQL con 717 y 570. Si los conteos no cuadran, **no** cambies `expected_counts` para forzarlos: revisa el rango de páginas y el parser, y muéstrale al cliente la diferencia.

- [ ] **Step 6: Retirar lo viejo y apuntar los links al 30/2026**

```bash
cd /home/alexis/Projects/abogadazo && git rm -q backend/scripts/seed_agents.py data/agents/agentes_procesados.csv
```

- En `frontend/src/pages/Home.js`, cambia el valor de `AGENTES_OFICIAL_URL` por la `url` de `acuerdo-agentes-transito` en `data/sources.json`, y la etiqueta de esa entrada de la lista por `'Acuerdo 30/2026: personal autorizado para infraccionar en la CDMX'`.
- En `frontend/src/content/guia/articulos/marco-juridico.json`, en la entrada `"tipo": "ACUERDO"`, pon `"titulo": "Acuerdo 30/2026: personal autorizado para expedir y firmar boletas de tránsito en la CDMX"` y como `url` la misma URL.
- En `README.md`, reemplaza `uv run python -m scripts.seed_agents` por:

```bash
   uv sync --group dev --group ingest
   uv run python -m scripts.fetch_sources    # descarga y registra las fuentes oficiales (data/sources.json)
   uv run python -m scripts.import_agents    # importa el Acuerdo de agentes facultados vigente
```

- En `CLAUDE.md`, en el bloque de comandos del backend, después de la línea de `promote_admin`, agrega las mismas dos líneas de `fetch_sources` e `import_agents` con sus comentarios.

- [ ] **Step 7: Verificación completa**

```bash
cd backend && uv run pytest -q
cd ../frontend && CI=true npx react-scripts test --watchAll=false
cd ../backend && (uv run uvicorn app.main:app --port 8000 &) && sleep 3
curl -s "http://localhost:8000/api/v1/agents/search?q=karla%20zavala" | python3 -m json.tool
curl -s "http://localhost:8000/api/v1/agents/search?q=000000" | python3 -m json.tool
kill %1 2>/dev/null || pkill -f "uvicorn app.main:app --port 8000"
```

Expected: pruebas verdes. La búsqueda por nombre devuelve coincidencias con `source.title` del Acuerdo 30/2026 y su URL; la placa inexistente devuelve `results: []` con `source` presente. Si "karla zavala" ya no está en la lista de 2026, usa cualquier nombre del PDF.

- [ ] **Step 8: Commit**

```bash
cd /home/alexis/Projects/abogadazo
git add .gitignore data/sources.json data/legal-sources/acuerdo-agentes-transito.pdf \
  data/legal-sources/reforma-reglamento-transito-2026-06-30.pdf backend/app/services/agents_import.py \
  backend/scripts/import_agents.py backend/tests/test_agents_import.py frontend/src README.md CLAUDE.md
git commit -m "feat: import authorized agents from Acuerdo 30/2026 and retire the 2024 CSV

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Hallazgos que el cliente debe conocer (se reportan al cerrar la fase)

- Los textos "vigentes" de la Consejería van atrasados respecto a algunas reformas: el Reglamento llega a nov-2024 (por eso se agrega el decreto del 30-jun-2026) y la Ley de Movilidad a dic-2021. Cómo combinar el texto base con los decretos posteriores se decide en el spec de la Fase 1.
- Policía Auxiliar y PBI: se modelan solo si el Acuerdo 30/2026 los distingue por elemento (ver Task 6, Step 4).
