from app.services.ai.llm_provider import LLMProvider


class ProgressEvaluator:
    """Stub for the future AI re-evaluation engine.

    Not implemented in this pass — see Section 2 of the build spec. Exists
    only so the shape can be imported/wired into routes ahead of time
    without committing to its behavior yet.
    """

    def __init__(self, llm: LLMProvider):
        self._llm = llm

    def evaluate(self, *args, **kwargs):
        raise NotImplementedError("ProgressEvaluator is not implemented in the MVP vertical slice")
