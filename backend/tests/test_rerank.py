from langchain_core.language_models.fake_chat_models import FakeListChatModel

from app.services.rerank import RERANK_PROMPT, rerank
from app.services.retrieval import SearchHit


def hit(chunk_id: int, article: str, text: str = "texto") -> SearchHit:
    return SearchHit(chunk_id, "reglamento-transito", "Reglamento", article, None, f"Reglamento › Art. {article}", text, 1, 1, 0.0, 0.5)


HITS = [hit(1, "10"), hit(2, "20"), hit(3, "30"), hit(4, "40")]


def test_chosen_candidates_go_first_in_the_models_order_and_the_rest_keep_their_order():
    llm = FakeListChatModel(responses=["3, 1"])
    assert [h.chunk_id for h in rerank(llm, "pregunta", HITS)] == [3, 1, 2, 4]


def test_numbers_that_do_not_exist_or_repeat_are_ignored():
    llm = FakeListChatModel(responses=["Los mejores son: 9, 2, 2, 0, 4."])
    assert [h.chunk_id for h in rerank(llm, "pregunta", HITS)] == [2, 4, 1, 3]


def test_an_unusable_reply_leaves_the_original_order_untouched():
    llm = FakeListChatModel(responses=["no sé"])
    assert [h.chunk_id for h in rerank(llm, "pregunta", HITS)] == [1, 2, 3, 4]
    assert rerank(llm, "pregunta", []) == []


def test_prompt_tells_the_model_to_judge_only_from_the_candidates():
    assert "solo con base en los candidatos" in RERANK_PROMPT


class Boom(FakeListChatModel):
    def invoke(self, *args, **kwargs):
        raise RuntimeError("OpenAI is down")


def test_if_the_model_call_fails_retrieval_still_returns_the_rrf_order():
    assert [h.chunk_id for h in rerank(Boom(responses=["x"]), "pregunta", HITS)] == [1, 2, 3, 4]
