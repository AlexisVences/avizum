from langchain_core.language_models.fake_chat_models import FakeListChatModel

from app.services.query_rewrite import REWRITE_PROMPT, rewrite_query


def test_rewrite_returns_one_clean_line_from_the_model_reply():
    llm = FakeListChatModel(responses=["  candado   inmovilizador\nretiro cuota  Reglamento de Tránsito "])
    assert rewrite_query(llm, "que hago si le pusieron la araña a mi coche?") == "candado inmovilizador retiro cuota Reglamento de Tránsito"


def test_prompt_forbids_inventing_articles_and_answering():
    assert "No respondas la pregunta" in REWRITE_PROMPT and "inventes números de artículo" in REWRITE_PROMPT
