############################################
# MOTOR CONTROL SUBSYSTEM - Motor Actuator
# Eric McFetridge SYSC3010:L3G6
############################################

import os
import socketio
from enum import Enum
from dotenv import load_dotenv
from actuator import execute_move_sequence

load_dotenv()
NODE_ID = os.getenv("NODE_ID")
sio = socketio.AsyncClient()

class MotorState(Enum):
    STARTUP = "startup"
    WAITING_FOR_LIST = "waiting_for_list"
    WAITING_FOR_START = "waiting_for_start"
    EXECUTING = "executing"

class StateManager:
    def __init__(self):
        self.state = MotorState.STARTUP
        self.move_buffer = []

    async def transition(self, new_state):
        print(f"[State Transition] {new_state.value.upper()}")
        self.state = new_state
        await sio.emit('node_state_update', {'node_id': NODE_ID, 'state': self.state.value})

manager = StateManager()

@sio.on('load_moves')
async def on_load(data):
    # Only accept moves if waiting
    if manager.state == MotorState.WAITING_FOR_LIST:
        manager.move_buffer = data.get('moves', [])
        await manager.transition(MotorState.WAITING_FOR_START)

@sio.on('start_solve')
async def on_start(data):
    # Only start if have a list
    if manager.state == MotorState.WAITING_FOR_START:
        await manager.transition(MotorState.EXECUTING)
        
        success = await execute_move_sequence(manager.move_buffer)
        
        await sio.emit('execution_complete', {
            'node_id': NODE_ID, 
            'success': success,
            'move_count': len(manager.move_buffer)
        })
        
        manager.move_buffer = []
        await manager.transition(MotorState.WAITING_FOR_LIST)

async def connect_to_server():
    await sio.connect(os.getenv("SERVER_URL"))
    await manager.transition(MotorState.WAITING_FOR_LIST)
    await sio.wait()