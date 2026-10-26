"""What each agent tool does, as plain functions over an `AgentContext`.

They return JSON-ready dicts with an `estado` the system prompt knows how to react to. Keeping them apart from the
`@tool` wrappers (tools.py) makes them testable without running an agent.
"""
import re
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select

from app.models.domain import AgentLookup, LegalChunk, OfficialSource
from app.services.agent.context import AgentContext
from app.services.agents_registry import PLATE_PATTERN, EmptyAgentQuery, normalize_name, normalize_plate, search_agents
from app.services.retrieval import SearchHit, get_article, search_many
from app.services.sanctions_lookup import verified_by_chunk

MIN_SIMILARITY = 0.25  # off-topic queries scored 0.22-0.24; relevant ones were >= 0.30 (see the spec, section 7)
MAX_FRAGMENTS = 14  # measured: the answer sat at rank 8-13 for natural queries; recall@20 was 0.96 vs 0.88 at 10
FULL_FRAGMENTS = 4  # best results with full text; the rest are ~450-char excerpts (about a third of the tokens)
EXCERPT_CHARS = 450
MAX_SEARCHES_PER_TURN = 3  # measured: without a cap the model once ran five near-identical searches (45k input tokens)
DUPLICATE_OVERLAP = 0.7  # Jaccard similarity of the words above which a query counts as a repeat
MAX_SIBLING_FRAGMENTS = 5  # extra fractions of articles that already matched twice
SIBLING_CHARS = 900
MAX_AGENT_RESULTS = 5
FRAGMENT_CHARS = 1500
ARTICLE_CHARS = 6000
MAX_SANCTION_ROWS = 30  # per tool result; a long article is read whole with obtener_articulo
SANCTION_CONDUCT_CHARS = 160
NO_DISCOUNT = {("30", "XXI"), ("33", "II")}  # Reglamento de Tránsito Art. 62: these fines are not discounted

LIST_LABELS = {
    "via_publica": "vía pública (equipos electrónicos portátiles)",
    "sistemas_tecnologicos": "sistemas tecnológicos (fotocívicas)",
}


# Words the model has searched as if they were a name ("placa", "agente"); the fuzzy match against a real surname turned
# one of them into a «verified» agent.
GENERIC_AGENT_WORDS = {"placa", "placas", "nombre", "agente", "agentes", "policia", "oficial", "transito", "numero", "del", "de", "la", "el", "un", "una"}


def _is_full_name(query: str) -> bool:
    """A person has at least a first name and a surname; one word, or only generic words, is not a name."""
    return len([w for w in normalize_name(query).split() if w not in GENERIC_AGENT_WORDS and len(w) > 1]) >= 2


