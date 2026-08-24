from dataclasses import dataclass
from pathlib import Path

from app.core.config import Settings


class LegalAIUnavailable(RuntimeError):
    pass


@dataclass
class GeneratedAnswer:
    answer: str
    category: str
    citations: list[dict]


class LegalAIService:
    """Lazy, optional adapter around the existing Ollama/LangChain RAG workflow."""

    categories = {"multas", "procedimientos", "reglamentacion", "general"}

    def __init__(self, settings: Settings):
        self.settings = settings
        self._chain = None
        self._llm = None

    def _initialize(self) -> None:
        if self._chain:
            return
        if not self.settings.ai_enabled:
            raise LegalAIUnavailable("Legal AI is disabled")
        path = Path(self.settings.ai_index_path)
        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()
        if not path.exists():
            raise LegalAIUnavailable(f"Legal index is unavailable: {path}")
        if not self.settings.ai_allow_legacy_faiss_deserialization:
            raise LegalAIUnavailable("FAISS index loading is disabled until a trusted index is explicitly approved")
        try:
            from langchain.chains import RetrievalQA
            from langchain.prompts import PromptTemplate
            from langchain_community.vectorstores import FAISS
            from langchain_ollama import OllamaEmbeddings, OllamaLLM
        except ImportError as exc:
            # TODO: message is inaccurate — `langchain` (langchain.chains/langchain.prompts) is
            # imported above but not declared in the `ai` dependency group, so `uv sync --group ai`
            # will not actually fix this.
            raise LegalAIUnavailable("Optional AI dependencies are not installed; run uv sync --group ai") from exc
        embeddings = OllamaEmbeddings(model=self.settings.ai_embedding_model, base_url=self.settings.ai_ollama_base_url)
        # LangChain's current FAISS format contains pickle metadata; this is opt-in above.
        store = FAISS.load_local(str(path), embeddings, allow_dangerous_deserialization=True)
        self._llm = OllamaLLM(model=self.settings.ai_chat_model, base_url=self.settings.ai_ollama_base_url, temperature=0.3, timeout=300)
        prompt = PromptTemplate(template=("Responde solo con el contexto legal proporcionado. No inventes datos. " "Explica con claridad y cita los artículos relevantes.\n\nContexto: {context}\nPregunta: {question}\nRespuesta:"), input_variables=["context", "question"])
        self._chain = RetrievalQA.from_chain_type(self._llm, retriever=store.as_retriever(search_kwargs={"k": 3}), chain_type_kwargs={"prompt": prompt}, return_source_documents=True)

    def answer(self, question: str) -> GeneratedAnswer:
        self._initialize()
        result = self._chain.invoke({"query": question})
        category = self._classify(question)
        citations = [{"document": str(doc.metadata.get("source", "Fuente legal")), "page": doc.metadata.get("page")} for doc in result["source_documents"]]
        return GeneratedAnswer(answer=result["result"], category=category, citations=citations)

    def _classify(self, question: str) -> str:
        text = question.lower()
        if any(word in text for word in ("multa", "sanción", "infracción")):
            return "multas"
        if any(word in text for word in ("trámite", "impugnar", "procedimiento")):
            return "procedimientos"
        if any(word in text for word in ("ley", "reglamento", "artículo")):
            return "reglamentacion"
        return "general"
