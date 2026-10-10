"""The tools the model can call. Thin wrappers: the logic lives in operations.py.

Two things are worth knowing about how LangChain turns these into what the model sees:
- The model gets the tool's name, its docstring and the JSON schema of `args_schema`. That text IS the interface:
  a vague docstring produces wrong calls, so each one says when to use the tool and when not to.
- A parameter annotated `ToolRuntime[...]` is injected by LangChain at call time and never appears in the schema, so
  the model cannot supply (or forge) the database session or the user.
"""
import json

from langchain.tools import ToolRuntime, tool
from pydantic import BaseModel, Field

from app.services.agent import operations
from app.services.agent.context import AgentContext


def _json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False)


class BuscarAgenteInput(BaseModel):
    placa_o_nombre: str = Field(
        min_length=2, max_length=100,
        description="Número de placa del agente (solo dígitos) o su nombre completo, tal como lo dio el usuario.",
    )


class BuscarLegislacionInput(BaseModel):
    consulta: str = Field(
        min_length=3, max_length=300,
        description="Consulta de búsqueda en vocabulario jurídico (p. ej. 'candado inmovilizador' en vez de jerga). "
        "Incluye la conducta, el documento o el trámite. No inventes números de artículo.",
    )
    ley: str | None = Field(
        default=None,
        description="Opcional y casi siempre conviene dejarlo vacío: limita la búsqueda a una fuente por su slug, p. ej. "
        "'reglamento-transito'. Filtrar puede excluir la ley donde está la otra parte de la respuesta.",
    )


class ObtenerArticuloInput(BaseModel):
    ley: str = Field(description="Slug de la fuente, p. ej. 'reglamento-transito'.")
    articulo: str = Field(description="Número del artículo, p. ej. '30' o '30 Bis'.")


class CalcularMultaInput(BaseModel):
    veces_uma_minima: float = Field(
        gt=0, description="Múltiplo mínimo de UMA que dice el artículo (en 'multa de 10, 15 o 20 veces la UMA' es 10).",
    )
    veces_uma_media: float | None = Field(
        default=None, gt=0, description="Múltiplo medio (en el ejemplo, 15). Omítelo si la multa es fija.",
    )
    veces_uma_maxima: float | None = Field(
        default=None, gt=0, description="Múltiplo máximo (en el ejemplo, 20). Omítelo si la multa es fija.",
    )


@tool(args_schema=BuscarAgenteInput)
def buscar_agente(placa_o_nombre: str, runtime: ToolRuntime[AgentContext]) -> str:
    """Verifica si una persona policial aparece en la lista oficial VIGENTE de personal autorizado para infraccionar
    en la Ciudad de México (Acuerdo 30/2026 de la SSC). Úsala cuando el usuario quiera saber si un agente es legítimo
    o está facultado para multar. No la uses para preguntas sobre reglas, multas o procedimientos."""
    return _json(operations.find_agent(runtime.context, placa_o_nombre))


@tool(args_schema=BuscarLegislacionInput)
def buscar_legislacion(consulta: str, ley: str | None = None, *, runtime: ToolRuntime[AgentContext]) -> str:
    """Busca fragmentos de la legislación vigente de la CDMX sobre tránsito (Reglamento de Tránsito, Ley de Movilidad,
    Cultura Cívica, Código Fiscal, recursos para impugnar, protocolos de actuación policial). Devuelve hasta 6
    fragmentos con un número de cita [n], artículo, fracción y páginas. Úsala para cualquier pregunta sobre qué está
    prohibido, cuánto se multa, qué procedimiento sigue la autoridad o cómo impugnar. Toda afirmación legal de tu
    respuesta debe salir de estos fragmentos."""
    return _json(operations.search_legislation(runtime.context, consulta, ley))


@tool(args_schema=ObtenerArticuloInput)
def obtener_articulo(ley: str, articulo: str, *, runtime: ToolRuntime[AgentContext]) -> str:
    """Devuelve el texto completo de UN artículo (todas sus fracciones) de una fuente. Úsala para leer un artículo
    que ya conoces por número, por ejemplo cuando un fragmento remite a otro ('artículo 64')."""
    return _json(operations.fetch_article(runtime.context, ley, articulo))


@tool(args_schema=CalcularMultaInput)
def calcular_multa(
    veces_uma_minima: float, veces_uma_media: float | None = None, veces_uma_maxima: float | None = None,
    *, runtime: ToolRuntime[AgentContext],
) -> str:
    """Convierte 'N veces la UMA' a pesos con la UMA vigente y explica cuál sanción (mínima, media o máxima) se aplica
    y el descuento del 50% por pronto pago. Úsala SIEMPRE que des un monto en pesos: nunca hagas esa aritmética tú.
    Primero busca el artículo con buscar_legislacion y toma de ahí los múltiplos de UMA."""
    return _json(operations.calculate_fine(runtime.context, veces_uma_minima, veces_uma_media, veces_uma_maxima))


TOOLS = [buscar_agente, buscar_legislacion, obtener_articulo, calcular_multa]
