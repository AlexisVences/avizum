from decimal import Decimal

from app.services.sanction_eval import amount_in_answer, confuser_in_answer, resolve_ref

UMA = Decimal("117.31")


def _entry(article, fraction, inciso, triple, applies_to=None, slug="reglamento-transito", points=1):
    low, mid, high = triple
    return {"source_slug": slug, "article": article, "fraction": fraction, "inciso": inciso, "applies_to": applies_to,
            "uma_min": str(low), "uma_mid": str(mid) if mid else None, "uma_max": str(high) if high else None,
            "points_license": points}


ENTRIES = [
    _entry("37", "II", "b", (5, 7, 10)), _entry("37", "II", "c", (10, 15, 20)),
    _entry("37", "III", "b", (10, 15, 20)), _entry("37", "III", "a", (5, 7, 10)),
    _entry("9", "IV", None, (10, 15, 20)), _entry("9", "IV", None, (20, 25, 30), applies_to="En el caso de vehículos de transporte público"),
]


def test_a_reference_resolves_to_the_verified_row_with_pesos_and_confusers():
    resolved = resolve_ref(ENTRIES, {"source": "reglamento-transito", "article": "37", "fraction": "II", "inciso": "b"}, UMA)
    assert resolved["uma"] == ["5", "7", "10"]
    assert resolved["pesos"] == ["586.55", "821.17", "1173.10"]
    # the other fraction's b) (10/15/20) and the inciso c) of the same fraction are what a wrong answer would say
    assert ["10", "15", "20"] in resolved["confusers"]


def test_qualified_rows_are_told_apart_and_an_unresolvable_reference_is_none():
    base = {"source": "reglamento-transito", "article": "9", "fraction": "IV"}
    assert resolve_ref(ENTRIES, base, UMA)["uma"] == ["10", "15", "20"]
    assert resolve_ref(ENTRIES, {**base, "applies_to_contains": "transporte público"}, UMA)["uma"] == ["20", "25", "30"]
    assert resolve_ref(ENTRIES, {"source": "reglamento-transito", "article": "37", "fraction": "II", "inciso": "z"}, UMA) is None
    assert resolve_ref(ENTRIES, {"source": "reglamento-transito", "article": "999"}, UMA) is None
    assert resolve_ref([], base, UMA) is None  # nothing verified: the case is skipped, not guessed


def test_amounts_are_found_as_multiples_or_as_pesos_in_any_common_format():
    assert amount_in_answer("5, 7 o 10 veces la UMA", ["5", "7", "10"], ["586.55", "821.17", "1173.10"])
    assert amount_in_answer("de $586.55 a $1,173.10, media $821.17", ["5", "7", "10"], ["586.55", "821.17", "1173.10"])
    assert not amount_in_answer("de 10, 15 o 20 veces", ["5", "7", "10"], ["586.55", "821.17", "1173.10"])
    assert not amount_in_answer("cincuenta UMA", ["5", "7", "10"], ["586.55"])


def test_a_confuser_triple_is_flagged_unless_it_is_also_the_right_amount():
    confusers = [["10", "15", "20"], ["5", "7", "10"]]
    assert confuser_in_answer("La multa es de 10, 15 o 20 veces la UMA", ["5", "7", "10"], confusers) == [["10", "15", "20"]]
    assert confuser_in_answer("La multa es de 5, 7 o 10 veces la UMA", ["5", "7", "10"], confusers) == []
    assert confuser_in_answer("de 110, 150 o 200", ["5", "7", "10"], confusers) == []  # "10, 15 o 20" inside bigger numbers
