########################################
# MOTOR CONTROL SUBSYSTEM - Heartbeat
# Eric McFetridge # 101310942
########################################

import os
import asyncio

NODE_ID = os.getenv("NODE_ID", "motor-node")
INTERVAL = 5

async def run_heartbeat(sio_client, controller):
    while True:
        if sio_client.connected:
            await sio_client.emit('heartbeat', {
                'node_id': NODE_ID,
                'status': 'online',
                'current_state': controller.state.value
            })
        await asyncio.sleep(INTERVAL)