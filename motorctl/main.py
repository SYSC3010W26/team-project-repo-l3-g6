########################################
# MOTOR CONTROL SUBSYSTEM - Main Entry 
# Eric McFetridge SYSC3010:L3G6
########################################
import asyncio
import sys
import os
from dotenv import load_dotenv
from src.healthcheck import wait_for_hardware
from src.server_bridge import connect_to_server, run_heartbeat

load_dotenv()

async def main():
    if not await wait_for_hardware():
        print("ERROR: Could not verify Klipper hardware. System exiting.")
        sys.exit(1)
    
    node_id = os.getenv("NODE_ID", "UNKNOWN_NODE")
    print(f"--- Starting Node {node_id} ---")

    # Run Network Bridge and Heartbeat concurrently
    try:
        await asyncio.gather(
            connect_to_server(),
            run_heartbeat()
        )
    except Exception as e:
        print(f"Main Loop Error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nNode shutting down gracefully.")