def find_agent(ctx: AgentContext, query: str) -> dict:
    if not PLATE_PATTERN.fullmatch(normalize_plate(query)) and normalize_name(query) and not _is_full_name(query):
        return {
            "estado": "consulta_invalida",
            "mensaje": "No tengo un nombre completo ni una placa para buscar. Pide al usuario la placa (solo números) o el "
            "nombre completo del agente; no busques con una palabra suelta ni inventes el dato.",
        }
    try:
        search = search_agents(ctx.db, query)
    except EmptyAgentQuery:
        return {"estado": "consulta_invalida", "mensaje": "Pide al usuario una placa (solo números) o el nombre completo del agente."}

    if search.source is None:
        return {
            "estado": "registro_no_disponible",
            "mensaje": "El registro oficial de agentes no está disponible en este momento. NO afirmes que no aparece; "
            "explica que no se pudo consultar y remite al sitio oficial de la SSC.",
        }

    matches = search.matches[:MAX_AGENT_RESULTS]
    ctx.db.add(AgentLookup(user_id=ctx.user_id, agent_id=matches[0].agent.id if matches else None))
    ctx.db.flush()
    citation = ctx.citations.register_source(
        source_id=search.source.id, slug=search.source.slug, title=search.source.title, url=search.source.url
    )
    source = {
        "cita": citation.n,
        "titulo": search.source.title,
        "url": search.source.url,
        "fecha": search.source.last_reform_date.isoformat() if search.source.last_reform_date else None,
    }
    if not matches:
        return {
            "estado": "sin_coincidencias",
            "consulta": query,
            "mensaje": "No aparece en la lista vigente. Puede deberse a un dato mal capturado, así que no concluyas que la "
            "persona no es policía. Recomienda: pedirle que se identifique con nombre y número de placa; los documentos "
            "(licencia, tarjeta de circulación, póliza) solo se entregan para su revisión y el agente debe devolverlos "
            "(Reglamento de Tránsito, art. 59, fr. II, incisos e y h), así que no permitir que se los queden; el "
            "Reglamento prevé que un agente no autorizado pida el apoyo de uno autorizado (art. 59, fr. II, inciso b); "
            "verificar en la SSC y, si hay abuso, denunciar ante Asuntos Internos de la SSC.",
            "fuente": source,
        }
    return {
        "estado": "ok",
        "coincidencia_por": search.matched_by,
        "resultados": [
            {
                "placa": m.agent.plate,
                "nombre": m.agent.full_name,
                "tipo_autorizacion": m.agent.authorization_type.value,
                "lista": LIST_LABELS[m.agent.authorization_type.value],
                "corporacion": m.agent.corporation,
                "alcaldias": m.agent.alcaldias,
            }
            for m in matches
        ],
        "nota": "Solo quien aparece en la lista de vía pública está autorizado en el acuerdo para firmar boletas en la "
        "calle con equipo portátil; la lista de sistemas tecnológicos autoriza boletas emitidas mediante esos sistemas.",
        "fuente": source,
    }


def _valid_slugs(ctx: AgentContext) -> list[str]:
    return list(ctx.db.scalars(
        select(OfficialSource.slug)
        .join(LegalChunk, LegalChunk.source_id == OfficialSource.id)
        .where(OfficialSource.is_current)
        .distinct()
        .order_by(OfficialSource.slug)
    ))


def _clip(text: str, chars: int) -> str:
    """Fit `text` in `chars` keeping its beginning AND its end.

    In these laws the sanction ("serán sancionados con una multa de…") closes each fraction, so cutting only from the
    start silently dropped the penalty of every long fraction.
    """
    flat = " ".join(text.split())
    if len(flat) <= chars:
        return flat
    if chars <= 0:
        return ""
    marker = " […] "
    head = max(0, int(chars * 0.55))
    tail = max(0, chars - head - len(marker))
    return flat[:head] + marker + (flat[-tail:] if tail else "")


def _fragment(ctx: AgentContext, hit: SearchHit, chars: int) -> dict:
    citation = ctx.citations.register(hit)
    ctx.fragment_texts.append(" ".join(hit.text.split()))
    pages = "" if hit.page_start == 0 else str(hit.page_start) if hit.page_start == hit.page_end else f"{hit.page_start}-{hit.page_end}"
    return {
        "cita": citation.n,
        "ley": hit.source_slug,
        "titulo_ley": hit.source_title,
        "articulo": hit.article,
        "fraccion": hit.fraction,
        "paginas": pages,
        "texto": _clip(hit.text, chars),
    }


def _words(query: str) -> set[str]:
    return {word for word in re.findall(r"\w+", query.lower()) if len(word) > 3}


def _is_repeat(ctx: AgentContext, consulta: str) -> bool:
    new = _words(consulta)
    for previous in map(_words, ctx.searched):
        union = new | previous
        if union and len(new & previous) / len(union) >= DUPLICATE_OVERLAP:
            return True
    return False


