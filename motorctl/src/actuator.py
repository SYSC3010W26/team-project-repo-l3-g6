############################################
# MOTOR CONTROL SUBSYSTEM - Motor Actuator
# Eric McFetridge # 101310942
############################################

import os
import httpx
import logging

MOONRAKER_BASE = os.getenv("MOONRAKER_URL", "http://localhost:7125")
MOONRAKER_URL = f"{MOONRAKER_BASE}/printer/gcode/script"

# Tweakable delay between moves in milliseconds (0 = no visible delay)
MOVE_DELAY_MS = int(os.getenv("MOVE_DELAY_MS", "0"))

# Configure logging for motor operations
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Face to Motor Mapping (m3 is U face)
FACE_TO_MOTOR = {
    'R': 1,
    'L': 2,
    'U': 3,
    'F': 4,
    'B': 5
}

def translate_singmaster_to_macro(move_str: str) -> str:
    """
    Translates standard Rubiks notation to MOVEMNN macros.
    Example: U' -> MOVEM32 (Motor 3, Move 2)
    """
    if not move_str:
        return ""
    
    face = move_str[0].upper()
    motor_num = FACE_TO_MOTOR.get(face)
    if not motor_num:
        return ""
    
    suffix = move_str[1:]
    if suffix == "'":
        move_type = 2 # 90 CCW
    elif suffix == "2":
        move_type = 3 # 180
    else:
        move_type = 1 # 90 CW
        
    return f"MOVEM{motor_num}{move_type}"

async def execute_move_sequence(moves_str: str) -> bool:
    """
    Translates a space-separated string of moves and dispatches to Moonraker via G-code macros.
    """
    if not moves_str:
        logger.info("No moves to execute")
        return True
    
    moves = moves_str.strip().split()
    gcode_commands = []
    
    for m in moves:
        macro = translate_singmaster_to_macro(m)
        if macro:
            gcode_commands.append(macro)
            # G4 P<ms> provides the delay, P0 ensures sync without extra delay
            delay_cmd = f"G4 P{MOVE_DELAY_MS}" if MOVE_DELAY_MS > 0 else "G4 P0"
            gcode_commands.append(delay_cmd)

    full_script = "\n".join(gcode_commands)
    
    logger.info(f"Dispatching batch to Klipper: {full_script.replace('\\n', ' ')}")
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(MOONRAKER_URL, json={"script": full_script}, timeout=30.0)
            return resp.status_code == 200
    except Exception as e:
        logger.error(f"Moonraker connection failed: {e}")
        return False
