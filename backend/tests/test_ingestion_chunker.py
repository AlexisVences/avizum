from app.services.ingestion.chunker import chunk_article
from app.services.ingestion.parser import ParsedArticle


def words(text: str) -> int:
    return len(text.split())


def article(lines_and_pages: list[tuple[str, int]], number: str = "30") -> ParsedArticle:
    return ParsedArticle(
        article=number,
        heading_path="Reglamento › Título Tercero › Art. " + number,
        lines=tuple(line for line, _ in lines_and_pages),
        line_pages=tuple(page for _, page in lines_and_pages),
    )


LONG = article([
    ("Artículo 30. Se prohíbe estacionar cualquier vehículo:", 31),
    ("I. Sobre banquetas y cruces peatonales,", 31),
    ("para ello basta una parte del vehículo;", 32),
    ("Los conductores serán sancionados con multa de 10, 15 o 20 veces la UMA.", 32),
    ("II. En doble fila;", 33),
    ("III Bis. Frente a rampas de acceso.", 34),
])


def test_short_article_is_a_single_chunk_with_article_pages():
    short = article([("Artículo 1.- Objeto del reglamento.", 1), ("Segunda línea.", 2)], "1")
    [chunk] = chunk_article(short, max_tokens=800, count_tokens=words)
    assert (chunk.article, chunk.fraction) == ("1", None)
    assert (chunk.page_start, chunk.page_end) == (1, 2)
    assert chunk.heading_path == short.heading_path


def test_long_article_splits_by_fraction_and_repeats_the_intro():
    chunks = chunk_article(LONG, max_tokens=20, count_tokens=words)
    assert [c.fraction for c in chunks] == ["I", "II", "III Bis"]
    assert all(c.text.startswith("Artículo 30. Se prohíbe estacionar cualquier vehículo:\n") for c in chunks)
    assert chunks[1].heading_path == "Reglamento › Título Tercero › Art. 30, fr. II"


def test_the_penalty_paragraph_stays_with_its_fraction_and_pages_follow_the_fraction():
    first, second, _ = chunk_article(LONG, max_tokens=20, count_tokens=words)
    assert "multa de 10, 15 o 20 veces la UMA" in first.text
    assert "multa" not in second.text
    assert (first.page_start, first.page_end) == (31, 32)  # the intro line (page 31) does not widen it beyond the fraction
    assert (second.page_start, second.page_end) == (33, 33)


def test_token_count_covers_what_will_be_embedded():
    [chunk] = chunk_article(article([("Artículo 1.- Texto corto.", 1)], "1"), max_tokens=800, count_tokens=words)
    assert chunk.embedding_text == f"{chunk.heading_path}\n{chunk.text}"
    assert chunk.token_count == words(chunk.embedding_text)


def test_long_article_without_fractions_is_cut_by_lines_repeating_the_first_line():
    flat = article([("Artículo 5.- " + "uno dos tres cuatro", 1)] + [(f"línea {n} " + "palabra " * 5, 1 + n // 2) for n in range(6)], "5")
    chunks = chunk_article(flat, max_tokens=20, count_tokens=words)
    assert len(chunks) > 1
    assert all(c.fraction is None and c.text.startswith("Artículo 5.- uno dos tres cuatro") for c in chunks)
    assert all(c.token_count <= 20 for c in chunks)


def test_fraction_labels_with_bis_in_capitals_start_a_fraction():
    capitals = article([
        ("Artículo 28.- Son infracciones:", 14),
        ("I. Primera", 14),
        ("V BIS. Vender bebidas alcohólicas en la vía pública", 15),
        ("VI. Otra", 15),
    ], "28")
    assert [c.fraction for c in chunk_article(capitals, max_tokens=12, count_tokens=words)] == ["I", "V Bis", "VI"]


INCISOS = article([
    ("Artículo 59.- Los agentes procederán de la manera siguiente:", 57),
    ("II. Cuando se trate de conductores de vehículos motorizados:", 57),
    ("a) Indicará al conductor que detenga la marcha de su vehículo en un lugar adecuado;", 57),
    ("b) Se identificará con su nombre y número de placa;", 58),
    ("e) Solicitará licencia para conducir, tarjeta de circulación y póliza de seguro vigente,", 58),
    ("documentos que serán entregados para su revisión;", 59),
    ("Los conductores que infrinjan la presente disposición serán sancionados con multa de 5, 7 o 10 UMA.", 59),
    ("III. Cuando se trate de ciclistas:", 59),
    ("Se les amonestará verbalmente.", 59),
], "59")


def test_a_long_fraction_with_incisos_is_cut_by_inciso_repeating_intro_and_fraction_header():
    chunks = chunk_article(INCISOS, max_tokens=30, count_tokens=words, inciso_min_tokens=20)
    assert [c.fraction for c in chunks] == ["II, inc. a)", "II, inc. b)", "II, inc. e)", "II, párrafo final", "III"]
    documents = chunks[2]
    assert documents.text.splitlines()[:3] == [
        "Artículo 59.- Los agentes procederán de la manera siguiente:",
        "II. Cuando se trate de conductores de vehículos motorizados:",
        "e) Solicitará licencia para conducir, tarjeta de circulación y póliza de seguro vigente,",
    ]
    assert "documentos que serán entregados para su revisión;" in documents.text
    assert "multa" not in documents.text
    assert documents.heading_path.endswith("Art. 59, fr. II, inc. e)")
    assert (documents.page_start, documents.page_end) == (57, 59)  # fraction header page through the inciso's last line


def test_the_closing_paragraph_stays_separate_so_the_sanction_is_not_pinned_to_the_last_inciso():
    chunks = chunk_article(INCISOS, max_tokens=30, count_tokens=words, inciso_min_tokens=20)
    final = next(c for c in chunks if c.fraction == "II, párrafo final")
    assert "multa de 5, 7 o 10 UMA" in final.text and "Solicitará licencia" not in final.text


def test_a_fraction_under_the_inciso_threshold_is_left_whole():
    chunks = chunk_article(INCISOS, max_tokens=30, count_tokens=words, inciso_min_tokens=500)
    assert [c.fraction for c in chunks] == ["II", "III"]


HEAVY = article(
    [("Artículo 64.- " + "regla " * 40, 70)]
    + [("la tabla de puntos explica " + "sanción " * 30, 70)]
    + [("I. Limpieza de centros públicos;", 71), ("II. Obras de ornato;", 71)],
    "64",
)


def test_a_heavy_intro_becomes_its_own_chunk_and_fractions_repeat_only_the_article_opening():
    chunks = chunk_article(HEAVY, max_tokens=60, count_tokens=words, heavy_intro_tokens=50)
    assert [c.fraction for c in chunks] == [None, "I", "II"]
    intro, first = chunks[0], chunks[1]
    assert "la tabla de puntos explica" in intro.text and "Limpieza" not in intro.text
    assert "la tabla de puntos explica" not in first.text  # not duplicated into every fraction
    assert first.text.startswith("Artículo 64.- regla") and "I. Limpieza de centros públicos;" in first.text


def test_a_light_intro_is_still_repeated_in_each_fraction():
    chunks = chunk_article(LONG, max_tokens=20, count_tokens=words, heavy_intro_tokens=50)
    assert all(c.text.startswith("Artículo 30. Se prohíbe estacionar cualquier vehículo:\n") for c in chunks)
