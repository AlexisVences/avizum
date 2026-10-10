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