def _excerpt(text: str, query: str) -> str:
    """About EXCERPT_CHARS of the text centred on the first word of the query that appears in it."""
    flat = " ".join(text.split())
    lowered = flat.lower()
    positions = [lowered.find(word) for word in _words(query) if lowered.find(word) >= 0]
    if not positions:
        return flat[:EXCERPT_CHARS]
    start = max(0, min(positions) - EXCERPT_CHARS // 4)
    return ("…" if start else "") + flat[start : start + EXCERPT_CHARS]


def _sibling_fragments(ctx: AgentContext, hits: list[SearchHit]) -> list[dict]:
    """Other fractions of any article that matched with two or more fractions.

    A search can return fractions II and V of an article and miss fraction I, which is the one that answers
    (measured: "¿me pueden multar por no traer licencia?" concluded "no hay fundamento" without Art. 44 fr. I).
    The model was told to read the whole article and did not reliably do it, so the tool brings the siblings itself.
    """
    seen = {hit.chunk_id for hit in hits}
    counts: dict[tuple[str, str], int] = {}
    for hit in hits:
        counts[(hit.source_slug, hit.article)] = counts.get((hit.source_slug, hit.article), 0) + 1
    extras: list[dict] = []
    for (slug, article), count in counts.items():
        if count < 2:
            continue
        for sibling in get_article(ctx.db, slug, article):
            if sibling.chunk_id in seen or len(extras) >= MAX_SIBLING_FRAGMENTS:
                continue
            seen.add(sibling.chunk_id)
            extras.append(_fragment(ctx, sibling, SIBLING_CHARS) | {"origen": "mismo_articulo"})
    return extras


def _whole_words(text: str, chars: int) -> str:
    """Whole words only: a cut in the middle of a word ("para in") reads as if the text said something else."""
    flat = " ".join(text.split())
    return flat if len(flat) <= chars else flat[:chars].rsplit(" ", 1)[0].rstrip(" ,;:") + " …"


def _levels(row) -> dict[str, Decimal]:
    values = [v for v in (row.uma_min, row.uma_mid, row.uma_max) if v is not None]
    if len(values) == 1:
        return {"unica": values[0]}
    labels = ["minima", "media", "maxima"] if row.uma_mid is not None else ["minima", "maxima"]
    return dict(zip(labels, values))


def _sanction_view(ctx: AgentContext, row, fragment_fraction: str | None) -> dict:
    """One verified conduct with its penalty already resolved, ready for the model to pick the matching row."""
    uma = ctx.settings.uma_value
    # No database id here: measured, the model cited a row id as if it were a fragment mark ([51], [52]).
    view: dict = {"conducta": _clip(row.conduct_text, SANCTION_CONDUCT_CHARS)}
    if row.fraction and row.fraction != fragment_fraction:
        view["fraccion"] = row.fraction
    if row.inciso:
        view["inciso"] = row.inciso
    if row.applies_to:
        view["aplica_a"] = row.applies_to
    levels = _levels(row)
    if levels:
        pesos = {name: _pesos(value, uma) for name, value in levels.items()}
        view["veces_uma"] = {name: f"{value.normalize():f}" for name, value in levels.items()}
        view["pesos"] = {name: str(amount) for name, amount in pesos.items()}
        ctx.served_uma_values.update(levels.values())
        ctx.served_uma_triples.add(tuple(v.normalize() for v in (row.uma_min, row.uma_mid, row.uma_max) if v is not None))
        ctx.served_amounts.update(pesos.values())
        if (row.article, row.fraction) in NO_DISCOUNT:
            view["sin_descuento"] = "esta sanción no tiene el 50% de pronto pago (Art. 62)"
        else:
            half = {name: (amount / 2).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) for name, amount in pesos.items()}
            view["pronto_pago_50"] = {name: str(amount) for name, amount in half.items()}
            ctx.served_amounts.update(half.values())
    if row.points_license is not None:
        view["puntos_licencia"] = row.points_license
    if row.points_plate is not None:
        view["puntos_matricula"] = row.points_plate
    if row.points_mode == "alternativos_por_captacion":
        view["puntos_nota"] = (
            "según cómo se capte la infracción: con un agente, los puntos van a la licencia; con un sistema tecnológico "
            "(fotomulta), a la matrícula. No se suman."
        )
    elif row.points_mode == "acumulativos":
        view["puntos_nota"] = "se aplican ambos: puntos a la licencia y a la matrícula"
    if row.other_consequences:
        view["otras_consecuencias"] = _clip(row.other_consequences, 220)
    if row.context_text:
        view["depende_de"] = _whole_words(row.context_text, 700)  # exemptions / the paragraph the clause points to
    return view


