"""What each agent tool does, as plain functions over an `AgentContext`.

They return JSON-ready dicts with an `estado` the system prompt knows how to react to. Keeping them apart from the
`@tool` wrappers (tools.py) makes them testable without running an agent.
"""
import re
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select

from app.models.domain import AgentLookup, LegalChunk, OfficialSource
from app.services.agent.context import AgentContext
from app.services.agents_registry import EmptyAgentQuery, search_agents
from app.services.retrieval import SearchHit, get_article, search_many

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

LIST_LABELS = {
    "via_publica": "vía pública (equipos electrónicos portátiles)",
    "sistemas_tecnologicos": "sistemas tecnológicos (fotocívicas)",
}


def find_agent(ctx: AgentContext, query: str) -> dict:
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
            "persona no es policía. Recomienda: pedirle que se identifique con nombre y número de placa, no entregar "
            "documentos si no hay boleta, verificar en la SSC y, si hay abuso, denunciar ante Asuntos Internos de la SSC.",
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
    pages = str(hit.page_start) if hit.page_start == hit.page_end else f"{hit.page_start}-{hit.page_end}"
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
    return {"estado": "ok", "fragmentos": [_fragment(ctx, hit, budget) for hit, budget in zip(hits, budgets)]}


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
    """Pesos from "N veces la UMA". The model reads the multiples from the article; the arithmetic is done here."""
    values = [veces_min, veces_med, veces_max]
    given = [Decimal(str(v)) for v in values if v is not None]
    fixed = veces_med is None and veces_max is None
    ordered = all(a <= b for a, b in zip(given, given[1:]))
    if (
        veces_min is None or not (fixed or (veces_med is not None and veces_max is not None))
        or any(v <= 0 or v > MAX_VECES_UMA for v in given) or not ordered
    ):
        return {
            "estado": "valores_invalidos",
            "mensaje": "Usa los múltiplos de UMA que dice el artículo, de menor a mayor (p. ej. 10, 15 y 20), o uno solo "
            "si la multa es fija.",
        }

    settings, today = ctx.settings, ctx.current_date()
    uma = settings.uma_value
    labels = ["unica"] if fixed else ["minima", "media", "maxima"]
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
        "con_descuento_50": {
            label: {"pesos": str((amount / 2).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))} for label, amount in amounts.items()
        },
        "regla_sancion": SANCTION_RULE,
        "descuento": DISCOUNT_RULE,
        "nota_fotocivicas": PHOTO_FINE_NOTE,
    }
    if not (settings.uma_valid_from <= today <= settings.uma_valid_until):
        result["advertencia_uma"] = (
            f"El valor de la UMA usado ({uma}) rige del {settings.uma_valid_from} al {settings.uma_valid_until}; "
            "hoy puede estar desactualizada. Indica que los montos son aproximados y que se confirmen en el INEGI."
        )

    # Make the two rule articles citable so the answer can link them like any other fragment.
    rule_fragments = []
    for article, marker in (("62", "descuente un 50%"), ("64", "sanción mínima")):
        for hit in get_article(ctx.db, "reglamento-transito", article):
            if marker in " ".join(hit.text.split()):
                rule_fragments.append(_fragment(ctx, hit, 0) | {"texto": None})
                break
    if rule_fragments:
        result["fundamento"] = [
            {key: f[key] for key in ("cita", "articulo", "fraccion", "paginas")} for f in rule_fragments
        ]
    return result
