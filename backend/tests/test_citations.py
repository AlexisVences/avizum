from app.services.agent.citations import resolve_citations
from app.services.agent.context import CitationRegistry
from app.services.retrieval import SearchHit


def registry_with(*articles: str) -> CitationRegistry:
    registry = CitationRegistry()
    for i, article in enumerate(articles, start=1):
        registry.register(SearchHit(
            i, "reglamento-transito", "Reglamento de Tránsito", article, "II" if article == "33" else None,
            "h", "t", 30 + i, 30 + i, 0.0, 0.5, source_url="https://x.mx/r.pdf",
        ))
    return registry


def test_only_the_citations_the_text_uses_are_kept_in_order_of_first_appearance():
    registry = registry_with("30", "33", "62", "64")  # [1]..[4]
    resolved = resolve_citations("Primero lo del 64 [4]. Luego el 30 [1] y otra vez el 64 [4].", registry)
    assert [(c["n"], c["orden"], c["article"]) for c in resolved.citations] == [(4, 1, "64"), (1, 2, "30")]
    assert resolved.anomalies == []


def test_a_citation_carries_everything_the_interface_needs():
    resolved = resolve_citations("Se inmoviliza [2].", registry_with("30", "33"))
    assert resolved.citations == [{
        "n": 2, "orden": 1, "source_slug": "reglamento-transito", "source_title": "Reglamento de Tránsito",
        "article": "33", "fraction": "II", "page": 32, "url": "https://x.mx/r.pdf#page=32",
    }]


def test_a_marker_that_matches_no_fragment_is_removed_and_reported():
    resolved = resolve_citations("La multa es de 10 UMA [1] y aplica siempre [99].", registry_with("30"))
    assert resolved.text == "La multa es de 10 UMA [1] y aplica siempre."
    assert [c["n"] for c in resolved.citations] == [1]
    assert resolved.anomalies == [{"tipo": "marca_invalida", "n": 99}]


def test_grouped_markers_are_normalised_and_each_one_is_validated():
    resolved = resolve_citations("Aplica en ambos casos [1, 2] y también [1; 7].", registry_with("30", "33"))
    assert resolved.text == "Aplica en ambos casos [1][2] y también [1]."
    assert [c["n"] for c in resolved.citations] == [1, 2]
    assert {"tipo": "marca_invalida", "n": 7} in resolved.anomalies


def test_tools_ran_but_the_answer_cites_nothing_is_flagged():
    resolved = resolve_citations("La multa es de 1,000 pesos.", registry_with("30"))
    assert resolved.citations == [] and resolved.anomalies == [{"tipo": "sin_citas"}]


def test_a_refusal_with_no_tool_results_is_not_an_anomaly():
    resolved = resolve_citations("Solo atiendo temas de tránsito en la CDMX.", CitationRegistry())
    assert resolved.text == "Solo atiendo temas de tránsito en la CDMX." and resolved.anomalies == []


def test_any_marker_in_an_answer_with_no_fragments_is_invalid():
    resolved = resolve_citations("Es así [1].", CitationRegistry())
    assert resolved.text == "Es así." and resolved.anomalies == [{"tipo": "marca_invalida", "n": 1}]
