from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(title="MIG Sovereign AI Control Plane", version="0.1.0")


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TaskState(StrEnum):
    PENDING = "PENDING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    EXECUTED = "EXECUTED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class AgentCreate(BaseModel):
    legal_entity_id: UUID
    code: str = Field(pattern=r"^[A-Z0-9_\-]{3,64}$")
    name: str = Field(min_length=3, max_length=120)
    department: str = Field(min_length=2, max_length=80)
    allowed_tools: list[str] = Field(default_factory=list, max_length=50)
    max_risk: RiskLevel = RiskLevel.LOW


class Agent(AgentCreate):
    id: UUID
    enabled: bool = True
    created_at: datetime


class TaskCreate(BaseModel):
    legal_entity_id: UUID
    agent_id: UUID
    action: str = Field(min_length=3, max_length=120)
    payload: dict[str, Any] = Field(default_factory=dict)
    risk: RiskLevel = RiskLevel.LOW
    idempotency_key: str = Field(min_length=8, max_length=128)


class Task(TaskCreate):
    id: UUID
    state: TaskState
    requested_by: str
    approved_by: str | None = None
    created_at: datetime
    executed_at: datetime | None = None


class AuditEvent(BaseModel):
    id: UUID
    legal_entity_id: UUID
    event_type: str
    actor: str
    object_id: UUID
    occurred_at: datetime
    previous_hash: str
    event_hash: str
    details: dict[str, Any]


AGENTS: dict[UUID, Agent] = {}
TASKS: dict[UUID, Task] = {}
IDEMPOTENCY: dict[tuple[UUID, str], UUID] = {}
AUDIT: list[AuditEvent] = []


def now() -> datetime:
    return datetime.now(timezone.utc)


def append_audit(*, entity: UUID, event_type: str, actor: str, object_id: UUID, details: dict[str, Any]) -> None:
    previous_hash = AUDIT[-1].event_hash if AUDIT else "GENESIS"
    material = f"{previous_hash}|{entity}|{event_type}|{actor}|{object_id}|{details}|{now().isoformat()}"
    event = AuditEvent(
        id=uuid4(), legal_entity_id=entity, event_type=event_type, actor=actor,
        object_id=object_id, occurred_at=now(), previous_hash=previous_hash,
        event_hash=sha256(material.encode()).hexdigest(), details=details,
    )
    AUDIT.append(event)


def actor(x_actor_id: str | None) -> str:
    if not x_actor_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-Actor-Id")
    return x_actor_id


def requires_approval(risk: RiskLevel) -> bool:
    return risk in {RiskLevel.HIGH, RiskLevel.CRITICAL}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "mig-sovereign-ai"}


@app.post("/v1/agents", response_model=Agent, status_code=201)
def create_agent(body: AgentCreate, x_actor_id: str | None = Header(default=None)) -> Agent:
    who = actor(x_actor_id)
    if any(a.legal_entity_id == body.legal_entity_id and a.code == body.code for a in AGENTS.values()):
        raise HTTPException(status_code=409, detail="Agent code already exists for legal entity")
    item = Agent(id=uuid4(), created_at=now(), **body.model_dump())
    AGENTS[item.id] = item
    append_audit(entity=item.legal_entity_id, event_type="AGENT_CREATED", actor=who, object_id=item.id, details={"code": item.code})
    return item


@app.get("/v1/agents", response_model=list[Agent])
def list_agents(legal_entity_id: UUID | None = None) -> list[Agent]:
    values = list(AGENTS.values())
    return [a for a in values if legal_entity_id is None or a.legal_entity_id == legal_entity_id]


@app.post("/v1/tasks", response_model=Task, status_code=201)
def create_task(body: TaskCreate, x_actor_id: str | None = Header(default=None)) -> Task:
    who = actor(x_actor_id)
    agent_item = AGENTS.get(body.agent_id)
    if not agent_item or not agent_item.enabled:
        raise HTTPException(status_code=404, detail="Enabled agent not found")
    if agent_item.legal_entity_id != body.legal_entity_id:
        raise HTTPException(status_code=403, detail="Cross-entity task denied")
    key = (body.legal_entity_id, body.idempotency_key)
    if key in IDEMPOTENCY:
        return TASKS[IDEMPOTENCY[key]]
    state = TaskState.AWAITING_APPROVAL if requires_approval(body.risk) else TaskState.APPROVED
    item = Task(id=uuid4(), state=state, requested_by=who, created_at=now(), **body.model_dump())
    TASKS[item.id] = item
    IDEMPOTENCY[key] = item.id
    append_audit(entity=item.legal_entity_id, event_type="TASK_CREATED", actor=who, object_id=item.id, details={"action": item.action, "risk": item.risk})
    return item


@app.post("/v1/tasks/{task_id}/approve", response_model=Task)
def approve_task(task_id: UUID, x_actor_id: str | None = Header(default=None)) -> Task:
    who = actor(x_actor_id)
    item = TASKS.get(task_id)
    if not item:
        raise HTTPException(status_code=404, detail="Task not found")
    if item.requested_by == who:
        raise HTTPException(status_code=403, detail="Four-eyes control: requester cannot approve")
    if item.state != TaskState.AWAITING_APPROVAL:
        raise HTTPException(status_code=409, detail=f"Task is {item.state}")
    item.state = TaskState.APPROVED
    item.approved_by = who
    append_audit(entity=item.legal_entity_id, event_type="TASK_APPROVED", actor=who, object_id=item.id, details={})
    return item


@app.post("/v1/tasks/{task_id}/execute", response_model=Task)
def execute_task(task_id: UUID, x_actor_id: str | None = Header(default=None)) -> Task:
    who = actor(x_actor_id)
    item = TASKS.get(task_id)
    if not item:
        raise HTTPException(status_code=404, detail="Task not found")
    if item.state != TaskState.APPROVED:
        raise HTTPException(status_code=409, detail="Task is not approved")
    agent_item = AGENTS[item.agent_id]
    requested_tool = str(item.payload.get("tool", ""))
    if requested_tool and requested_tool not in agent_item.allowed_tools:
        raise HTTPException(status_code=403, detail="Tool is not allow-listed for agent")
    # Tool adapters are deliberately not invoked in Phase 1. Execution records the governed hand-off.
    item.state = TaskState.EXECUTED
    item.executed_at = now()
    append_audit(entity=item.legal_entity_id, event_type="TASK_EXECUTED", actor=who, object_id=item.id, details={"action": item.action})
    return item


@app.get("/v1/tasks/{task_id}", response_model=Task)
def get_task(task_id: UUID) -> Task:
    item = TASKS.get(task_id)
    if not item:
        raise HTTPException(status_code=404, detail="Task not found")
    return item


@app.get("/v1/audit-events", response_model=list[AuditEvent])
def audit_events(legal_entity_id: UUID | None = None) -> list[AuditEvent]:
    return [e for e in AUDIT if legal_entity_id is None or e.legal_entity_id == legal_entity_id]
