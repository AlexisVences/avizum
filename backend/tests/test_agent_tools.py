import json

from langchain.agents import create_agent
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, ToolMessage

from app.services.agent.context import AgentContext
from app.services.agent.tools import TOOLS, buscar_agente, buscar_legislacion, calcular_multa, obtener_articulo
from tests.factories import add_agent, add_agents_source
from tests.test_retrieval import FixedQuery, add_chunk, add_source, vec


class ScriptedModel(GenericFakeChatModel):
    """A chat model that replays prepared replies; create_agent only needs bind_tools to hand itself back."""

    def bind_tools(self, tools, **kwargs):
        return self


def call(name: str, args: dict, call_id: str = "c1") -> AIMessage:
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": call_id, "type": "tool_call"}])


def test_the_model_only_sees_its_own_arguments_never_the_injected_runtime():
    for tool in TOOLS:
        assert "runtime" not in tool.args, tool.name
    assert set(buscar_legislacion.args) == {"consulta", "ley"}
    assert set(buscar_agente.args) == {"placa_o_nombre"}
    assert set(obtener_articulo.args) == {"ley", "articulo"}
    assert set(calcular_multa.args) == {"veces_uma_minima", "veces_uma_media", "veces_uma_maxima"}


def test_descriptions_say_when_to_use_each_tool():
    assert "no la uses para preguntas sobre reglas" in buscar_agente.description.lower()
    assert "toda afirmación legal" in buscar_legislacion.description.lower()
    assert "nunca hagas esa aritmética" in calcular_multa.description.lower()


def test_a_real_langchain_agent_runs_the_tools_with_injected_context_and_numbers_the_citations(client):
    _, factory = client
    with factory() as db:
        source = add_source(db, "reglamento-transito", "a")
        add_chunk(db, source, "33", "Inmovilizador en vehículos estacionados", vec(1, 0), fraction="II", page=35)
        add_agent(db, add_agents_source(db), "1163184", "BAUTISTA DONALDO")
        db.commit()

        ctx = AgentContext(db=db, user_id=None, embeddings=FixedQuery(vec(1, 0)), user_message="me pusieron la araña")
        model = ScriptedModel(messages=iter([
            call("buscar_legislacion", {"consulta": "candado inmovilizador", "ley": "reglamento-transito"}),
            call("buscar_agente", {"placa_o_nombre": "1163184"}, "c2"),
            AIMessage(content="Se inmoviliza en estos casos [1]."),
        ]))
        agent = create_agent(model, tools=TOOLS, context_schema=AgentContext)
        result = agent.invoke({"messages": [{"role": "user", "content": "me pusieron la araña"}]}, context=ctx)

        tool_messages = [m for m in result["messages"] if isinstance(m, ToolMessage)]
        search = json.loads(tool_messages[0].content)
        assert search["estado"] == "ok" and search["fragmentos"][0]["cita"] == 1
        assert json.loads(tool_messages[1].content)["resultados"][0]["placa"] == "1163184"
        assert ctx.citations.get(1).article == "33"  # the registry the tool filled is the one we passed in
        assert result["messages"][-1].content == "Se inmoviliza en estos casos [1]."
