from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from app.models.domain import (
    EMBEDDING_DIMENSIONS, LegalChunk, LegalSanction, OfficialSource, SanctionStatus, UserRole,
)
from app.services.admin.sources import list_sources, pending_sanctions
from tests.admin_support import make_user

URL = "/api/v1/admin/sources"
TODAY = date(2026, 10, 27)


def _source(db, slug="reglamento", sha="a", current=True, retrieved=None, kind="reglamento",
            title="Reglamento"):
    source = OfficialSource(
        slug=slug, title=title, kind=kind, url=f"https://x.mx/{slug}.pdf", sha256=sha * 64,
        is_current=current,
        retrieved_at=retrieved or datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc),
    )
    db.add(source)
    db.flush()
    return source


def _chunks(db, source, n):
    rows = [
        LegalChunk(
            source_id=source.id, article=str(i + 1), heading_path=f"Art. {i + 1}", text="t",
            page_start=1, page_end=1, token_count=1, embedding=[0.0] * EMBEDDING_DIMENSIONS,
        )
        for i in range(n)
    ]
    db.add_all(rows)
    db.flush()
    return rows


def _sanction(chunk, ordinal, status=SanctionStatus.PENDING):
    return LegalSanction(
        chunk_id=chunk.id, ordinal=ordinal, source_slug="reglamento", article="1",
        conduct_text="c", clause_text="5 veces la UMA", uma_min=Decimal("5"),
        chunk_hash="a" * 64, extractor_version="test", status=status,
    )


def test_solo_lista_la_version_vigente_de_cada_fuente_y_cuenta_cuantas_versiones_hay(client):
    _, factory = client
    with factory() as db:
        _source(db, sha="a", current=False)
        _source(db, sha="b", current=False)
        _source(db, sha="c", current=True)
        _source(db, slug="otra", sha="d", title="Otra")
        db.commit()
        rows = list_sources(db, today=TODAY)
    assert [(r.slug, r.versions) for r in rows] == [("otra", 1), ("reglamento", 3)]


def test_se_ordena_por_tipo_y_titulo(client):
    _, factory = client
    with factory() as db:
        _source(db, slug="a", kind="reglamento", title="Zeta")
        _source(db, slug="b", kind="acuerdo", title="Beta")
        _source(db, slug="c", kind="reglamento", title="Alfa")
        db.commit()
        rows = list_sources(db, today=TODAY)
    assert [r.slug for r in rows] == ["b", "c", "a"]


def test_chunk_count_cuenta_los_fragmentos_de_la_version_vigente(client):
    _, factory = client
    with factory() as db:
        old = _source(db, sha="a", current=False)
        new = _source(db, sha="b", current=True)
        _chunks(db, old, 5)
        _chunks(db, new, 3)
        db.commit()
        rows = list_sources(db, today=TODAY)
    assert [r.chunk_count for r in rows] == [3]


def test_review_due_es_verdadero_a_los_366_dias_y_falso_a_los_365(client):
    _, factory = client
    retrieved = datetime(2025, 10, 26, 12, 0, tzinfo=timezone.utc)
    with factory() as db:
        _source(db, slug="viejo", retrieved=retrieved, title="A")
        db.commit()
        due = list_sources(db, today=retrieved.date() + timedelta(days=366))[0]
        not_due = list_sources(db, today=retrieved.date() + timedelta(days=365))[0]
    assert due.review_due is True
    assert due.review_due_since == retrieved.date() + timedelta(days=366)
    assert not_due.review_due is False
    assert not_due.review_due_since is None


def test_una_fuente_sin_fragmentos_el_acuerdo_de_agentes_aparece_con_0(client):
    _, factory = client
    with factory() as db:
        _source(db, slug="agentes", kind="acuerdo")
        db.commit()
        rows = list_sources(db, today=TODAY)
    assert [(r.slug, r.chunk_count) for r in rows] == [("agentes", 0)]


def test_pending_sanctions_cuenta_solo_las_pendientes(client):
    _, factory = client
    with factory() as db:
        chunk = _chunks(db, _source(db), 1)[0]
        db.add_all([
            _sanction(chunk, 0), _sanction(chunk, 1),
            _sanction(chunk, 2, SanctionStatus.VERIFIED),
        ])
        db.commit()
        assert pending_sanctions(db) == 2


def test_el_endpoint_devuelve_fuentes_y_sanciones_pendientes(client):
    http, factory = client
    _, headers = make_user(factory, email="a@example.com", role=UserRole.ADMIN)
    with factory() as db:
        chunk = _chunks(db, _source(db), 2)[0]
        db.add(_sanction(chunk, 0))
        db.commit()
    body = http.get(URL, headers=headers).json()
    assert body["pending_sanctions"] == 1
    assert len(body["sources"]) == 1
    row = body["sources"][0]
    assert row["slug"] == "reglamento"
    assert row["chunk_count"] == 2
    assert row["versions"] == 1
    assert set(row) == {
        "slug", "title", "kind", "url", "last_reform_date", "retrieved_at", "chunk_count",
        "versions", "review_due", "review_due_since",
    }


def test_403_a_un_usuario_normal_y_401_sin_sesion(client):
    http, factory = client
    _, headers = make_user(factory, email="u@example.com")
    assert http.get(URL, headers=headers).status_code == 403
    assert http.get(URL).status_code == 401
