import json
from dataclasses import replace
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
        again, changed = register_source(db, replace(SPEC, title="Ley de Movilidad de la CDMX"), "a" * 64)
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
