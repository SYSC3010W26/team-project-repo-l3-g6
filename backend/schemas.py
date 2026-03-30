"""
============================================================
SYSC3010 L3-G6 — Backend API Schemas (Pydantic v2)
Done By : Saim Hashmi

Lean request/response models for every REST endpoint.
These are API-contract models — separate from database/models.py per D-02.
Each model defines only the fields the endpoint needs, not the full DB row.
============================================================
"""
from typing import Optional
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

class JobStartRequest(BaseModel):
    algorithm: str = "CFOP"
    session_name: Optional[str] = None


class JobStartResponse(BaseModel):
    session_id: int


class JobStateResponse(BaseModel):
    session_id: int
    status: str
    started_at: str
    completed_at: Optional[str] = None
    selected_algorithm: str


class SolveSessionResponse(BaseModel):
    session_id: int
    status: str
    selected_algorithm: str
    session_name: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None


# ---------------------------------------------------------------------------
# Scan
# ---------------------------------------------------------------------------

class ScanSubmitRequest(BaseModel):
    session_id: int
    state_string: str
    is_valid: bool
    confidence: Optional[float] = None


class ScanSubmitResponse(BaseModel):
    cube_state_id: int


class ScanResultResponse(BaseModel):
    session_id: int
    state_string: str
    is_valid: bool
    confidence: Optional[float] = None
    created_at: str


# ---------------------------------------------------------------------------
# Solve
# ---------------------------------------------------------------------------

class SolveStartRequest(BaseModel):
    session_id: int


class SolveStartResponse(BaseModel):
    session_id: int
    status: str


class SolveSubmitRequest(BaseModel):
    session_id: int
    algorithm_used: str
    move_count: int
    solution_string: str


class SolveSubmitResponse(BaseModel):
    solution_id: int


class SolutionStepResponse(BaseModel):
    step_index: int
    move_notation: str


class SolveResultResponse(BaseModel):
    session_id: int
    solution_id: int
    algorithm_used: str
    move_count: int
    solution_string: Optional[str] = None
    generated_at: str
    steps: list[SolutionStepResponse] = []


# ---------------------------------------------------------------------------
# Execute
# ---------------------------------------------------------------------------

class ExecuteStartRequest(BaseModel):
    session_id: int
    solution_id: int
    motor_node_id: Optional[str] = None


class ExecuteStartResponse(BaseModel):
    run_id: int


class ExecuteProgressRequest(BaseModel):
    session_id: int
    run_id: int
    current_step: int
    total_steps: int
    move: str


class ExecuteCompleteRequest(BaseModel):
    session_id: int
    run_id: int
    status: str


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

class HeartbeatRequest(BaseModel):
    node_id: str
    node_type: str
    ip_address: Optional[str] = None
    status: str = "online"
    last_message: Optional[str] = None


class NodeStatusResponse(BaseModel):
    node_id: str
    node_type: str
    ip_address: Optional[str] = None
    is_online: bool
    last_heartbeat: str
    last_message: Optional[str] = None


# ---------------------------------------------------------------------------
# Logs
# ---------------------------------------------------------------------------

class LogEntryResponse(BaseModel):
    id: int
    session_id: Optional[int] = None
    node_id: Optional[str] = None
    severity: str           # renamed from 'level' to match frontend SystemLog.severity
    event_type: str
    message: str
    metadata: Optional[str] = None
    created_at: str


# ---------------------------------------------------------------------------
# Generic
# ---------------------------------------------------------------------------

class MessageResponse(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# Job State Machine
# ---------------------------------------------------------------------------

class JobTransitionRequest(BaseModel):
    to: str  # idle | scanning | solving | executing | done | error


class JobTransitionResponse(BaseModel):
    session_id: int
    previous_status: str
    new_status: str


# ---------------------------------------------------------------------------
# Control Flags
# ---------------------------------------------------------------------------

class ControlFlagRequest(BaseModel):
    action: str           # start | stop | reset | rescan
    issued_by: str = "gui"


class ControlFlagResponse(BaseModel):
    control_id: int
    session_id: int
    action: str
    issued_by: str
    issued_at: str
    status: str


class ControlAckRequest(BaseModel):
    control_id: int