def _rule_citations(ctx: AgentContext) -> list[dict]:
    """Arts. 62 (discount) and 64 (minimum/medium/maximum) made citable like any fragment."""
    cited = []
    for article, marker in (("62", "descuente un 50%"), ("64", "sanción mínima")):
        for hit in get_article(ctx.db, "reglamento-transito", article):
            if marker in " ".join(hit.text.split()):
                f = _fragment(ctx, hit, 0)
                cited.append({key: f[key] for key in ("cita", "articulo", "fraccion", "paginas")})
                break
    return cited


def _attach_sanctions(ctx: AgentContext, result: dict) -> None:
    """Put the verified penalty rows next to the fragments they belong to (same tool call, no extra model round).

    A row is one conduct with the amount that applies to THAT conduct. Choosing a row from a short closed list replaces
    reading which inciso a clause covers out of prose, which is where amounts went wrong (seat belt, Art. 37 II vs III).
    """
    fragments = result.get("fragmentos") or []
    chunk_of: dict[int, int] = {}
    for fragment in fragments:
        citation = ctx.citations.get(fragment["cita"])
        if citation is not None and citation.chunk_id > 0:
            chunk_of[fragment["cita"]] = citation.chunk_id
    rows_by_chunk = verified_by_chunk(ctx.db, sorted(set(chunk_of.values())))
    attached = 0
    for fragment in fragments:
        rows = rows_by_chunk.get(chunk_of.get(fragment["cita"]), [])
        if not rows:
            continue
        room = MAX_SANCTION_ROWS - attached
        if room <= 0:
            result["nota_sanciones_truncadas"] = "Hay más sanciones: lee el artículo completo con obtener_articulo."
            break
        fragment["sanciones"] = [_sanction_view(ctx, row, fragment.get("fraccion")) for row in rows[:room]]
        leads = {row.lead_text for row in rows[:room]}
        if len(leads) == 1 and None not in leads:
            # The article's own wording tells a prohibition from a duty; said once per fragment, complete.
            fragment["encabezado"] = _whole_words(next(iter(leads)), 500)
        else:
            for view, row in zip(fragment["sanciones"], rows[:room]):
                if row.lead_text:
                    view["encabezado"] = _whole_words(row.lead_text, 500)
        attached += len(fragment["sanciones"])
    if not attached:
        return
    settings, today = ctx.settings, ctx.current_date()
    result["uma"] = {
        "valor_pesos": str(settings.uma_value),
        "vigencia": f"{settings.uma_valid_from.isoformat()} a {settings.uma_valid_until.isoformat()}",
    }
    if not (settings.uma_valid_from <= today <= settings.uma_valid_until):
        result["advertencia_uma"] = (
            f"El valor de la UMA usado ({settings.uma_value}) rige del {settings.uma_valid_from} al "
            f"{settings.uma_valid_until}; hoy puede estar desactualizada. Indica que los montos son aproximados."
        )
    result["nota_sanciones"] = (
        "Cada fila de 'sanciones' es UNA conducta con la sanción que le aplica, ya verificada: elige la fila cuya "
        "'conducta' coincide con la de la persona (misma fracción e inciso) y usa sus montos tal cual. No mezcles "
        "montos de otra fila o fracción aunque compartan la letra del inciso. Si ninguna fila coincide, no des monto."
    )
    result["regla_sancion"] = SANCTION_RULE
    result["descuento"] = DISCOUNT_RULE
    result["fundamento_reglas"] = _rule_citations(ctx)


