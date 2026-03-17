"""
Hardware Unit Test - PiCamera v2 Frame Capture
SYSC3010 L3-G6 | Scanner Pi

Verifies that the PiCamera v2 can be initialised and returns a valid frame.

Run with:
pytest test_camera.py -v
"""

import time
import numpy as np

def capture_frame():
    """Initialise PiCamera2, capture one frame, return it as a BGR numpy array."""
    import cv2
    from picamera2 import Picamera2

    picam = Picamera2()
    picam.configure(picam.create_still_configuration(
        main={"size": (1280, 960), "format": "RGB888"}
    ))
    picam.start()
    time.sleep(2)                              
    raw   = picam.capture_array()
    frame = cv2.cvtColor(raw, cv2.COLOR_RGB2BGR)
    picam.stop()
    return frame


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_camera_returns_a_frame():
    """Camera must return a numpy array not None, not empty."""
    frame = capture_frame()
    assert isinstance(frame, np.ndarray), "capture did not return a numpy array"
    assert frame.size > 0, "returned frame is empty"


def test_frame_has_correct_dimensions():
    """Frame must match the configured resolution: 1280 × 960, 3 colour channels."""
    frame = capture_frame()
    h, w, c = frame.shape
    assert w == 1280, f"expected width 1280, got {w}"
    assert h == 960,  f"expected height 960, got {h}"
    assert c == 3,    f"expected 3 channels (BGR), got {c}"


def test_frame_is_not_blank():
    """
    Pixel standard deviation must be above a minimum threshold.
    A covered lens or dead sensor produces a near-zero variance image.
    """
    frame = capture_frame()
    std   = float(np.std(frame))
    assert std > 5.0, f"frame looks blank (pixel std={std:.2f}); check lens and connection"
