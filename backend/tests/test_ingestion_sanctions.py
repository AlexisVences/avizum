"""Golden cases for the sanction extractor: real chunks (tests/fixtures/sanctions/chunks.json, copied from the
indexed corpus) with the expected rows written by hand from the article text, plus synthetic edge cases."""
import json
from decimal import Decimal as D
from pathlib import Path

from app.services.ingestion.sanctions import chunk_hash, extract_sanctions

CHUNKS = json.loads((Path(__file__).parent / "fixtures" / "sanctions" / "chunks.json").read_text(encoding="utf-8"))


def _run(key: str):
    chunk = CHUNKS[key]
    return extract_sanctions(chunk["article"], chunk["fraction"], chunk["text"])


def _tuples(extraction):
    return [
        (s.fraction, s.inciso, s.uma_min, s.uma_mid, s.uma_max, s.points_license, s.points_plate, s.applies_to)
        for s in extraction.sanctions
    ]


def test_art_37_fraction_II_maps_each_inciso_to_its_own_clause():
    """The case that failed in production: the seat belt is inciso b), 5/7/10 UMA, not 10/15/20 (that is inciso c)."""
    result = _run("37_II")
    assert result.issues == []
    assert _tuples(result) == [
        ("II", "a", D(5), D(7), D(10), 1, 1, None),
        ("II", "b", D(5), D(7), D(10), 1, 1, None),
        ("II", "c", D(10), D(15), D(20), 3, 3, None),
        ("II", "d", D(5), D(7), D(10), 1, 1, None),
        ("II", "e", D(5), D(7), D(10), 1, 1, None),
    ]
    seat_belt = result.sanctions[1]
    assert "cinturón de seguridad" in seat_belt.conduct_text
    assert seat_belt.clause_text.startswith("Los conductores de vehículos motorizados que infrinjan los incisos a), b), d) y e)")
    assert [s.ordinal for s in result.sanctions] == [0, 1, 2, 3, 4]


def test_art_37_fraction_III_reuses_the_same_letters_with_different_amounts():
    result = _run("37_III")
    assert result.issues == []
    by_inciso = {s.inciso: (s.uma_min, s.uma_mid, s.uma_max, s.points_license) for s in result.sanctions}
    assert by_inciso == {
        "a": (D(5), D(7), D(10), 1), "c": (D(5), D(7), D(10), 1), "e": (D(5), D(7), D(10), 1), "g": (D(5), D(7), D(10), 1),
        "b": (D(10), D(15), D(20), 3), "d": (D(10), D(15), D(20), 3), "e Bis": (D(10), D(15), D(20), 3),
        "f": (D(10), D(15), D(20), 3),
    }
    # b) is 5/7/10 in fraction II and 10/15/20 in fraction III: rows must never be mixed across fractions.
    assert {s.fraction for s in result.sanctions} == {"III"}


def test_art_38_fraction_IV_reads_dotted_incisos():
    result = _run("38_IV")
    assert result.issues == []
    assert [(s.inciso, s.uma_max, s.points_license) for s in result.sanctions] == [("a", D(20), 3), ("b", D(20), 3)]
    assert "vidrios polarizados" in result.sanctions[1].conduct_text


def test_art_43_gives_each_of_its_seven_fractions_its_own_penalty():
    result = _run("43")
    assert result.issues == []
    assert [(s.fraction, s.uma_min, s.uma_max) for s in result.sanctions] == [
        ("I", D(20), D(30)), ("II", D(10), D(20)), ("III", D(10), D(20)), ("IV", D(40), D(50)),
        ("V", D(20), D(30)), ("VI", D(20), D(30)), ("VII", D(20), D(30)),
    ]
    assert "antirradares" in result.sanctions[3].conduct_text
    assert "polarizado" in result.sanctions[6].conduct_text