def search_legislation(ctx: AgentContext, consulta: str, ley: str | None = None) -> dict:
    valid = _valid_slugs(ctx)
    if ley is not None and ley not in valid:
        return {"estado": "ley_desconocida", "leyes_validas": valid}
    if ctx.searches_run >= MAX_SEARCHES_PER_TURN:
        return {
            "estado": "limite_de_busquedas",
            "mensaje": "Ya hiciste el máximo de búsquedas permitidas en este turno. Responde con lo que tienes y, si "
            "no hay fundamento suficiente, dilo; o lee un artículo concreto con obtener_articulo.",
        }
    if _is_repeat(ctx, consulta):
        return {
            "estado": "consulta_repetida",
            "mensaje": "Esta consulta es casi igual a una anterior de este turno. Cambia de enfoque (otro término "
            "jurídico u otra ley), lee un artículo con obtener_articulo o responde con lo que ya tienes.",
        }
    ctx.searched.append(consulta)
    # Two phrasings fused: the model's legal-vocabulary query and the user's own words (measured: 0.72 -> 0.80 recall@5).
    hits = search_many(
        ctx.db, [consulta, ctx.user_message], ctx.embeddings, source_slugs=[ley] if ley else None, k=MAX_FRAGMENTS
    )
    relevant = [hit for hit in hits if hit.similarity is not None and hit.similarity >= MIN_SIMILARITY]
    if not relevant:
        return {
            "estado": "sin_resultados_relevantes",
            "mensaje": "No se encontró fundamento en las fuentes oficiales indexadas. No respondas con conocimiento "
            "propio; di que no hay fundamento y remite a la autoridad.",
        }
    fragments = []
    for rank, hit in enumerate(relevant):
        fragment = _fragment(ctx, hit, FRAGMENT_CHARS) | {"origen": "busqueda"}
        if rank >= FULL_FRAGMENTS:
            fragment["texto"] = _excerpt(hit.text, f"{consulta} {ctx.user_message}")
            fragment["extracto"] = True
        fragments.append(fragment)
    fragments += _sibling_fragments(ctx, relevant)
    result = {"estado": "ok", "fragmentos": fragments}
    _attach_sanctions(ctx, result)
    if any(hit.fraction for hit in relevant):
        result["nota"] = (
            "Varios resultados son fracciones de un artículo. Si el artículo enumera casos por tipo de conductor, vehículo "
            "o situación, léelo completo con obtener_articulo antes de concluir que algo no está regulado: la fracción "
            "que buscas puede no haber salido en esta búsqueda."
        )
    return result


def fetch_article(ctx: AgentContext, ley: str, articulo: str) -> dict:
    valid = _valid_slugs(ctx)
    if ley not in valid:
        return {"estado": "ley_desconocida", "leyes_validas": valid}
    hits = get_article(ctx.db, ley, articulo)
    if not hits:
        return {"estado": "no_encontrado", "mensaje": f"El artículo {articulo} no está en las fuentes indexadas de {ley}."}
    # Budget in proportion to length: a long fraction (and its penalty clause) must not be cut like a one-liner.
    lengths = [len(" ".join(hit.text.split())) for hit in hits]
    total = sum(lengths) or 1
    budgets = [lengths[i] if total <= ARTICLE_CHARS else max(300, int(ARTICLE_CHARS * lengths[i] / total)) for i in range(len(hits))]
    result = {"estado": "ok", "fragmentos": [_fragment(ctx, hit, budget) for hit, budget in zip(hits, budgets)]}
    _attach_sanctions(ctx, result)
    return result


MAX_VECES_UMA = 1000  # no traffic fine in the sources comes close; guards against a misread number

SANCTION_RULE = (
    "El monto que se impone lo determina automáticamente el Sistema Integral de Administración de Infracciones, no el "
    "agente: sanción mínima con cero o una sanción pendiente; media con dos o tres pendientes; máxima con cuatro o más "
    "pendientes o si el vehículo tiene placas de otra entidad federativa o país (Reglamento de Tránsito, Art. 64)."
)
DISCOUNT_RULE = (
    "Se descuenta 50% si se paga dentro de los 30 días naturales siguientes a la notificación de la boleta, salvo las "
    "sanciones de los artículos 30, fracción XXI, y 33, fracción II (Reglamento de Tránsito, Art. 62)."
)
PHOTO_FINE_NOTE = (
    "Si la infracción la captó un sistema tecnológico (fotocívica), la sanción puede ser amonestación, curso o trabajo "
    "comunitario según los puntos de la matrícula; siempre es multa en carriles confinados, personas morales, "
    "transporte público, de carga, taxis y placas de otra entidad o país (Art. 64)."
)


