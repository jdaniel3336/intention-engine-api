from pydantic import BaseModel

from app.services.ai.llm_provider import LLMMessage, LLMProvider

SYSTEM_PROMPT = """You are the clarification interviewer for Intention Engine, an app that turns a \
vague intention (e.g. "I want to start a company") into a clear outcome and plan.

Ask only questions that materially improve the plan: what exactly the user is trying to \
accomplish, why, what success looks like, deadline, budget, existing resources, constraints, \
what's already been done. Ask ONE question at a time. Do not overwhelm the user. Once you have \
enough to draft a clear, measurable desired outcome, stop asking and summarize instead.

Keep your tone calm, direct, and encouraging — never corporate or robotic."""


class ClarifierTurn(BaseModel):
    ready_to_summarize: bool
    message: str
    summary: str | None = None


class IntentionClarifier:
    def __init__(self, llm: LLMProvider):
        self._llm = llm

    def next_turn(self, title: str, description: str | None, history: list[LLMMessage]) -> ClarifierTurn:
        intro = f'The user\'s intention: "{title}"'
        if description:
            intro += f"\nInitial description: {description}"

        messages = [LLMMessage(role="user", content=intro), *history]
        return self._llm.generate(messages, ClarifierTurn, system=SYSTEM_PROMPT)
