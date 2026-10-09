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
    assert [(r.number, r.plate) for r in via.rows] == [
        (1, "1151407"), (2, "57196"), (3, "1032742"), (4, "885312"), (5, "730249")
    ]
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
