from app.services.ingestion.parser import parse_articles

TITLE = "Reglamento de Tránsito CDMX"

PAGES = [
    # page 1: preamble before the first article, then title + chapter headings
    "PUBLICADO EN LA GACETA\nTÍTULO PRIMERO\nDISPOSICIONES GENERALES\nCAPÍTULO I\nDEL OBJETO\n"
    "Artículo 1.- Este reglamento regula la circulación.\nArtículo 2.- Se basa en principios.\n",
    # page 2: article 2 continues; a cross-reference starts a line in lowercase and must NOT open an article
    "y además en otros.\nartículo 10; cuando haya vehículos esperando.\n"
    "TÍTULO SEGUNDO\nDE LOS CONDUCTORES\nCAPÍTULO II\nDE LAS MEDIDAS\nPARA LA SEGURIDAD\n"
    "Artículo 3 Bis.- Texto del bis.\n",
    # page 3: the last article shares the page with TRANSITORIOS
    "Artículo 4.- Último artículo.\nTRANSITORIOS\nPrimero.- Entra en vigor mañana.\n",
    # page 4: annex after the transitorios, must be ignored
    "Artículo 99.- Esto no es del articulado.\n",
]


def test_splits_articles_and_tracks_pages():
    articles = parse_articles(PAGES, TITLE)
    assert [a.article for a in articles] == ["1", "2", "3 Bis", "4"]
    two = articles[1]
    assert (two.page_start, two.page_end) == (1, 2)
    assert two.text == "Artículo 2.- Se basa en principios.\ny además en otros.\nartículo 10; cuando haya vehículos esperando."


def test_heading_path_uses_title_and_chapter_names():
    articles = parse_articles(PAGES, TITLE)
    assert articles[0].heading_path == f"{TITLE} › Título Primero: Disposiciones generales › Capítulo I: Del objeto › Art. 1"
    assert articles[2].heading_path == (
        f"{TITLE} › Título Segundo: De los conductores › Capítulo II: De las medidas para la seguridad › Art. 3 Bis"
    )


def test_stops_at_transitorios_inside_a_page_and_keeps_the_article_before_it():
    articles = parse_articles(PAGES, TITLE)
    assert articles[-1].article == "4"
    assert "Entra en vigor" not in articles[-1].text
    assert all(a.article != "99" for a in articles)


def test_recognizes_the_spellings_used_by_other_cdmx_laws():
    pages = [
        "Artículo 1º.- Orden público.\nArtículo 5º BIS.- Dependencias.\nArtículo 6.- Actos.\n"
        "Articulo 7.- Sin acento.\nArtículo 8 Ter.- Con sufijo.\nartículo 28 y se negare a repararlo, será sancionado.\n"
        "ARTÍCULO 78; UN CUARTO PÁRRAFO.\n",
    ]
    assert [a.article for a in parse_articles(pages, TITLE)] == ["1", "5 Bis", "6", "7", "8 Ter"]


def test_accepts_uppercase_articles_and_drops_running_headers():
    header = "CÓDIGO FISCAL DE LA CIUDAD DE MÉXICO"
    pages = [f"{header}\nARTÍCULO 230.- Servicio de grúa.\nI. Hasta 3.5 toneladas\n"] + [f"{header}\ncontinúa el texto {n}\n" for n in range(11)]
    [article] = parse_articles(pages, "Código Fiscal")
    assert article.article == "230"
    assert header not in article.text
    assert article.page_end == 12


def test_drops_editorial_amendment_notes():
    pages = ["Artículo 1.- Texto.\nPárrafo reformado en su cuota G.O. CDMX 19/12/25\nSegundo párrafo.\nInciso reformado en su cuota\n"]
    assert parse_articles(pages, TITLE)[0].lines == ("Artículo 1.- Texto.", "Segundo párrafo.")


def test_fraction_labels_repeated_on_many_pages_are_not_running_headers():
    # "I." / "II." appear on most pages of a long law; only long repeated lines are page headers.
    header = "LEY DE CULTURA CÍVICA DE LA CIUDAD DE MÉXICO"
    pages = [f"{header}\nArtículo 28.- Son infracciones:\nI.\nPrimera conducta\nII.\nSegunda conducta\n"] + [f"{header}\nI.\nII.\ntexto {n}\n" for n in range(11)]
    [article] = parse_articles(pages, "Ley")
    assert "I." in article.lines and "II." in article.lines
    assert header not in article.text


from app.services.ingestion.parser import parse_sections

PROTOCOL = [
    "PROTOCOLO GENERAL DE ACTUACIÓN POLICIAL\nCAPÍTULO CUARTO\n"
    "CAPÍTULO CUARTO. PROCEDIMIENTOS Y PAUTAS DE ACCIÓN PARA LA\nFUNCIÓN POLICIAL\n"
    "4.4 USO DE LA FUERZA\nEl uso de la fuerza se regirá por principios.\n",
    "PROTOCOLO GENERAL DE ACTUACIÓN POLICIAL\nCAPÍTULO CUARTO\n"
    "4.5 DETENCIONES\nI. Supuestos legales para la detención\nSolo en flagrancia.\n"
    "4.4 de este protocolo no aplica aquí.\nII. Aspectos a observar\nTrato digno.\n",
    "PROTOCOLO GENERAL DE ACTUACIÓN POLICIAL\nCAPÍTULO CUARTO\ncontinúa la inspección.\nTRANSITORIOS\nÚnico.- Vigente.\n",
]

