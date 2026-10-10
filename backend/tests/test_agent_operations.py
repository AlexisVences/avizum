from sqlalchemy import select

from app.models.domain import AgentLookup, AuthorizationType
from app.services.agent.context import AgentContext, CitationRegistry
from app.services.agent.operations import fetch_article, find_agent, search_legislation
from tests.factories import add_agent, add_agents_source
from tests.test_retrieval import FixedQuery, PerQuery, add_chunk, add_source, vec


def context(db, embeddings=None, user_message="pregunta del usuario", user_id=None) -> AgentContext:
    return AgentContext(db=db, user_id=user_id, embeddings=embeddings or FixedQuery(vec(1)), user_message=user_message)


# ---------- buscar_agente

def test_a_plate_in_both_lists_returns_both_authorizations_and_records_the_lookup(client):
    _, factory = client
    with factory() as db:
        source = add_agents_source(db)
        add_agent(db, source, "1163184", "BAUTISTA DONALDO", AuthorizationType.VIA_PUBLICA)
        add_agent(db, source, "1163184", "BAUTISTA DONALDO", AuthorizationType.SISTEMAS_TECNOLOGICOS)
        db.commit()

        ctx = context(db)
        result = find_agent(ctx, "1163184")

        assert result["estado"] == "ok" and result["coincidencia_por"] == "plate"
        assert {r["tipo_autorizacion"] for r in result["resultados"]} == {"via_publica", "sistemas_tecnologicos"}
        assert result["fuente"]["titulo"].startswith("Acuerdo 30/2026")
        citation = ctx.citations.get(result["fuente"]["cita"])
        assert citation.source_slug == "acuerdo-agentes-transito" and citation.page is None
        assert db.scalars(select(AgentLookup)).one().agent_id is not None


def test_an_unknown_plate_says_it_is_not_in_the_current_list_without_calling_the_person_fake(client):
    _, factory = client
    with factory() as db:
        add_agent(db, add_agents_source(db), "100", "PEREZ LOPEZ ANA")
        db.commit()
        result = find_agent(context(db), "999999")
        assert result["estado"] == "sin_coincidencias"
        assert "no aparece en la lista vigente" in result["mensaje"].lower()
        assert "falso" not in result["mensaje"].lower().replace("no es prueba de que", "")


def test_without_an_imported_registry_the_tool_says_unavailable_and_forbids_claiming_absence(client):
    _, factory = client
    with factory() as db:
        result = find_agent(context(db), "1163184")
        assert result["estado"] == "registro_no_disponible"
        assert "NO afirmes que no aparece" in result["mensaje"]


def test_a_query_with_no_plate_or_name_is_invalid(client):
    _, factory = client
    with factory() as db:
        assert find_agent(context(db), "   -- ")["estado"] == "consulta_invalida"


# ---------- buscar_legislacion

def seed_laws(db):
    reglamento = add_source(db, "reglamento-transito", "a")
    movilidad = add_source(db, "ley-movilidad", "b")
    add_chunk(db, reglamento, "33", "Inmovilizador en vehículos estacionados", vec(1, 0), fraction="II", page=35)
    add_chunk(db, reglamento, "9", "Límites de velocidad", vec(0, 1))
    add_chunk(db, movilidad, "64", "Licencia para vehículos eléctricos", vec(1, 0))
    db.commit()


def test_fragments_are_numbered_and_carry_the_official_pdf_page(client):
    _, factory = client
    with factory() as db:
        seed_laws(db)
        ctx = context(db, FixedQuery(vec(1, 0)))
        result = search_legislation(ctx, "inmovilizador", ley="reglamento-transito")

        assert result["estado"] == "ok"
        first = result["fragmentos"][0]
        assert (first["cita"], first["articulo"], first["fraccion"], first["paginas"]) == (1, "33", "II", "35")
        citation = ctx.citations.get(1)
        assert citation.url == "https://x.mx/reglamento-transito.pdf#page=35"
        assert all(f["ley"] == "reglamento-transito" for f in result["fragmentos"])


def test_fraction_results_warn_the_model_to_read_the_whole_article_before_concluding(client):
    _, factory = client
    with factory() as db:
        seed_laws(db)
        with_fraction = search_legislation(context(db, FixedQuery(vec(1, 0))), "inmovilizador", ley="reglamento-transito")
        assert "obtener_articulo" in with_fraction["nota"]
        whole_article = search_legislation(context(db, FixedQuery(vec(0, 1))), "velocidad", ley="reglamento-transito")
        assert [f["fraccion"] for f in whole_article["fragmentos"]] != [] or "nota" not in whole_article


