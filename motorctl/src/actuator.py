############################################
# MOTOR CONTROL SUBSYSTEM - Motor Actuator
# Eric McFetridge SYSC3010:L3G6
############################################

import os
import asyncio
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging for motor operations
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Move notation to motor mapping
# Format: move_notation -> (motor_id, direction, steps)
# This maps standard Rubik's cube Singmaster notation to hardware signals
MOVE_MAP = {
    "R": (0, 1, 200),      # Right face, CW, 200 steps (~90°)
    "R'": (0, -1, 200),    # Right face, CCW
    "R2": (0, 1, 400),     # Right face, CW 180°
    "L": (1, -1, 200),     # Left face, CCW (opposite of right)
    "L'": (1, 1, 200),
    "L2": (1, 1, 400),
    "U": (2, 1, 200),      # Up face, CW
    "U'": (2, -1, 200),
    "U2": (2, 1, 400),
    "F": (3, 1, 200),      # Front face, CW
    "F'": (3, -1, 200),
    "F2": (3, 1, 400),
    "D": (4, -1, 200),     # Down face, CCW (opposite of up)
    "D'": (4, 1, 200),
    "D2": (4, 1, 400),
    "B": (3, -1, 200),     # Back face (approximation via front face CCW)
    "B'": (3, 1, 200),
    "B2": (3, 1, 400),
}

MOTOR_NAMES = {0: "Right", 1: "Left", 2: "Up", 3: "Front", 4: "Down"}
MOTOR_STEP_PINS = {0: 26, 1: 16, 2: 12, 3: 7, 4: 8}  # Raspberry Pi GPIO BCM pins
MOTOR_DIR_PINS = {0: 27, 1: 17, 2: 13, 3: 11, 4: 9}
MOTOR_ENABLE_PINS = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2}


async def execute_move_sequence(moves):
    """
    Execute a sequence of Rubik's cube moves via stepper motors.
    
    Translates standard Singmaster move notation (R, U, F2, R', etc.) to GPIO
    STEP/DIR signals on the SKR v1.4 motor controller board. Each move is
    executed sequentially with proper timing and progress reporting.
    
    Args:
        moves: List of move notation strings, e.g., ['R', 'U', "R'", 'F2']
               Each string must be a valid move in MOVE_MAP.
    
    Returns:
        bool: True if all moves executed successfully, False on hardware error
              or unknown move notation.
    
    Raises:
        No exceptions raised - returns False on error instead.
    
    Example:
        >>> result = await execute_move_sequence(['R', 'U', "R'"])
        >>> assert result is True
        
        >>> result = await execute_move_sequence(['INVALID'])
        >>> assert result is False
    
    Performance:
        - 90° move (200 steps @ 400 Hz): ~1.0 second
        - 180° move (400 steps @ 400 Hz): ~2.0 seconds
        - Typical CFOP solution (22 moves): ~22-25 seconds
    """
    if not moves:
        logger.info("No moves to execute")
        return True
    
    logger.info(f"Starting execution of {len(moves)} moves: {moves}")
    
    try:
        for idx, move in enumerate(moves):
            if move not in MOVE_MAP:
                logger.error(f"Unknown move notation: {move}")
                return False
            
            motor_id, direction, steps = MOVE_MAP[move]
            motor_name = MOTOR_NAMES[motor_id]
            direction_str = "CW" if direction > 0 else "CCW"
            
            logger.info(
                f"Move {idx+1}/{len(moves)}: {move} → "
                f"motor_id={motor_id} ({motor_name}) "
                f"direction={direction_str} steps={steps}"
            )
            
            # Execute the move via GPIO (stubbed here, real implementation calls Klipper)
            success = await _send_motor_signal(motor_id, direction, steps)
            if not success:
                logger.error(f"Failed to execute move: {move}")
                return False
            
            # Brief delay between moves (motors need settling time)
            await asyncio.sleep(0.1)
        
        logger.info(f"Successfully executed all {len(moves)} moves")
        return True
    
    except Exception as e:
        logger.exception(f"Exception during execution: {e}")
        return False


async def _send_motor_signal(motor_id, direction, steps):
    """
    Send STEP/DIR pulse signal to a stepper motor via GPIO.
    
    On actual hardware, this would:
    1. Enable the motor (set ENABLE pin high)
    2. Set DIR pin to indicate rotation direction
    3. Generate STEP pulses at a frequency matching desired speed
    4. Wait for motion to complete (~0.5-1.0s per move)
    5. Disable motor (set ENABLE pin low)
    
    In this stub, we simulate the timing but don't actually touch GPIO
    (which would require RPi.GPIO or gpiozero library + root permissions).
    
    Args:
        motor_id: Motor index (0-4)
        direction: +1 for CW, -1 for CCW
        steps: Number of microsteps to execute
    
    Returns:
        bool: True if signal sent successfully, False on error
        
    Example:
        >>> result = await _send_motor_signal(0, 1, 200)  # Right motor CW
        >>> assert result is True
    
    Hardware Integration:
        For Raspberry Pi with RPi.GPIO library:
        ```python
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        step_pin = MOTOR_STEP_PINS[motor_id]
        dir_pin = MOTOR_DIR_PINS[motor_id]
        enable_pin = MOTOR_ENABLE_PINS[motor_id]
        
        GPIO.setup(step_pin, GPIO.OUT)
        GPIO.setup(dir_pin, GPIO.OUT)
        GPIO.setup(enable_pin, GPIO.OUT)
        
        GPIO.output(enable_pin, GPIO.HIGH)  # Enable motor
        GPIO.output(dir_pin, GPIO.HIGH if direction > 0 else GPIO.LOW)
        
        # Generate step pulses (frequency ~400 Hz for ~1 sec per 200-step move)
        step_freq = 400  # Hz
        for _ in range(steps):
            GPIO.output(step_pin, GPIO.HIGH)
            await asyncio.sleep(1 / (2 * step_freq))
            GPIO.output(step_pin, GPIO.LOW)
            await asyncio.sleep(1 / (2 * step_freq))
        
        GPIO.output(enable_pin, GPIO.LOW)  # Disable motor
        GPIO.cleanup()
        ```
    """
    try:
        # Validate inputs
        if motor_id < 0 or motor_id > 4:
            logger.error(f"Invalid motor_id: {motor_id}. Must be 0-4.")
            return False
        
        if steps <= 0:
            logger.error(f"Invalid steps: {steps}. Must be positive.")
            return False
        
        if direction not in (-1, 1):
            logger.error(f"Invalid direction: {direction}. Must be +1 or -1.")
            return False
        
        motor_name = MOTOR_NAMES[motor_id]
        direction_str = "CW" if direction > 0 else "CCW"
        
        # Simulate motor movement time (~1 second per 200-step move)
        move_duration = (steps / 200.0) * 1.0
        
        logger.debug(
            f"GPIO signal: motor_id={motor_id} ({motor_name}) "
            f"dir_pin={MOTOR_DIR_PINS[motor_id]} "
            f"dir={'HIGH' if direction > 0 else 'LOW'} "
            f"step_pin={MOTOR_STEP_PINS[motor_id]} "
            f"step_count={steps} "
            f"duration~{move_duration:.1f}s"
        )
        
        # Wait for motor to complete (simulated in stub, actual GPIO in hardware)
        await asyncio.sleep(move_duration)
        
        logger.debug(f"Motor {motor_id} ({motor_name}) completed {direction_str} rotation")
        return True
    
    except Exception as e:
        logger.exception(f"Error sending motor signal: {e}")
        return False
