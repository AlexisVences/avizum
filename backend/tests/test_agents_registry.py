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
        with pytest.raises(IntegrityError):
            add_agent(db, source, "1151407", "ABARCA CASTRO YANELI")
            db.commit()


def test_only_one_current_version_per_source_slug(client):
    _, factory = client
    with factory() as db:
        add_agents_source(db, sha256="a" * 64)
        db.commit()
        with pytest.raises(IntegrityError):
            add_agents_source(db, sha256="b" * 64)
            db.commit()