def test_the_same_fragment_keeps_its_number_across_tool_calls(client):
    _, factory = client
    with factory() as db:
        seed_laws(db)
        ctx = context(db, FixedQuery(vec(1, 0)))
        first = search_legislation(ctx, "inmovilizador", ley="reglamento-transito")
        second = search_legislation(ctx, "estacionados", ley="reglamento-transito")
        numbers = {f["articulo"]: f["cita"] for f in first["fragmentos"]}
        assert {f["articulo"]: f["cita"] for f in second["fragmentos"]}["33"] == numbers["33"]
        assert len({c.n for c in ctx.citations.all()}) == len(ctx.citations.all())


def test_results_below_the_relevance_floor_are_reported_as_none_and_not_registered(client):
    _, factory = client
    with factory() as db:
        seed_laws(db)
        ctx = context(db, FixedQuery(vec(0, 0, 1)))  # orthogonal to every chunk
        result = search_legislation(ctx, "receta de mole poblano")
        assert result["estado"] == "sin_resultados_relevantes"
        assert ctx.citations.all() == []


def test_an_unknown_law_slug_lists_the_valid_ones(client):
    _, factory = client
    with factory() as db:
        seed_laws(db)
        result = search_legislation(context(db), "placas", ley="ley-inventada")
        assert result["estado"] == "ley_desconocida"
        assert "reglamento-transito" in result["leyes_validas"] and "ley-movilidad" in result["leyes_validas"]


def test_the_users_own_words_are_a_second_phrasing_that_can_rescue_the_search(client):
    _, factory = client
    with factory() as db:
        seed_laws(db)
        embeddings = PerQuery({"consulta mal formulada": vec(0, 1), "me pusieron la araña": vec(1, 0)})
        ctx = context(db, embeddings, user_message="me pusieron la araña")
        result = search_legislation(ctx, "consulta mal formulada", ley="reglamento-transito")
        assert "33" in [f["articulo"] for f in result["fragmentos"]]


# ---------- obtener_articulo

def test_fetch_article_returns_every_fraction_in_order_and_registers_them(client):
    _, factory = client
    with factory() as db:
        source = add_source(db, "reglamento-transito", "a")
        add_chunk(db, source, "30", "Intro\nI. Banquetas", vec(1), fraction="I", page=31)
        add_chunk(db, source, "30", "Intro\nII. Doble fila", vec(1), fraction="II", page=33)
        db.commit()
        ctx = context(db)
        result = fetch_article(ctx, "reglamento-transito", "30")
        assert [f["fraccion"] for f in result["fragmentos"]] == ["I", "II"]
        assert [f["cita"] for f in result["fragmentos"]] == [1, 2]
        assert fetch_article(ctx, "reglamento-transito", "999")["estado"] == "no_encontrado"


def test_citation_registry_numbers_from_one_and_reuses_numbers():
    from app.services.retrieval import SearchHit

    registry = CitationRegistry()
    hit = lambda chunk_id: SearchHit(chunk_id, "s", "T", "1", None, "h", "t", 4, 4, 0.0, 0.5, source_url="https://x.mx/s.pdf")
    assert [registry.register(hit(7)).n, registry.register(hit(9)).n, registry.register(hit(7)).n] == [1, 2, 1]
    assert registry.get(2).url == "https://x.mx/s.pdf#page=4" and registry.get(5) is None


# ---------- calcular_multa

from datetime import date
from decimal import Decimal

from app.core.config import Settings
from app.services.agent.operations import calculate_fine


def fine_context(db, today=date(2026, 10, 10), **settings):
    base = dict(uma_value=Decimal("117.31"), uma_valid_from=date(2026, 2, 1), uma_valid_until=date(2027, 1, 31))
    return AgentContext(db=db, user_id=None, embeddings=FixedQuery(vec(1)), user_message="cuánto es la multa",
                        settings=Settings(_env_file=None, **{**base, **settings}), today=today)


def test_fine_amounts_use_the_uma_and_round_half_up_to_cents(client):
    _, factory = client
    with factory() as db:
        result = calculate_fine(fine_context(db), 10, 15, 20)
        assert result["estado"] == "ok"
        assert result["uma"]["valor_pesos"] == "117.31" and result["uma"]["vigencia"] == "2026-02-01 a 2027-01-31"
        assert {k: v["pesos"] for k, v in result["montos"].items()} == {"minima": "1173.10", "media": "1759.65", "maxima": "2346.20"}
        assert {k: v["pesos"] for k, v in result["con_descuento_50"].items()} == {"minima": "586.55", "media": "879.83", "maxima": "1173.10"}
        assert "cero o una" in result["regla_sancion"] and "otra entidad federativa" in result["regla_sancion"]
        assert "30 días naturales" in result["descuento"] and "33, fracción II" in result["descuento"]
        assert "advertencia_uma" not in result
        # Plain numbers for the citizen: never scientific notation such as "1E+1".
        assert [v["veces_uma"] for v in result["montos"].values()] == ["10", "15", "20"]
        assert calculate_fine(fine_context(db), 2.5, 5, 7.5)["montos"]["minima"]["veces_uma"] == "2.5"


