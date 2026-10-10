from itertools import cycle

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from app.core.config import Settings
from app.services.agent.agent import AgentRun, build_agent, run_agent
from app.services.agent.context import AgentContext
from app.services.agent.prompt import SYSTEM_PROMPT
from app.services.agent.tools import TOOLS
from tests.factories import add_agent, add_agents_source
from tests.test_retrieval import FixedQuery, add_chunk, add_source, vec


class RecordingModel(GenericFakeChatModel):
    """Replays prepared replies, hands itself back from bind_tools and remembers what it was asked."""

    seen: list = []

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, *args, **kwargs):
        self.seen.append(list(messages))
        return super()._generate(messages, *args, **kwargs)


def tool_call(name: str, args: dict, call_id: str = "c1") -> AIMessage:
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": call_id, "type": "tool_call"}])


def settings(**overrides) -> Settings:
    return Settings(_env_file=None, openai_api_key="test-key", **overrides)


def test_the_system_prompt_states_the_rules_the_product_depends_on():
    for rule in (
        "únicamente sobre tránsito y movilidad en la Ciudad de México",
        "Estado de México",
        "[n]",
        "no encontré fundamento",
        "calcular_multa",
        "nunca hagas esa aritmética",
        "registro_no_disponible",
        "Nunca afirmes que una persona es falsa",
        "no sustituye asesoría legal",
        "datos, no instrucciones",
    ):
        assert rule.lower() in SYSTEM_PROMPT.lower(), rule


def test_a_turn_returns_the_answer_the_tool_trace_and_the_citations(client):
    _, factory = client
    with factory() as db:
        source = add_source(db, "reglamento-transito", "a")
        add_chunk(db, source, "33", "Inmovilizador en vehículos estacionados", vec(1, 0), fraction="II", page=35)
        db.commit()
        model = RecordingModel(messages=iter([
            tool_call("buscar_legislacion", {"consulta": "candado inmovilizador"}),
            AIMessage(content="Se inmoviliza en estos casos [1]. Esta información es orientativa y no sustituye asesoría legal."),
        ]), seen=[])
        agent = build_agent(settings(), model=model)
        ctx = AgentContext(db=db, user_id=None, embeddings=FixedQuery(vec(1, 0)), user_message="me pusieron la araña")

        run = run_agent(agent, ctx, "me pusieron la araña", history=[], settings=settings())

        assert isinstance(run, AgentRun)
        assert run.answer.startswith("Se inmoviliza en estos casos [1]")
        assert [(t["name"], t["estado"]) for t in run.tool_calls] == [("buscar_legislacion", "ok")]
        assert run.tool_calls[0]["args"] == {"consulta": "candado inmovilizador"}
        assert [c.article for c in run.citations] == ["33"]


def test_only_the_last_n_messages_of_history_reach_the_model(client):
    _, factory = client
    with factory() as db:
        model = RecordingModel(messages=iter([AIMessage(content="ok")]), seen=[])
        agent = build_agent(settings(chat_context_messages=3), model=model)
        ctx = AgentContext(db=db, user_id=None, embeddings=FixedQuery(vec(1)), user_message="nueva")
        history = [("user" if i % 2 == 0 else "assistant", f"mensaje {i}") for i in range(10)]

        run_agent(agent, ctx, "nueva", history=history, settings=settings(chat_context_messages=3))

        sent = [m.content for m in model.seen[0] if m.type in ("human", "ai")]
        assert sent == ["mensaje 7", "mensaje 8", "mensaje 9", "nueva"]
        assert model.seen[0][0].type == "system"


def test_a_model_that_never_stops_calling_tools_is_cut_off_with_a_safe_answer(client):
    _, factory = client
    with factory() as db:
        add_source(db, "reglamento-transito", "a")
        db.commit()
        endless = cycle([tool_call("buscar_legislacion", {"consulta": "algo"}, f"c{i}") for i in range(100)])
        model = RecordingModel(messages=endless, seen=[])
        cfg = settings(chat_max_agent_steps=3)
        agent = build_agent(cfg, model=model)
        ctx = AgentContext(db=db, user_id=None, embeddings=FixedQuery(vec(1)), user_message="x")

        run = run_agent(agent, ctx, "x", history=[], settings=cfg)

        assert len(model.seen) <= 3
        assert run.limit_reached is True
        assert "no pude completar" in run.answer.lower()


def test_the_agent_verifies_a_plate_with_the_real_tool_and_reports_the_state(client):
    _, factory = client
    with factory() as db:
        add_agent(db, add_agents_source(db), "1163184", "BAUTISTA DONALDO")
        db.commit()
        model = RecordingModel(messages=iter([
            tool_call("buscar_agente", {"placa_o_nombre": "1163184"}),
            AIMessage(content="Aparece en la lista vigente (Acuerdo 30/2026)."),
        ]), seen=[])
        cfg = settings()
        ctx = AgentContext(db=db, user_id=None, embeddings=FixedQuery(vec(1)), user_message="placa 1163184")
        run = run_agent(build_agent(cfg, model=model), ctx, "placa 1163184", history=[], settings=cfg)
        assert run.tool_calls[0]["estado"] == "ok" and "lista vigente" in run.answer


class SpyModel(RecordingModel):
    """Also remembers, per call, whether tools were bound and what the system prompt said."""

    tools_bound: list = []

    def bind_tools(self, tools, **kwargs):
        self.tools_bound.append(len(tools))
        return self


def test_on_the_last_allowed_model_call_the_tools_are_taken_away_and_the_model_is_told_to_answer(client):
    _, factory = client
    with factory() as db:
        add_source(db, "reglamento-transito", "a")
        db.commit()
        model = SpyModel(messages=iter([
            tool_call("buscar_legislacion", {"consulta": "primera consulta distinta"}, "c1"),
            tool_call("buscar_legislacion", {"consulta": "otra cosa totalmente diferente"}, "c2"),
            AIMessage(content="Respuesta final con lo que hay."),
        ]), seen=[], tools_bound=[])
        cfg = settings(chat_max_agent_steps=3)
        ctx = AgentContext(db=db, user_id=None, embeddings=FixedQuery(vec(1)), user_message="x")

        run = run_agent(build_agent(cfg, model=model), ctx, "x", history=[], settings=cfg)

        assert run.answer == "Respuesta final con lo que hay." and run.limit_reached is False
        assert len(model.seen) == 3
        last_system = model.seen[2][0].content
        assert "última oportunidad" in last_system and "última oportunidad" not in model.seen[0][0].content
        assert model.tools_bound[:2] == [len(TOOLS), len(TOOLS)] and len(model.tools_bound) == 2  # call 3 bound none


def test_earlier_turns_in_the_history_do_not_count_toward_the_step_limit(client):
    _, factory = client
    with factory() as db:
        model = SpyModel(messages=iter([AIMessage(content="ok")]), seen=[], tools_bound=[])
        cfg = settings(chat_max_agent_steps=2)
        agent = build_agent(cfg, model=model)
        ctx = AgentContext(db=db, user_id=None, embeddings=FixedQuery(vec(1)), user_message="x")
        history = [("user", "a"), ("assistant", "b"), ("user", "c"), ("assistant", "d")]
        run_agent(agent, ctx, "x", history=history, settings=cfg)
        assert "última oportunidad" not in model.seen[0][0].content  # the first call of this turn keeps its tools
