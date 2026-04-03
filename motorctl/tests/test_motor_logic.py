""" Tests for motor control logic and state management. """
import pytest
from unittest.mock import AsyncMock, patch
from motorctl.src.server_bridge import MotorController, MotorState

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.mark.anyio
async def test_state_transitions_flow():
    # Create controller with mocked callbacks
    state_callback = AsyncMock()
    controller = MotorController("test-node", on_state_change=state_callback)
    
    # Initial State
    assert controller.state == MotorState.STARTUP
    
    # Move to waiting for list
    await controller.transition(MotorState.WAITING_FOR_LIST)
    state_callback.assert_called_with("waiting_for_list")
    
    # Load moves
    await controller.handle_load_moves("U R L")
    assert controller.state == MotorState.WAITING_FOR_START
    assert controller.move_buffer == "U R L"

@pytest.mark.anyio
async def test_solve_execution_cycle():
    complete_callback = AsyncMock()
    controller = MotorController("test-node", on_complete=complete_callback)
    
    # Set up ready state
    controller.state = MotorState.WAITING_FOR_START
    controller.move_buffer = "U R"
    
    # Mock the hardware call
    with patch('motorctl.src.server_bridge.execute_move_sequence', new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = True
        
        await controller.handle_start_solve()
        
        # Verify hardware was called with buffered moves
        mock_exec.assert_called_once_with("U R")
        # Verify completion callback
        complete_callback.assert_called_with("success")
        # Verify state reset
        assert controller.state == MotorState.WAITING_FOR_LIST
        assert controller.move_buffer == ""