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
