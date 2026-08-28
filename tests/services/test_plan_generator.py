from app.services.ai.plan_generator import PlanGenerator
from tests.fakes import FakeLLMProvider


def test_generates_milestones_and_actions():
    generator = PlanGenerator(FakeLLMProvider())
    plan = generator.generate("Start a company", "A software company", "User wants $10k MRR in a year")

    assert plan.desired_outcome
    assert len(plan.milestones) >= 1
    assert all(m.actions for m in plan.milestones)
    first_action = plan.milestones[0].actions[0]
    assert first_action.priority == 1