def test_a_vehicle_type_override_becomes_a_second_row_with_applies_to():
    result = _run("conditional")  # Art. 9 IV, 30 km/h
    assert result.issues == []
    general, override = result.sanctions
    assert (general.uma_min, general.uma_max, general.points_license, general.applies_to) == (D(10), D(20), 6, None)
    assert (override.uma_min, override.uma_max, override.points_license) == (D(20), D(30), 6)
    assert override.applies_to == "En el caso de vehículos de transporte público de pasajeros y carga"
    # "uno a cinco puntos a la matrícula" depends on the excess: not forced into a single number
    assert general.points_plate is None and "uno a cinco puntos a la matrícula" in general.other_consequences


def test_what_cannot_be_read_without_guessing_is_reported_and_produces_no_row():
    table = _run("table")  # penalties by vehicle type laid out as a table
    assert table.sanctions == [] and [i.kind for i in table.issues] == ["tabla"]

    ranges = _run("range")  # Ley de Cultura Cívica: "de 1 a 10 veces", a judge's range, not three fixed levels
    assert ranges.sanctions == [] and {i.kind for i in ranges.issues} == {"rango"}


def _article(body: str) -> str:
    return f"Artículo 99.- Intro. I. Los conductores deben: {body}"


def test_a_clause_naming_an_inciso_the_fraction_lacks_is_an_issue_not_a_row():
    text = _article(
        "a) Hacer algo; b) Hacer otra cosa. Los conductores que infrinjan el inciso z) de la presente disposición "
        "serán sancionados con una multa equivalente a 5, 7 o 10 veces la Unidad de Medida y Actualización vigente."
    )
    result = extract_sanctions("99", "I", text)
    assert result.sanctions == []
    assert {i.kind for i in result.issues} == {"inciso_desconocido"}


def test_incisos_left_without_a_clause_are_reported():
    text = _article(
        "a) Hacer algo; b) Hacer otra cosa; c) Una más. Los conductores que infrinjan los incisos a) y b) de la "
        "presente disposición serán sancionados con una multa equivalente a 5, 7 o 10 veces la Unidad de Medida y "
        "Actualización vigente."
    )
    result = extract_sanctions("99", "I", text)
    assert [s.inciso for s in result.sanctions] == ["a", "b"]
    assert [i.kind for i in result.issues] == ["cobertura_incompleta"]
    assert "c" in result.issues[0].detail


def test_two_clauses_for_the_same_inciso_are_reported():
    text = _article(
        "a) Hacer algo; b) Hacer otra cosa. Quien infrinja el inciso a) será sancionado con una multa equivalente a "
        "5, 7 o 10 veces la Unidad de Medida y Actualización vigente. Quien infrinja los incisos a) y b) será "
        "sancionado con una multa equivalente a 10, 15 o 20 veces la Unidad de Medida y Actualización vigente."
    )
    result = extract_sanctions("99", "I", text)
    assert "cobertura_duplicada" in [i.kind for i in result.issues]


def test_a_range_of_incisos_is_expanded():
    text = _article(
        "a) Uno; b) Dos; c) Tres; d) Cuatro. Los conductores que infrinjan los incisos a) al c) de la presente "
        "disposición serán sancionados con una multa equivalente a 5, 7 o 10 veces la Unidad de Medida y "
        "Actualización vigente. Quien infrinja el inciso d) será sancionado con una multa equivalente a 10, 15 o "
        "20 veces la Unidad de Medida y Actualización vigente."
    )
    result = extract_sanctions("99", "I", text)
    assert result.issues == []
    assert [(s.inciso, s.uma_min) for s in result.sanctions] == [("a", D(5)), ("b", D(5)), ("c", D(5)), ("d", D(10))]


def test_text_without_a_penalty_produces_nothing():
    result = extract_sanctions("5", None, "Artículo 5.- Los peatones tienen preferencia en los cruces.")
    assert result.sanctions == [] and result.issues == []


def test_every_clause_and_conduct_is_a_verbatim_part_of_the_chunk():
    for key, chunk in CHUNKS.items():
        flat = " ".join(chunk["text"].split())
        for sanction in extract_sanctions(chunk["article"], chunk["fraction"], chunk["text"]).sanctions:
            assert sanction.clause_text in flat, (key, sanction.ordinal)
            assert sanction.conduct_text in flat, (key, sanction.ordinal)