def test_a_fixed_fine_has_a_single_amount(client):
    _, factory = client
    with factory() as db:
        result = calculate_fine(fine_context(db), 300, None, None)
        assert list(result["montos"]) == ["unica"] and result["montos"]["unica"]["pesos"] == "35193.00"


def test_impossible_inputs_are_rejected_instead_of_computed(client):
    _, factory = client
    with factory() as db:
        for args in ((0, 5, 7), (-10, 15, 20), (20, 15, 10), (10, None, 20), (5000, 5000, 5000)):
            assert calculate_fine(fine_context(db), *args)["estado"] == "valores_invalidos", args


def test_an_expired_uma_is_flagged_not_silently_used(client):
    _, factory = client
    with factory() as db:
        result = calculate_fine(fine_context(db, today=date(2027, 2, 15)), 10, 15, 20)
        assert result["estado"] == "ok" and "puede estar desactualizada" in result["advertencia_uma"]
        before = calculate_fine(fine_context(db, today=date(2026, 1, 20)), 10, 15, 20)
        assert "advertencia_uma" in before


def test_the_rule_articles_are_registered_as_citable_fragments(client):
    _, factory = client
    with factory() as db:
        source = add_source(db, "reglamento-transito", "a")
        add_chunk(db, source, "62", "El infractor tendrá derecho a que se le descuente un 50% del monto", vec(1), page=70)
        add_chunk(db, source, "64", "Se impondrá la sanción mínima, cuando tenga cero o una sanción pendiente", vec(1), fraction="VII", page=73)
        db.commit()
        ctx = fine_context(db)
        result = calculate_fine(ctx, 10, 15, 20)
        assert sorted(f["articulo"] for f in result["fundamento"]) == ["62", "64"]
        assert {c.article for c in ctx.citations.all()} == {"62", "64"}


# ---------- guardas contra búsquedas repetidas

def test_a_near_duplicate_search_in_the_same_turn_is_not_run_again(client):
    _, factory = client
    with factory() as db:
        seed_laws(db)
        ctx = context(db, FixedQuery(vec(1, 0)))
        first = search_legislation(ctx, "obligación portar licencia conducir reglamento", ley="reglamento-transito")
        again = search_legislation(ctx, "portar licencia conducir obligación reglamento de tránsito", ley="reglamento-transito")
        assert first["estado"] == "ok"
        assert again["estado"] == "consulta_repetida" and "obtener_articulo" in again["mensaje"]
        different = search_legislation(ctx, "inmovilizador estacionado cajón", ley="reglamento-transito")
        assert different["estado"] == "ok"
        assert ctx.searches_run == 2  # the duplicate did not reach the database


def test_the_per_turn_search_cap_is_enforced_by_the_operation_itself(client):
    _, factory = client
    with factory() as db:
        seed_laws(db)
        ctx = context(db, FixedQuery(vec(1, 0)))
        topics = ["inmovilizador estacionado", "velocidad máxima vías", "licencia eléctricos", "placas matrícula", "multa descuento"]
        states = [search_legislation(ctx, topic)["estado"] for topic in topics]
        assert states[:3] == ["ok", "ok", "ok"] and set(states[3:]) == {"limite_de_busquedas"}


# ---------- expansión de fracciones hermanas

def test_when_two_fractions_of_one_article_match_the_sibling_fractions_come_along(client):
    _, factory = client
    with factory() as db:
        source = add_source(db, "reglamento-transito", "a")
        add_chunk(db, source, "44", "Conductores de transporte público deben portar licencia", vec(1, 0), fraction="II", page=56)
        add_chunk(db, source, "44", "Conductores de carga deben portar licencia", vec(1, 0.1), fraction="V", page=57)
        add_chunk(db, source, "44", "Conductores particulares: portar licencia vigente en formato físico o digital", vec(0, 1), fraction="I", page=56)
        add_chunk(db, source, "9", "Límites de velocidad", vec(0, 1), page=15)
        db.commit()
        ctx = context(db, FixedQuery(vec(1, 0)))
        result = search_legislation(ctx, "licencia conducir", ley="reglamento-transito")

        by_fraction = {(f["articulo"], f["fraccion"]): f["origen"] for f in result["fragmentos"]}
        assert by_fraction[("44", "II")] == "busqueda" and by_fraction[("44", "V")] == "busqueda"
        assert by_fraction[("44", "I")] == "mismo_articulo"  # the one the search alone had missed


