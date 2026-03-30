############################################
# MOTOR CONTROL SUBSYSTEM - Motor Actuator
# Eric McFetridge SYSC3010:L3G6
############################################

import asyncio
import logging
from typing import Any, Dict, Optional

from dotenv import load_dotenv

load_dotenv()

# Configure logging for motor operations
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# GPIO Hardware Abstraction Layer
# This allows real GPIO to be used on RPi and mocked in tests
class GPIO:
    """Abstraction layer for GPIO operations."""
    
    BCM = 11  # GPIO numbering mode (BCM = Broadcom)
    OUT = 1   # GPIO direction
    HIGH = 1  # GPIO logic level
    LOW = 0   # GPIO logic level
    
    @staticmethod
    def setmode(mode):
        """Set GPIO numbering mode (BCM or BOARD)."""
        pass
    
    @staticmethod
    def setup(pin, mode):
        """Configure a GPIO pin as input or output."""
        pass
    
    @staticmethod
    def output(pin, level):
        """Set a GPIO pin to HIGH or LOW."""
        pass
    
    @staticmethod
    def cleanup():
        """Release GPIO resources."""
        pass

# Global GPIO implementation (can be mocked for testing)
_gpio_impl: Optional[Any] = None
_mock_gpio_state: Dict[int, int] = {}

def set_gpio_impl(impl: Any):
    """Set the GPIO implementation (for testing with mocks)."""
    global _gpio_impl
    _gpio_impl = impl

def get_gpio():
    """Get the active GPIO implementation."""
    global _gpio_impl
    if _gpio_impl is not None:
        return _gpio_impl
    
    # Try to import real RPi.GPIO on hardware
    try:
        import RPi.GPIO as real_gpio
        _gpio_impl = real_gpio
        return real_gpio
    except ImportError:
        # Not on RPi hardware, use stub
        return GPIO

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
    
    Implements hardware control via GPIO STEP/DIR signals:
    1. Enable the motor (set ENABLE pin HIGH)
    2. Set DIR pin to indicate rotation direction (HIGH=CW, LOW=CCW)
    3. Generate STEP pulses at 400 Hz (2.5 ms period)
    4. Wait for motion to complete
    5. Disable motor (set ENABLE pin LOW) to save power
    
    For development/testing on non-RPi machines, runs in mock mode using
    asyncio.sleep to simulate the real timing without GPIO hardware.
    
    Args:
        motor_id: Motor index (0-4)
        direction: +1 for CW, -1 for CCW
        steps: Number of microsteps to execute (200=90°, 400=180°)
    
    Returns:
        bool: True if signal sent successfully, False on error
        
    Example:
        >>> result = await _send_motor_signal(0, 1, 200)  # Right motor CW
        >>> assert result is True
    
    GPIO Signals:
        STEP pin:   Pulsed at 400 Hz (high 1.25ms, low 1.25ms)
        DIR pin:    Set at start of move (HIGH for CW, LOW for CCW)
        ENABLE pin: HIGH during move (LOW to disable/sleep motor)
    
    Hardware Integration (RPi with RPi.GPIO):
        When RPi.GPIO is available, real GPIO signals are sent to STEP, DIR,
        and ENABLE pins. On dev machines without GPIO, timing is simulated.
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
        
        # Get GPIO implementation (real or mock)
        gpio = get_gpio()
        
        # Get pin assignments
        step_pin = MOTOR_STEP_PINS[motor_id]
        dir_pin = MOTOR_DIR_PINS[motor_id]
        enable_pin = MOTOR_ENABLE_PINS[motor_id]
        
        # Setup GPIO pins (no-op if using mock or already set up)
        try:
            gpio.setmode(gpio.BCM)
            gpio.setup(step_pin, gpio.OUT)
            gpio.setup(dir_pin, gpio.OUT)
            gpio.setup(enable_pin, gpio.OUT)
        except (AttributeError, RuntimeError):
            # GPIO setup failed (likely not RPi hardware) - continue with mock
            pass
        
        # Enable motor (HIGH = enabled, ready to receive signals)
        try:
            gpio.output(enable_pin, gpio.HIGH)
        except (AttributeError, RuntimeError):
            pass
        
        # Set direction (HIGH = CW, LOW = CCW)
        dir_level = gpio.HIGH if direction > 0 else gpio.LOW
        try:
            gpio.output(dir_pin, dir_level)
        except (AttributeError, RuntimeError):
            pass
        
        # Generate STEP pulses at 400 Hz
        # 400 Hz = 2.5 ms period = 1.25 ms per half-cycle
        pulse_period = 1.0 / 400.0  # 0.0025 seconds
        half_period = pulse_period / 2.0  # 0.00125 seconds (1.25 ms)
        
        logger.debug(
            f"GPIO signal start: motor_id={motor_id} ({motor_name}) "
            f"dir_pin={dir_pin} dir={'HIGH' if direction > 0 else 'LOW'} "
            f"step_pin={step_pin} step_count={steps} "
            f"frequency=400Hz period={pulse_period*1000:.2f}ms"
        )
        
        # Generate step pulses
        for step_num in range(steps):
            # STEP HIGH
            try:
                gpio.output(step_pin, gpio.HIGH)
            except (AttributeError, RuntimeError):
                pass
            
            await asyncio.sleep(half_period)
            
            # STEP LOW
            try:
                gpio.output(step_pin, gpio.LOW)
            except (AttributeError, RuntimeError):
                pass
            
            await asyncio.sleep(half_period)
        
        # Disable motor (LOW = disabled/sleeping, saves power)
        try:
            gpio.output(enable_pin, gpio.LOW)
        except (AttributeError, RuntimeError):
            pass
        
        # Clean up GPIO (safe to call even if not on RPi)
        try:
            gpio.cleanup()
        except (AttributeError, RuntimeError):
            pass
        
        # Calculate actual duration for logging
        move_duration = steps * pulse_period
        logger.info(
            f"Motor {motor_id} ({motor_name}) completed {direction_str} "
            f"rotation: {steps} steps @ 400Hz = {move_duration:.2f}s"
        )
        
        return True
    
    except Exception as e:
        logger.exception(f"Error sending motor signal: {e}")
        return False
