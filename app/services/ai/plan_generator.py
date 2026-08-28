from datetime import date

from pydantic import BaseModel

from app.services.ai.llm_provider import LLMMessage, LLMProvider

SYSTEM_PROMPT = """You are the plan generator for Intention Engine. Given a user's intention and \
a clarifying-conversation summary, produce a concrete, non-overwhelming execution plan: a \
measurable desired outcome, a small number of milestones in logical order, and a small number of \
concrete actions under each milestone. Assign each action a priority (1 = do first). Prefer a \
short, high-signal plan over an exhaustive task list."""


class GeneratedAction(BaseModel):
    title: str
    description: str | None = None
    priority: int
    due_date: date | None = None


class GeneratedMilestone(BaseModel):
    title: str
    description: str | None = None
    order: int
    target_date: date | None = None
    actions: list[GeneratedAction]


class GeneratedPlan(BaseModel):
    desired_outcome: str
    target_date: date | None = None
    milestones: list[GeneratedMilestone]


class PlanGenerator:
    def __init__(self, llm: LLMProvider):
        self._llm = llm

    def generate(self, title: str, description: str | None, conversation_summary: str) -> GeneratedPlan:
        content = (
            f'Intention: "{title}"\n'
            f"Description: {description or '(none)'}\n\n"
            f"Clarification summary:\n{conversation_summary}\n\n"
            "Generate the plan now."
        )
        messages = [LLMMessage(role="user", content=content)]
        return self._llm.generate(messages, GeneratedPlan, system=SYSTEM_PROMPT)
