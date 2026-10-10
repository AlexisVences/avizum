"""Turns a citizen's question into a search query in the vocabulary of the law.

Retrieval alone fails on colloquial wording ("corralón" for the depósito vehicular,
"mordida" for cohecho). The agent's search tools do this implicitly because the model writes the query; this module
makes the step explicit so it can be measured on its own (scripts.eval_retrieval --rewrite).
"""
from langchain_core.language_models import BaseChatModel

from app.core.config import Settings

REWRITE_PROMPT = (
    "Preparas búsquedas en la legislación de tránsito de la Ciudad de México (reglamentos, leyes, Código Fiscal, "
    "protocolos de actuación policial). Reescribe la pregunta de una persona como UNA consulta de búsqueda breve "
    "(máximo 40 palabras) con el vocabulario jurídico: nombra la figura legal (p. ej. 'depósito vehicular' en vez de "
    "'corralón', 'cohecho' en vez de 'mordida', 'infracción captada por sistemas tecnológicos' en vez de 'fotomulta', "
    "'recurso de inconformidad', 'juicio de nulidad ante el Tribunal de Justicia Administrativa'), la conducta y el "
    "documento o trámite. No respondas la pregunta ni inventes números de artículo. Devuelve solo la consulta."
)


def build_chat_model(settings: Settings, model: str | None = None) -> BaseChatModel:
    if settings.openai_api_key is None:
        raise RuntimeError("OPENAI_API_KEY is not set; add it to backend/.env")
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=model or settings.openai_chat_model, api_key=settings.openai_api_key, reasoning_effort="low", max_retries=2)


def _text(content: str | list) -> str:
    if isinstance(content, str):
        return content
    return "".join(block.get("text", "") if isinstance(block, dict) else str(block) for block in content)


def rewrite_query(llm: BaseChatModel, question: str) -> str:
    reply = llm.invoke([("system", REWRITE_PROMPT), ("human", question)])
    return " ".join(_text(reply.content).split())
