"""
============================================================
SYSC3010 L3-G6 — Pydantic v2 Models
One model per database table, used for FastAPI request/response
validation and serialisation.
============================================================
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# users
# ---------------------------------------------------------------------------

class UserBase(BaseModel):
    username: str
    role: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# node_status
# ---------------------------------------------------------------------------

class NodeStatusBase(BaseModel):
    node_id: str
    node_type: str
    ip_address: Optional[str] = None
    status: str
    last_heartbeat: datetime
    last_message: Optional[str] = None

class NodeStatusUpsert(NodeStatusBase):
    pass

class NodeStatus(NodeStatusBase):
    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# solve_sessions
# ---------------------------------------------------------------------------

class SolveSessionBase(BaseModel):
    user_id: Optional[int] = None
    session_name: Optional[str] = None
    selected_algorithm: str
    status: str
    notes: Optional[str] = None

class SolveSessionCreate(SolveSessionBase):
    pass

class SolveSession(SolveSessionBase):
    id: int
    started_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# cube_states
# ---------------------------------------------------------------------------

class CubeStateBase(BaseModel):
    session_id: int
    source: str
    state_string: str
    is_valid: bool
    confidence: Optional[float] = None

class CubeStateCreate(CubeStateBase):
    pass

class CubeState(CubeStateBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# scan_faces
# ---------------------------------------------------------------------------

class ScanFaceBase(BaseModel):
    session_id: int
    face_name: str
    face_string: str
    confidence: Optional[float] = None
    captured_by: Optional[str] = None

class ScanFaceCreate(ScanFaceBase):
    pass

class ScanFace(ScanFaceBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# solutions
# ---------------------------------------------------------------------------

class SolutionBase(BaseModel):
    session_id: int
    algorithm_used: str
    move_count: int
    solution_string: Optional[str] = None
    generated_by: Optional[str] = None

class SolutionCreate(SolutionBase):
    pass

class Solution(SolutionBase):
    id: int
    generated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# solution_steps
# ---------------------------------------------------------------------------

class SolutionStepBase(BaseModel):
    solution_id: int
    step_index: int
    face: str
    direction: str
    degrees: int

class SolutionStepCreate(SolutionStepBase):
    pass

class SolutionStep(SolutionStepBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# execution_runs
# ---------------------------------------------------------------------------

class ExecutionRunBase(BaseModel):
    session_id: int
    solution_id: int
    status: str
    motor_node_id: Optional[str] = None

class ExecutionRunCreate(ExecutionRunBase):
    pass

class ExecutionRun(ExecutionRunBase):
    id: int
    started_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# motor_execution_log
# ---------------------------------------------------------------------------

class MotorExecutionLogBase(BaseModel):
    run_id: int
    step_index: int
    commanded_face: str
    commanded_dir: str
    commanded_deg: int
    status: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None

class MotorExecutionLogCreate(MotorExecutionLogBase):
    pass

class MotorExecutionLog(MotorExecutionLogBase):
    id: int
    ts: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# verification_results
# ---------------------------------------------------------------------------

class VerificationResultBase(BaseModel):
    session_id: int
    run_id: Optional[int] = None
    verified: bool
    final_state_string: Optional[str] = None
    method: str
    notes: Optional[str] = None

class VerificationResultCreate(VerificationResultBase):
    pass

class VerificationResult(VerificationResultBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# system_logs
# ---------------------------------------------------------------------------

class SystemLogBase(BaseModel):
    session_id: Optional[int] = None
    node_id: Optional[str] = None
    level: str
    event_type: str
    message: str
    metadata: Optional[str] = None

class SystemLogCreate(SystemLogBase):
    pass

class SystemLog(SystemLogBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
