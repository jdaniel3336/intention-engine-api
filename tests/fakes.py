from typing import TypeVar

from pydantic import BaseModel

from app.services.ai.intention_clarifier import ClarifierTurn
from app.services.ai.llm_provider import LLMMessage, LLMProvider
from app.services.ai.plan_generator import GeneratedAction, GeneratedMilestone, GeneratedPlan

T = TypeVar("T", bound=BaseModel)


class FakeLLMProvider(LLMProvider):
    """Deterministic stand-in for a real provider, used across all tests.

    Ready-to-summarize triggers after 2 user turns so tests can drive the
    clarification loop without depending on real model behavior.
    """

    def generate(
        self,
        messages: list[LLMMessage],
        response_schema: type[T],
        system: str | None = None,
    ) -> T:
        if response_schema is ClarifierTurn:
            user_turns = [m for m in messages if m.role == "user"]
            # first item in `messages` is always the intro turn injected by
            # IntentionClarifier, so subtract it from the count of real turns
            real_user_turns = len(user_turns) - 1
            if real_user_turns >= 2:
                return ClarifierTurn(
                    ready_to_summarize=True,
                    message="Got it — here's what I understand.",
                    summary="Clarified intention summary based on the conversation so far.",
                )
            return ClarifierTurn(
                ready_to_summarize=False,
                message="What does success look like for this, and by when?",
            )

        if response_schema is GeneratedPlan:
            return GeneratedPlan(
                desired_outcome="A concrete, measurable outcome derived from the conversation.",
                target_date=None,
                milestones=[
                    GeneratedMilestone(
                        title="Milestone 1",
                        description="First milestone",
                        order=1,
                        target_date=None,
                        actions=[
                            GeneratedAction(title="First action", priority=1, due_date=None),
                            GeneratedAction(title="Second action", priority=2, due_date=None),
                        ],
                    ),
                    GeneratedMilestone(
                        title="Milestone 2",
                        description="Second milestone",
                        order=2,
                        target_date=None,
                        actions=[
                            GeneratedAction(title="Third action", priority=1, due_date=None),
                        ],
                    ),
                ],
            )

        raise AssertionError(f"FakeLLMProvider has no canned response for {response_schema}")
