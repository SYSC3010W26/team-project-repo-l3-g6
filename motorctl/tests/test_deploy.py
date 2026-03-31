"""
MOTOR CONTROL SUBSYSTEM - Deployment Verification Suite

This test suite is designed to be run directly on the Raspberry Pi to verify that
the motorctl subsystem is correctly configured and can communicate with the 
Klipper/Moonraker hardware.

Prerequisites:
1. Klipper/Moonraker must be running on the Pi (default port 7125).
2. Stepper motor drivers (SKR v1.4) should be powered.

How to run:
    pytest tests/test_deploy.py -v -s
"""

import pytest
import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from server_bridge import MotorController, MotorState
from healthcheck import check_klipper_ready

@pytest.mark.asyncio
async def test_hardware_connection():
    """
    Step 1: Hardware Connectivity Check
    Verifies that the Moonraker API is reachable and reporting a 'ready' state.
    This ensures the USB connection to the SKR board and the firmware are functional.
    """
    is_ready = await check_klipper_ready()
    assert is_ready, "Hardware (Klipper) is not in 'ready' state. Check SKR power."

@pytest.mark.asyncio
async def test_full_solve_flow():
    """
    Step 2: Full Solve Cycle Simulation
    Emulates the behavior of the main backend server via the Socket.IO bridge logic.
    
    Flow:
    1. Transition to WAITING_FOR_LIST.
    2. Load a variety of Singmaster notation moves (Standard, Double, Prime).
    3. Execute the moves (This will trigger REAL motor movement).
    4. Verify the controller resets to a clean state after completion.
    """
    logs = []
    states = []
    
    # Mock callbacks to capture subsystem output for verification
    async def mock_log(msg): logs.append(msg)
    async def mock_state(s): states.append(s)

    controller = MotorController(
        "pi-test-node", 
        on_state_change=mock_state, 
        on_log=mock_log
    )

    # 1. Setup
    await controller.transition(MotorState.WAITING_FOR_LIST)
    
    # 2. Load moves (Variety check)
    move_sequence = "U R L F B B' F' L' R' U' U2 U2 R2 R2 L2 L2 F2 F2 B2 B2"
    await controller.handle_load_moves(move_sequence)
    assert controller.state == MotorState.WAITING_FOR_START
    assert controller.move_buffer == move_sequence

    # 3. Execute - Note: This sends G-Code to the hardware
    print(f"\n[Test] Executing moves: {move_sequence}.")
    await controller.handle_start_solve()
    
    # 4. Verification of state reset
    assert controller.state == MotorState.WAITING_FOR_LIST
    assert controller.move_buffer == ""
    assert "executing" in states

@pytest.mark.asyncio
async def test_invalid_move_resiliency():
    """
    Step 3: Error Handling & Resiliency
    Ensures that malformed move strings or invalid notation do not cause the 
    state machine to hang. The system should attempt to process what it can 
    and gracefully return to a waiting state.
    """
    controller = MotorController("pi-test-node")
    await controller.transition(MotorState.WAITING_FOR_LIST)
    
    # Load invalid moves mixed with garbage data
    await controller.handle_load_moves("INVALID_MOVE 1234 %%%")
    
    # The subsystem should handle the error and reset to ready
    await controller.handle_start_solve()
    assert controller.state == MotorState.WAITING_FOR_LIST
