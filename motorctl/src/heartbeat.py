########################################
# MOTOR CONTROL SUBSYSTEM - Heartbeat
# Eric McFetridge SYSC3010:L3G6
########################################

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
NODE_ID = os.getenv("NODE_ID")
INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", 5))

async def run_heartbeat(sio_client, state_manager):
    while True:
        if sio_client.connected:
            await sio_client.emit('heartbeat', {
                'node_id': NODE_ID,
                'status': 'online',
                'current_state': state_manager.state.value
            })
        await asyncio.sleep(INTERVAL)