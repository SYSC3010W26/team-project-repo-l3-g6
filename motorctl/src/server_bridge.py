###########################################
# MOTOR CONTROL SUBSYSTEM - Server Bridge
# Eric McFetridge # 101310942
###########################################

import os
import asyncio
import socketio
from enum import Enum
from .actuator import execute_move_sequence

class MotorState(Enum):
    STARTUP = "startup"
    WAITING_FOR_LIST = "waiting_for_list"
    WAITING_FOR_START = "waiting_for_start"
    EXECUTING = "executing"

NODE_ID = os.getenv("NODE_ID", "motor-node")
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:5000")
sio = socketio.AsyncClient()

class MotorController:
    def __init__(self, node_id, on_state_change=None, on_log=None, on_complete=None):
        self.node_id = node_id
        self.state = MotorState.STARTUP
        self.move_buffer = ""
        self.on_state_change = on_state_change
        self.on_log = on_log
        self.on_complete = on_complete

    async def transition(self, new_state):
        print(f"[{self.node_id}] {self.state.value} -> {new_state.value}")
        self.state = new_state
        if self.on_state_change:
            await self.on_state_change(self.state.value)

    async def handle_load_moves(self, moves_str: str):
        """Logic to buffer moves. Exposed for backend wrappers."""
        if self.state == MotorState.WAITING_FOR_LIST:
            self.move_buffer = moves_str
            await self.transition(MotorState.WAITING_FOR_START)
            if self.on_log:
                await self.on_log("Moves buffered.")

    async def handle_start_solve(self):
        """Logic to trigger motor execution. Exposed for backend wrappers."""
        if self.state == MotorState.WAITING_FOR_START:
            await self.transition(MotorState.EXECUTING)
            success = await execute_move_sequence(self.move_buffer)
            
            if self.on_complete:
                await self.on_complete('success' if success else 'failed')
            
            self.move_buffer = ""
            await self.transition(MotorState.WAITING_FOR_LIST)

async def safe_emit(event, data):
    """Helper to emit events only when connected to prevent errors."""
    if sio.connected:
        try:
            await sio.emit(event, data)
        except Exception as e:
            print(f"[Bridge] Failed to emit {event}: {e}")

# Setup global controller instance with SIO callbacks
manager = MotorController(
    node_id=NODE_ID,
    on_state_change=lambda s: safe_emit('state_change', {'node_id': NODE_ID, 'state': s}),
    on_log=lambda m: safe_emit('log', {'node_id': NODE_ID, 'msg': m}),
    on_complete=lambda res: safe_emit('complete', {'node_id': NODE_ID, 'status': res})
)

@sio.on('load_moves')
async def on_load(data):
    await manager.handle_load_moves(data.get('moves', ""))

@sio.on('start_solve')
async def on_start(data):
    await manager.handle_start_solve()

async def connect_to_server():
    """Connects to server with a retry loop to allow standalone hardware testing."""
    while True:
        try:
            if not sio.connected:
                await sio.connect(SERVER_URL)
                await manager.transition(MotorState.WAITING_FOR_LIST)
            await sio.wait()
        except Exception as e:
            print(f"[Bridge] Connection to {SERVER_URL} failed: {e}. Retrying in 5s...")
            await asyncio.sleep(5)