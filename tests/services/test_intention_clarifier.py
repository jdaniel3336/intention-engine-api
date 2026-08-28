from app.services.ai.intention_clarifier import IntentionClarifier
from app.services.ai.llm_provider import LLMMessage
from tests.fakes import FakeLLMProvider


def test_asks_a_question_before_enough_info():
    clarifier = IntentionClarifier(FakeLLMProvider())
    turn = clarifier.next_turn("Start a company", None, [LLMMessage(role="user", content="I dunno yet")])
    assert turn.ready_to_summarize is False
    assert turn.message


def test_ready_to_summarize_after_enough_turns():
    clarifier = IntentionClarifier(FakeLLMProvider())
    history = [
        LLMMessage(role="user", content="I want to build a software company"),
        LLMMessage(role="assistant", content="What does success look like?"),
        LLMMessage(role="user", content="$10k MRR within a year"),
    ]
    turn = clarifier.next_turn("Start a company", None, history)
    assert turn.ready_to_summarize is True
    assert turn.summary
