########################################
# MOTOR CONTROL SUBSYSTEM - Main Entry 
# Eric McFetridge # 101310942
########################################

import asyncio
import os
import sys
from dotenv import load_dotenv
from .healthcheck import wait_for_hardware
from .server_bridge import sio, connect_to_server, manager
from .heartbeat import run_heartbeat
load_dotenv()

NODE_ID = os.getenv('NODE_ID', 'motor-node')

async def main():
    # Healthcheck
    if not await wait_for_hardware():
        print("ERROR: Could not verify Klipper hardware. Is the SKR v1.4 powered?")
        sys.exit(1)
    
    # Start Main Script
    print(f"Starting Node {NODE_ID}...")
    await asyncio.gather(
        connect_to_server(),
        run_heartbeat(sio, manager)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nNode shutting down.")