FILLER = ["PROTOCOLO GENERAL DE ACTUACIÓN POLICIAL\nCAPÍTULO CUARTO\nRelleno\n"] * 9


def test_sections_are_numbered_headings_with_chapter_context_and_pages():
    pages = PROTOCOL + FILLER  # >= 10 pages so the running header is detected
    sections = parse_sections(pages, "Protocolo")
    assert [s.article for s in sections] == ["4.4", "4.5"]
    detentions = sections[1]
    assert detentions.heading_path == "Protocolo › Capítulo cuarto: Procedimientos y pautas de acción para la función policial › 4.5 Detenciones"
    assert (detentions.page_start, detentions.page_end) == (2, 3)
    assert "Protocolo General" not in detentions.text and "TRANSITORIOS" not in detentions.text


def test_a_line_that_starts_with_an_earlier_section_number_is_a_reference_not_a_heading():
    sections = parse_sections(PROTOCOL + FILLER, "Protocolo")
    assert "4.4 de este protocolo no aplica aquí." in sections[1].lines


from app.services.ingestion.parser import parse_chapters

PROGRAMA = [
    "GACETA OFICIAL DE LA CIUDAD DE MÉXICO\n1. OBJETIVOS DEL PROGRAMA\nEstablecer el calendario.\n"
    "5. CALENDARIO PARA REALIZAR LA VERIFICACIÓN\n5.1. Cada semestre se verifica.\n",
    "GACETA OFICIAL DE LA CIUDAD DE MÉXICO\n18\n5.1.9. Se podrá ampliar el período por 15 días en estos supuestos:\n"
    "1. Haber obtenido un rechazo en los últimos siete días.\n2. Que el portal no refleje un pago.\n"
    "10. VERIFICACIÓN EXTEMPORÁNEA\nPagar 20 veces la UMA.\n",
    "GACETA OFICIAL DE LA CIUDAD DE MÉXICO\n19. TRÁMITES Y SERVICIOS RELACIONADOS CON LA\nOPERACIÓN DEL PROGRAMA\n"
    "Trámites digitales.\nTRANSITORIO\nPRIMERO.- Publíquese.\n",
]
PROGRAMA_FILLER = ["GACETA OFICIAL DE LA CIUDAD DE MÉXICO\nRelleno\n"] * 9


def test_chapters_are_uppercase_numbered_headings_and_keep_the_numerals_inside_them():
    chapters = parse_chapters(PROGRAMA + PROGRAMA_FILLER, "Programa")
    assert [c.article for c in chapters] == ["1", "5", "10", "19"]
    calendario = chapters[1]
    assert calendario.heading_path == "Programa › 5 Calendario para realizar la verificación"
    assert (calendario.page_start, calendario.page_end) == (1, 2)
    assert "5.1.9. Se podrá ampliar el período por 15 días en estos supuestos:" in calendario.lines
    assert "GACETA OFICIAL" not in calendario.text


def test_a_numbered_list_item_is_not_a_chapter_and_a_wrapped_title_is_joined():
    chapters = parse_chapters(PROGRAMA + PROGRAMA_FILLER, "Programa")
    assert "1. Haber obtenido un rechazo en los últimos siete días." in chapters[1].lines
    assert chapters[3].heading_path == "Programa › 19 Trámites y servicios relacionados con la operación del programa"


def test_chapters_stop_at_the_transitorio():
    chapters = parse_chapters(PROGRAMA + PROGRAMA_FILLER, "Programa")
    assert "Publíquese" not in chapters[-1].text and "TRANSITORIO" not in chapters[-1].text


TARIFAS = [
    "SECRETARÍA DE ADMINISTRACIÓN Y FINANZAS\nCONTROL VEHICULAR 2026\nDERECHOS POR SERVICIOS DE CONTROL VEHICULAR:\n"
    "Art. 219\nPor los servicios de control vehicular respecto a vehículos particulares:\n"
    "IV. Por reposición o refrendo de tarjeta de circulación\n$433.00\n",
    "V. Por cambio de propietario, carrocería, motor, domicilio\n$433.00\nArt. 220\nPor los servicios del servicio público:\n$100.00\n"
    "conforme al Art. 219 de este documento\n",
]


def test_tarifas_layout_reads_short_article_headings_alone_on_their_line():
    articles = parse_articles(TARIFAS, "Tarifas", short_headings=True)
    assert [a.article for a in articles] == ["219", "220"]
    assert "V. Por cambio de propietario, carrocería, motor, domicilio $433.00" in articles[0].lines
    assert "conforme al Art. 219 de este documento" in articles[1].lines  # a reference is text, not a heading
    assert articles[0].heading_path == "Tarifas › Art. 219"


