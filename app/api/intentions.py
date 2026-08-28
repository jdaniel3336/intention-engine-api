import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.action import Action, ActionStatus
from app.models.conversation_message import ConversationMessage, MessageRole
from app.models.intention import Intention, IntentionStatus
from app.models.milestone import Milestone
from app.models.user import User
from app.schemas.action import ActionRead
from app.schemas.conversation_message import MessageCreate, MessageRead, MessageTurnResponse
from app.schemas.intention import IntentionCreate, IntentionRead, IntentionUpdate
from app.services.ai.intention_clarifier import IntentionClarifier
from app.services.ai.llm_provider import LLMMessage, LLMProvider, get_llm_provider
from app.services.ai.plan_generator import PlanGenerator

router = APIRouter(prefix="/intentions", tags=["intentions"])


def get_owned_intention(intention_id: uuid.UUID, db: Session, current_user: User) -> Intention:
    intention = db.get(Intention, intention_id)
    if intention is None or intention.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intention not found")
    return intention


@router.post("", response_model=IntentionRead, status_code=status.HTTP_201_CREATED)
def create_intention(
    payload: IntentionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Intention:
    intention = Intention(
        user_id=current_user.id,
        title=payload.title,
        description=payload.description,
        status=IntentionStatus.CLARIFYING,
    )
    db.add(intention)
    db.commit()
    db.refresh(intention)
    return intention


@router.get("", response_model=list[IntentionRead])
def list_intentions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Intention]:
    return (
        db.query(Intention)
        .filter(Intention.user_id == current_user.id)
        .order_by(Intention.created_at.desc())
        .all()
    )


@router.get("/{intention_id}", response_model=IntentionRead)
def get_intention(
    intention_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Intention:
    return get_owned_intention(intention_id, db, current_user)


@router.patch("/{intention_id}", response_model=IntentionRead)
def update_intention(
    intention_id: uuid.UUID,
    payload: IntentionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Intention:
    intention = get_owned_intention(intention_id, db, current_user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(intention, field, value)
    db.commit()
    db.refresh(intention)
    return intention


@router.post("/{intention_id}/messages", response_model=MessageTurnResponse)
def post_message(
    intention_id: uuid.UUID,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    llm: LLMProvider = Depends(get_llm_provider),
) -> MessageTurnResponse:
    intention = get_owned_intention(intention_id, db, current_user)

    user_message = ConversationMessage(
        intention_id=intention.id, role=MessageRole.USER, content=payload.content
    )
    db.add(user_message)
    db.commit()

    history = [
        LLMMessage(role=m.role.value, content=m.content)
        for m in db.query(ConversationMessage)
        .filter(ConversationMessage.intention_id == intention.id)
        .order_by(ConversationMessage.created_at)
        .all()
    ]

    clarifier = IntentionClarifier(llm)
    turn = clarifier.next_turn(intention.title, intention.description, history)

    assistant_message = ConversationMessage(
        intention_id=intention.id, role=MessageRole.ASSISTANT, content=turn.message
    )
    db.add(assistant_message)
    db.commit()

    return MessageTurnResponse(
        assistant_message=turn.message,
        ready_to_summarize=turn.ready_to_summarize,
        summary=turn.summary,
    )


@router.get("/{intention_id}/messages", response_model=list[MessageRead])
def list_messages(
    intention_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ConversationMessage]:
    intention = get_owned_intention(intention_id, db, current_user)
    return (
        db.query(ConversationMessage)
        .filter(ConversationMessage.intention_id == intention.id)
        .order_by(ConversationMessage.created_at)
        .all()
    )


@router.post("/{intention_id}/generate-plan", response_model=IntentionRead)
def generate_plan(
    intention_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    llm: LLMProvider = Depends(get_llm_provider),
) -> Intention:
    intention = get_owned_intention(intention_id, db, current_user)

    messages = (
        db.query(ConversationMessage)
        .filter(ConversationMessage.intention_id == intention.id)
        .order_by(ConversationMessage.created_at)
        .all()
    )
    if not messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot generate a plan before the clarification conversation has started",
        )

    transcript = "\n".join(f"{m.role.value}: {m.content}" for m in messages)

    generator = PlanGenerator(llm)
    plan = generator.generate(intention.title, intention.description, transcript)

    intention.desired_outcome = plan.desired_outcome
    if plan.target_date:
        intention.target_date = plan.target_date
    intention.status = IntentionStatus.ACTIVE

    for milestone_data in plan.milestones:
        milestone = Milestone(
            intention_id=intention.id,
            title=milestone_data.title,
            description=milestone_data.description,
            order=milestone_data.order,
            target_date=milestone_data.target_date,
        )
        db.add(milestone)
        db.flush()

        for action_data in milestone_data.actions:
            db.add(
                Action(
                    milestone_id=milestone.id,
                    intention_id=intention.id,
                    title=action_data.title,
                    description=action_data.description,
                    priority=action_data.priority,
                    due_date=action_data.due_date,
                    status=ActionStatus.PENDING,
                )
            )

    db.commit()
    db.refresh(intention)
    return intention


@router.get("/{intention_id}/next-action", response_model=ActionRead | None)
def get_next_action(
    intention_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Action | None:
    intention = get_owned_intention(intention_id, db, current_user)
    return (
        db.query(Action)
        .filter(Action.intention_id == intention.id, Action.status == ActionStatus.PENDING)
        .order_by(Action.priority, Action.created_at)
        .first()
    )