def test_a_single_matching_fraction_does_not_pull_in_its_article(client):
    _, factory = client
    with factory() as db:
        source = add_source(db, "reglamento-transito", "a")
        add_chunk(db, source, "33", "Inmovilizador estacionados", vec(1, 0), fraction="II", page=35)
        add_chunk(db, source, "33", "Inmovilizador por artículo 30", vec(0, 0, 1), fraction="I", page=35)
        db.commit()
        result = search_legislation(context(db, FixedQuery(vec(1, 0))), "inmovilizador", ley="reglamento-transito")
        assert {f["origen"] for f in result["fragmentos"]} == {"busqueda"}


# ---------- extractos y detección de repetidas

def test_an_excerpt_is_centred_on_the_searched_word_and_much_shorter_than_the_text():
    from app.services.agent.operations import EXCERPT_CHARS, _excerpt

    padding = "texto de relleno sin relación " * 30
    text = padding + "b) debe portar licencia vigente en formato digital." + padding
    excerpt = _excerpt(text, "portar licencia")
    assert "portar licencia vigente" in excerpt and len(excerpt) <= EXCERPT_CHARS + 1
    assert _excerpt("sin coincidencias aquí", "zzzz")[:10] == "sin coinci"  # no keyword: the start of the text


def test_only_the_best_results_carry_full_text_and_the_rest_are_marked_as_excerpts(client):
    from app.services.agent.operations import FULL_FRAGMENTS

    _, factory = client
    with factory() as db:
        source = add_source(db, "reglamento-transito", "a")
        for i in range(FULL_FRAGMENTS + 3):
            add_chunk(db, source, str(100 + i), f"Artículo {100 + i}. regla sobre placas número {i} " * 5, vec(1, 0.01 * i), page=i + 1)
        db.commit()
        fragments = search_legislation(context(db, FixedQuery(vec(1, 0))), "placas", ley="reglamento-transito")["fragmentos"]
        assert [bool(f.get("extracto")) for f in fragments] == [False] * FULL_FRAGMENTS + [True] * 3


def test_a_longer_query_that_merely_contains_a_shorter_one_is_not_a_repeat(client):
    _, factory = client
    with factory() as db:
        seed_laws(db)
        ctx = context(db, FixedQuery(vec(1, 0)))
        assert search_legislation(ctx, "conducir licencia multa")["estado"] == "ok"
        longer = search_legislation(ctx, "conducir licencia multa documentos vigentes portar obligación boleta tránsito formato digital")
        assert longer["estado"] == "ok"


# ---------- truncado que conserva la sanción (va al final de la fracción)

def test_clipping_keeps_the_end_of_a_long_fragment_where_the_penalty_clause_sits():
    from app.services.agent.operations import _clip

    text = "regla " * 400 + "serán sancionados con una multa equivalente a 10, 15 o 20 veces la UMA."
    clipped = _clip(text, 1000)
    assert len(clipped) <= 1000 and clipped.startswith("regla") and "[…]" in clipped
    assert clipped.endswith("10, 15 o 20 veces la UMA.")
    assert _clip("texto corto", 1000) == "texto corto" and _clip("x", 0) == ""


def test_an_article_budget_goes_to_the_long_fractions_not_split_evenly(client):
    from app.services.agent.operations import ARTICLE_CHARS

    _, factory = client
    with factory() as db:
        source = add_source(db, "reglamento-transito", "a")
        add_chunk(db, source, "44", "Art. 44. I. " + "licencia particular " * 200 + "multa de 10, 15 o 20 veces la UMA.", vec(1), fraction="I")
        for fr in ("II", "III", "IV", "V"):
            add_chunk(db, source, "44", f"corta {fr}", vec(1), fraction=fr)
        db.commit()
        fragments = fetch_article(context(db), "reglamento-transito", "44")["fragmentos"]
        long_one = next(f for f in fragments if f["fraccion"] == "I")
        assert len(long_one["texto"]) > ARTICLE_CHARS // 5 and long_one["texto"].endswith("veces la UMA.")
        assert sum(len(f["texto"]) for f in fragments) <= ARTICLE_CHARS + 100
