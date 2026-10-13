"""A chat model for tests that streams like a real one: text arrives word by word and a tool call arrives as
tool-call chunks. (LangChain's GenericFakeChatModel cannot stream a reply that has no text.)"""
import json

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult


class FakeStreaming(BaseChatModel):
    script: list  # AIMessage replies, consumed in order; endless scripts are fine
    cursor: int = 0
    fail_after_words: int | None = None  # raise in the middle of a text reply

    @property
    def _llm_type(self) -> str:
        return "fake-streaming"

    def bind_tools(self, tools, **kwargs):
        return self

    def _next(self) -> AIMessage:
        message = self.script[self.cursor % len(self.script)]
        self.cursor += 1
        return message

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        return ChatResult(generations=[ChatGeneration(message=self._next())])

    def _stream(self, messages, stop=None, run_manager=None, **kwargs):
        message = self._next()
        if message.tool_calls:
            for index, call in enumerate(message.tool_calls):
                yield ChatGenerationChunk(message=AIMessageChunk(content="", tool_call_chunks=[
                    {"name": call["name"], "args": json.dumps(call["args"]), "id": call["id"], "index": index}]))
        else:
            for count, word in enumerate(message.content.split(" ")):
                if self.fail_after_words is not None and count >= self.fail_after_words:
                    raise RuntimeError("connection reset by peer sk-SECRET-123")
                yield ChatGenerationChunk(message=AIMessageChunk(content=word + " "))
        yield ChatGenerationChunk(
            message=AIMessageChunk(content="", usage_metadata={"input_tokens": 100, "output_tokens": 20, "total_tokens": 120}),
            generation_info={"finish_reason": "stop"},
        )


def tool_call(name: str, args: dict, call_id: str = "c1") -> AIMessage:
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": call_id, "type": "tool_call"}])