def _pesos(veces: Decimal, uma: Decimal) -> Decimal:
    return (veces * uma).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_fine(ctx: AgentContext, veces_min: float, veces_med: float | None = None, veces_max: float | None = None) -> dict:
    """Pesos from "N veces la UMA". The model reads the multiples from the article; the arithmetic is done here.

    Three shapes: one fixed amount (only `veces_min`), three levels minimum/medium/maximum (Reglamento de Tránsito),
    or a RANGE "de X a Y" (`veces_min` and `veces_max`, no medium): a range has two ends, and a made-up middle is not
    in the law."""
    values = [veces_min, veces_med, veces_max]
    given = [Decimal(str(v)) for v in values if v is not None]
    fixed = veces_med is None and veces_max is None
    ranged = veces_med is None and veces_max is not None
    ordered = all(a <= b for a, b in zip(given, given[1:]))
    if (
        veces_min is None or not (fixed or ranged or (veces_med is not None and veces_max is not None))
        or any(v <= 0 or v > MAX_VECES_UMA for v in given) or not ordered
    ):
        return {
            "estado": "valores_invalidos",
            "mensaje": "Usa los múltiplos de UMA que dice el artículo, de menor a mayor: tres (p. ej. 10, 15 y 20), solo el "
            "mínimo y el máximo si el artículo da un rango 'de X a Y', o uno solo si la multa es fija.",
        }

    settings, today = ctx.settings, ctx.current_date()
    uma = settings.uma_value
    labels = ["unica"] if fixed else ["minima", "maxima"] if ranged else ["minima", "media", "maxima"]
    amounts = {label: _pesos(Decimal(str(v)), uma) for label, v in zip(labels, given)}
    result: dict = {
        "estado": "ok",
        "uma": {
            "valor_pesos": str(uma),
            "vigencia": f"{settings.uma_valid_from.isoformat()} a {settings.uma_valid_until.isoformat()}",
            "fuente": settings.uma_source,
        },
        "montos": {
            label: {"veces_uma": f"{Decimal(str(v)).normalize():f}", "pesos": str(amounts[label])}
            for label, v in zip(labels, given)
        },
    }
    if not ranged:
        result["con_descuento_50"] = {
            label: {"pesos": str((amount / 2).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))} for label, amount in amounts.items()
        }
    if ranged:
        result["nota_rango"] = (
            "El artículo da un RANGO: la autoridad fija el monto dentro de él. Da los dos extremos y no inventes un monto "
            "medio. Las reglas de sanción mínima/media/máxima y el descuento del 50% son del Reglamento de Tránsito y no "
            "se aplican a este rango salvo que el artículo lo diga."
        )
    else:
        result.update({"regla_sancion": SANCTION_RULE, "descuento": DISCOUNT_RULE, "nota_fotocivicas": PHOTO_FINE_NOTE})
    if not (settings.uma_valid_from <= today <= settings.uma_valid_until):
        result["advertencia_uma"] = (
            f"El valor de la UMA usado ({uma}) rige del {settings.uma_valid_from} al {settings.uma_valid_until}; "
            "hoy puede estar desactualizada. Indica que los montos son aproximados y que se confirmen en el INEGI."
        )

    ctx.served_uma_values.update(Decimal(str(v)) for v in given)
    ctx.served_uma_triples.add(tuple(Decimal(str(v)).normalize() for v in given))
    ctx.served_amounts.update(amounts.values())
    if not ranged:
        ctx.served_amounts.update(
            (amount / 2).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) for amount in amounts.values()
        )
    # Make the two rule articles citable so the answer can link them like any other fragment.
    rule_fragments = _rule_citations(ctx)
    if rule_fragments:
        result["fundamento"] = rule_fragments
    return result
