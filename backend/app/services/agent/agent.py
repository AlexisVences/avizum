"""Builds the LangChain agent and runs one turn of it (non-streaming; the chat service streams, see step 12)."""
import json
from collections.abc import Iterator
from dataclasses import dataclass, field

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware, ToolCallLimitMiddleware, wrap_model_call
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, SystemMessage, ToolMessage

from app.core.config import Settings
from app.services.agent.citations import resolve_citations
from app.services.agent.context import AgentContext
from app.services.agent.prompt import SYSTEM_PROMPT
from app.services.agent.tools import TOOLS

LIMIT_ANSWER = (
    "No pude completar la consulta con las fuentes disponibles en este momento. "
    "Intenta reformular tu pregunta de forma más concreta."
)


@dataclass
class AgentRun:
    answer: str
    tool_calls: list[dict]  # [{"name", "args", "estado"}] in the order they ran: the turn's trace
    citations: list[dict]  # only the citations the answer actually uses, ready for JSON and the interface
    input_tokens: int
    output_tokens: int
    model: str
    cached_input_tokens: int = 0  # part of input_tokens that OpenAI billed at the cached rate
    limit_reached: bool = False
    anomalies: list[dict] = field(default_factory=list)  # invalid markers, answers with tools but no citations


def build_chat_model(settings: Settings) -> BaseChatModel:
    if settings.openai_api_key is None:
        raise RuntimeError("OPENAI_API_KEY is not set; add it to backend/.env")
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=settings.openai_chat_model,
        api_key=settings.openai_api_key,
        reasoning_effort="low",
        max_tokens=settings.chat_max_output_tokens,  # sent as max_completion_tokens; includes reasoning tokens
        max_retries=2,
        timeout=60,
    )


LAST_CALL_NUDGE = (
    "Esta es tu última oportunidad: ya no puedes usar herramientas. Responde ahora con lo que obtuviste. Si no hay "
    "fundamento suficiente en esos resultados, dilo con claridad y remite a la autoridad; no inventes."
)


def _answer_on_last_call(max_model_calls: int):
    """On the last allowed model call, remove the tools so the turn ends with an answer, not a silent cut-off.

    Without it, a model that keeps searching used up its calls and the user got "no pude completar" even though the
    tools had already returned what was needed (measured on the licence question: 2 of 3 runs).
    """

    @wrap_model_call
    def answer_now(request, handler):
        calls_this_turn = 0
        for message in reversed(request.messages):  # earlier turns of the history are not part of this budget
            if isinstance(message, HumanMessage):
                break
            if isinstance(message, AIMessage):
                calls_this_turn += 1
        if calls_this_turn >= max_model_calls - 1:
            nudge = f"{request.system_message.content}\n\n{LAST_CALL_NUDGE}" if request.system_message else LAST_CALL_NUDGE
            request = request.override(tools=[], system_message=SystemMessage(content=nudge))
        return handler(request)

    return answer_now


def build_agent(settings: Settings, model: BaseChatModel | None = None):
    return create_agent(
        model or build_chat_model(settings),
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
        context_schema=AgentContext,
        middleware=[
            _answer_on_last_call(settings.chat_max_agent_steps),
            # Hard ceilings on a turn: the model stops looping, and parallel tool calls cannot explode either.
            ModelCallLimitMiddleware(run_limit=settings.chat_max_agent_steps, exit_behavior="end"),
            ToolCallLimitMiddleware(run_limit=settings.chat_max_agent_steps * 2, exit_behavior="continue"),
        ],
        name="avizum-asistente",
    )


def _text(content: str | list) -> str:
    if isinstance(content, str):
        return content
    return "".join(block.get("text", "") if isinstance(block, dict) else str(block) for block in content)


def _estado(message: ToolMessage) -> str | None:
    try:
        data = json.loads(_text(message.content))
        return data.get("estado") if isinstance(data, dict) else None
    except (json.JSONDecodeError, TypeError):
        return None


def _input_messages(user_message: str, history: list[tuple[str, str]], settings: Settings) -> list[dict]:
    """`history` is [(role, text)] oldest first; only the last `chat_context_messages` reach the model."""
    recent = history[-settings.chat_context_messages :] if settings.chat_context_messages else []
    return [*({"role": role, "content": content} for role, content in recent), {"role": "user", "content": user_message}]


def _summarize(new_messages: list, ctx: AgentContext, settings: Settings) -> AgentRun:
    """Everything the agent produced this turn -> the answer, the trace, the citations and the usage."""
    ai_messages = [m for m in new_messages if isinstance(m, AIMessage)]
    tool_rounds = [m for m in ai_messages if m.tool_calls]
    states = {m.tool_call_id: _estado(m) for m in new_messages if isinstance(m, ToolMessage)}
    trace = [
        {"name": call["name"], "args": call["args"], "estado": states.get(call["id"])}
        for message in tool_rounds
        for call in message.tool_calls
    ]
    usage = [m.usage_metadata or {} for m in ai_messages]
    # Every model call was a tool round: the model never got to answer and the middleware cut the turn off.
    limit_reached = len(tool_rounds) >= settings.chat_max_agent_steps
    answer = LIMIT_ANSWER if limit_reached else _text(ai_messages[-1].content).strip() if ai_messages else ""

    resolved = resolve_citations(answer, ctx.citations) if not limit_reached else None
    return AgentRun(
        answer=resolved.text if resolved else answer,
        tool_calls=trace,
        citations=resolved.citations if resolved else [],
        anomalies=resolved.anomalies if resolved else [],
        input_tokens=sum(u.get("input_tokens", 0) for u in usage),
        output_tokens=sum(u.get("output_tokens", 0) for u in usage),
        cached_input_tokens=sum((u.get("input_token_details") or {}).get("cache_read", 0) for u in usage),
        model=settings.openai_chat_model,
        limit_reached=limit_reached,
    )


def run_agent(
    agent, ctx: AgentContext, user_message: str, history: list[tuple[str, str]], settings: Settings
) -> AgentRun:
    messages = _input_messages(user_message, history, settings)
    result = agent.invoke({"messages": messages}, context=ctx)
    return _summarize(result["messages"][len(messages) :], ctx, settings)


def stream_agent(
    agent, ctx: AgentContext, user_message: str, history: list[tuple[str, str]], settings: Settings
) -> Iterator[tuple[str, object]]:
    """Same turn as `run_agent`, but yields events as they happen: ("tool_start" | "tool_end" | "token", dict) and,
    last, ("run", AgentRun). Text tokens are raw: invalid citation markers are cleaned only in the final answer."""
    messages = _input_messages(user_message, history, settings)
    produced: list = []
    for chunk in agent.stream({"messages": messages}, context=ctx, stream_mode=["messages", "updates"], version="v2"):
        kind, data = chunk["type"], chunk["data"]
        if kind == "messages":
            token, metadata = data
            if isinstance(token, ToolMessage):
                yield "tool_end", {"name": token.name, "ok": token.status != "error"}
            elif isinstance(token, AIMessageChunk) and metadata.get("langgraph_node") == "model":
                text = _text(token.content)
                if text:
                    yield "token", {"text": text}
        elif kind == "updates":
            for update in data.values():
                for message in (update.get("messages", []) if isinstance(update, dict) else []):
                    produced.append(message)
                    if isinstance(message, AIMessage) and message.tool_calls:
                        for call in message.tool_calls:
                            yield "tool_start", {"name": call["name"], "args": call["args"]}
    yield "run", _summarize(produced, ctx, settings)
