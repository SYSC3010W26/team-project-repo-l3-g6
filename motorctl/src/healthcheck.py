########################################
# MOTOR CONTROL SUBSYSTEM - Healthcheck
# Eric McFetridge SYSC3010:L3G6
########################################

import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()
MOONRAKER_URL = os.getenv("MOONRAKER_URL")

async def check_klipper_ready():
    """Polls Moonraker API until Klipper reports a 'ready' state."""
    print(f"[Healthcheck] Contacting Klipper at {MOONRAKER_URL}...")
    async with httpx.AsyncClient() as client:
        try:
            # Moonraker endpoint for printer status
            response = await client.get(f"{MOONRAKER_URL}/printer/info", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                state = data.get("result", {}).get("state")
                if state == "ready":
                    print("[Healthcheck] Klipper is READY.")
                    return True
                print(f"[Healthcheck] Klipper is in state: {state}")
            return False
        except Exception as e:
            print(f"[Healthcheck] Connection failed: {e}")
            return False

async def wait_for_hardware(attempts=10, delay=3):
    for i in range(attempts):
        if await check_klipper_ready():
            return True
        print(f"  Attempt {i+1}/{attempts} failed. Retrying in {delay}s...")
        await asyncio.sleep(delay)
    return False