def test_short_article_headings_are_ignored_unless_the_layout_asks_for_them():
    assert parse_articles(TARIFAS, "Tarifas") == []


def test_tarifas_layout_keeps_each_amount_on_the_line_of_its_fraction():
    [article, _] = parse_articles(TARIFAS, "Tarifas", short_headings=True)
    assert "IV. Por reposición o refrendo de tarjeta de circulación $433.00" in article.lines
    assert "V. Por cambio de propietario, carrocería, motor, domicilio $433.00" in article.lines
    assert not any(line.startswith("$") for line in article.lines)


from app.services.ingestion.parser import parse_decree

DECRETO = [
    "GACETA OFICIAL DEL DISTRITO FEDERAL\nI.- OBJETIVO DEL PROGRAMA\nEstablecer medidas.\n"
    "II.- ÁMBITO DE APLICACIÓN\nRige en todo el territorio.\nI.- Días.\nII.- Horarios.\n"
    "IV.- REGLAS APLICABLES A LA CIRCULACION CON BASE EN HOLOGRAMAS\nLos hologramas son los del programa.\n"
    "IV.1. “EXENTO”\nQuedan exentos.\n",
    "GACETA OFICIAL DEL DISTRITO FEDERAL\n9\nIV.3. HOLOGRAMA “1”\nSe limita un día entre semana.\nAmarillo\n5 ó 6\nLunes\n"
    "IV.4. HOLOGRAMA “2”\nSe limita un día y todos los sábados.\nAmarillo\n5 ó 6\nLunes\n"
    "V.- VEHÍCULOS MATRICULADOS FUERA DEL DISTRITO FEDERAL Y\nEN EL EXTRANJERO (FORÁNEOS)\nSe limita su circulación.\n"
    "VI. 1. Los foráneos podrán verificar voluntariamente.\n",
    "GACETA OFICIAL DEL DISTRITO FEDERAL\nX.- CRITERIOS DE APLICACIÓN PARA PLACAS\nSe aplica el último dígito.\nTRANSTORIOS\nPRIMERO.- Publíquese.\n",
]


def test_decree_units_are_roman_chapters_and_their_numbered_subsections():
    units = parse_decree(DECRETO + PROGRAMA_FILLER, "Decreto HNC")
    assert [u.article for u in units] == ["I", "II", "IV", "IV.1", "IV.3", "IV.4", "V", "X"]
    holograma_2 = next(u for u in units if u.article == "IV.4")
    assert holograma_2.heading_path == "Decreto HNC › IV Reglas aplicables a la circulacion con base en hologramas › IV.4 Holograma “2”"
    assert "Lunes" in holograma_2.lines and "V.- VEHÍCULOS" not in holograma_2.text
    assert (holograma_2.page_start, holograma_2.page_end) == (2, 2)


def test_decree_keeps_inner_roman_lists_and_unnumbered_chapters_inside_their_unit_and_joins_wrapped_titles():
    units = {u.article: u for u in parse_decree(DECRETO + PROGRAMA_FILLER, "Decreto HNC")}
    assert "I.- Días." in units["II"].lines  # a sentence-case roman item is a list item, not a chapter
    assert units["V"].heading_path == "Decreto HNC › V Vehículos matriculados fuera del distrito federal y en el extranjero (foráneos)"
    assert "VI. 1. Los foráneos podrán verificar voluntariamente." in units["V"].lines
    assert "Publíquese" not in units["X"].text


from app.services.ingestion.parser import parse_ficha

FICHA = """# SEMOVI — Cambio de propietario
Fuente: https://www.semovi.cdmx.gob.mx/x
Consultada: 2026-10-24

Los nuevos propietarios tendrán 15 días hábiles.

## Requisitos
- Identificación oficial vigente.
- Línea de captura pagada.

## Costo
$433.00 (clave 36-7).
"""


def test_a_ficha_is_split_by_its_second_level_headings_and_drops_its_metadata_lines():
    units = parse_ficha(FICHA, "SEMOVI — Cambio de propietario")
    assert [u.article for u in units] == ["Resumen", "Requisitos", "Costo"]
    assert units[0].lines == ("Los nuevos propietarios tendrán 15 días hábiles.",)
    assert units[1].lines == ("Requisitos", "- Identificación oficial vigente.", "- Línea de captura pagada.")
    assert units[2].heading_path == "SEMOVI — Cambio de propietario › Costo"


def test_a_ficha_has_no_page_because_it_is_a_web_page():
    assert all(u.page_start == 0 and u.page_end == 0 for u in parse_ficha(FICHA, "Ficha"))


def test_a_ficha_heading_longer_than_the_article_column_is_cut_for_the_id_but_kept_in_the_path():
    long_heading = "SSC — Dirección General de Asuntos Internos (denuncias contra policías por abusos en la vía pública)"
    [unit] = parse_ficha(f"## {long_heading}\nTeléfono: 55 5208 9898", "Ficha")
    assert len(unit.article) <= 50 and unit.article.endswith("…")
    assert unit.heading_path == f"Ficha › {long_heading}"