def test_chunk_hash_changes_when_the_text_changes():
    assert chunk_hash("a") == chunk_hash("a") and chunk_hash("a") != chunk_hash("a ")
    assert len(chunk_hash("a")) == 64


def test_a_typo_in_the_clause_list_does_not_silently_drop_incisos():
    """Art. 38 III really says "los incisos c), d) e), f) y g)" (no comma): e, f and g must still be covered."""
    text = _article(
        "a) Uno; b) Dos; c) Tres; d) Cuatro; e) Cinco; f) Seis; g) Siete. Los conductores que infrinjan los incisos "
        "a) y b) de la presente disposición serán sancionados con una multa equivalente a 5, 7 o 10 veces la Unidad "
        "de Medida y Actualización vigente. En caso de infringir lo dispuesto en los incisos c), d) e), f) y g) de "
        "esta fracción, serán sancionados con una multa equivalente a 10, 15 o 20 veces la Unidad de Medida y "
        "Actualización vigente."
    )
    result = extract_sanctions("99", "I", text)
    assert result.issues == []
    assert [s.inciso for s in result.sanctions if s.uma_min == D(10)] == ["c", "d", "e", "f", "g"]


def test_a_comma_before_the_last_inciso_marker_is_accepted():
    text = _article("a) Uno; b) Dos, y c) Tres. El incumplimiento de las obligaciones previstas en esta fracción, se sancionará con una multa equivalente a 5, 7 o 10 veces la Unidad de Medida y Actualización vigente.")
    result = extract_sanctions("99", "I", text)
    assert result.issues == [] and [s.inciso for s in result.sanctions] == [None]


def test_amounts_written_in_words_are_read():
    clause = (
        "Artículo 66.- Cuerpo. Serán sancionadas con la remisión del vehículo al depósito y una multa de ciento "
        "ochenta veces la Unidad de Medida y Actualización vigente."
    )
    result = extract_sanctions("66", None, clause)
    assert result.issues == []
    (row,) = result.sanctions
    assert (row.uma_min, row.uma_mid, row.uma_max) == (D(180), None, None)
    assert "depósito" in row.other_consequences


def test_a_range_written_in_words_is_not_taken_as_one_amount():
    clause = "Artículo 5.- Se sancionará con multa de trescientos cincuenta a cuatrocientos cincuenta veces la Unidad de Medida y Actualización vigente."
    result = extract_sanctions("5", None, clause)
    assert result.sanctions == [] and [i.kind for i in result.issues] == ["rango"]


def test_thousands_in_words_and_amounts_that_are_not_penalties():
    penalty = "Artículo 5.- Se sancionará con multa de quinientos a mil veces la Unidad de Medida y Actualización vigente."
    result = extract_sanctions("5", None, penalty)
    assert result.sanctions == [] and [i.kind for i in result.issues] == ["rango"]

    coverage = (
        "Artículo 90.- La cobertura mínima asegurada por evento deberá ser de al menos cincuenta mil veces la Unidad "
        "de Medida y Actualización de la Ciudad de México vigente."
    )
    result = extract_sanctions("90", None, coverage)
    assert result.sanctions == [] and result.issues == []  # not a penalty: ignored, not an error


def test_a_conduct_with_no_penalty_in_its_fraction_is_reported_not_invented():
    """Art. 44 IV: the clause covers incisos a) and b) only; c) has no sanction in the text."""
    text = (
        "Artículo 44.- Intro. IV. Los conductores de transporte escolar deberán: a) Licencia; b) Cromática; y, "
        "c) Contar con el permiso. El incumplimiento de las obligaciones señaladas en los incisos a) y b) de la "
        "presente disposición, se sancionará con una multa equivalente a 60, 70 o 80 veces la Unidad de Medida y "
        "Actualización vigente."
    )
    result = extract_sanctions("44", "IV", text)
    assert [s.inciso for s in result.sanctions] == ["a", "b"]
    assert [i.kind for i in result.issues] == ["cobertura_incompleta"] and "c" in result.issues[0].detail
