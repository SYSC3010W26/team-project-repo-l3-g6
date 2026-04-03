"""
Software Unit Test - Colour Detection
SYSC3010 L3-G6 | Scanner Pi

Tests the colour classification algorithm against a predetermined cube face
pattern.

Predetermined test face (reading left->right, top->bottom):
    W  O  G
    B  R  Y      expected face string: "WOGRBYYBW"  
    Y  B  W

Run with:
pytest test_colour_detection.py -v
"""

import cv2
import numpy as np

# ── Colour classification code ───────────────────

COLOUR_RANGES = {
    "W":  ([0,   0,   180], [180, 40,  255]),
    "Y":  ([20,  80,  80],  [35,  255, 255]),
    "R":  ([0,   120, 70],  [10,  255, 255]),
    "R2": ([170, 120, 70],  [180, 255, 255]),
    "O":  ([11,  100, 70],  [19,  255, 255]),
    "B":  ([100, 80,  70],  [130, 255, 255]),
    "G":  ([40,  80,  40],  [80,  255, 255]),
}

def classify_colour(bgr):
    """Return the Rubik's colour letter for a single BGR pixel."""
    pixel = np.uint8([[bgr]])
    hsv   = cv2.cvtColor(pixel, cv2.COLOR_BGR2HSV)[0][0]
    h, s, v = int(hsv[0]), int(hsv[1]), int(hsv[2])

    if s < 40 and v > 160:
        return "W"

    for colour, (lo, hi) in COLOUR_RANGES.items():
        if colour == "R2":
            continue
        if lo[0] <= h <= hi[0] and lo[1] <= s <= hi[1] and lo[2] <= v <= hi[2]:
            return colour

    r_lo, _ = COLOUR_RANGES["R"]
    r2_lo, _ = COLOUR_RANGES["R2"]
    if (COLOUR_RANGES["R"][0][0] <= h <= COLOUR_RANGES["R"][1][0] or
            COLOUR_RANGES["R2"][0][0] <= h <= COLOUR_RANGES["R2"][1][0]):
        if s >= r_lo[1] and v >= r_lo[2]:
            return "R"

    return "?"

def scan_face(image):
    """
    Divide a 300×300 image into a 3×3 grid, sample the centre of each cell,
    and return a 9-character colour string (left->right, top->bottom).
    """
    step = image.shape[0] // 3
    result = []
    for row in range(3):
        for col in range(3):
            cx = int(step * col + step / 2)
            cy = int(step * row + step / 2)
            mask = np.zeros(image.shape[:2], dtype=np.uint8)
            cv2.circle(mask, (cx, cy), 8, 255, -1)
            mean = cv2.mean(image, mask=mask)
            bgr  = (int(mean[0]), int(mean[1]), int(mean[2]))
            result.append(classify_colour(bgr))
    return "".join(result)

# ── Synthetic image helper ────────────────────────────────────────────────────

def hsv_to_bgr(h, s, v):
    """Convert a single HSV value to BGR."""
    pixel = np.uint8([[[h, s, v]]])
    bgr   = cv2.cvtColor(pixel, cv2.COLOR_HSV2BGR)[0][0]
    return (int(bgr[0]), int(bgr[1]), int(bgr[2]))

# Pure-HSV representative pixels for each colour.
# These sit at the centre of each COLOUR_RANGES band.
COLOUR_PIXELS = {
    "W": hsv_to_bgr(0,   0,   220),   # white:  low saturation, high value
    "Y": hsv_to_bgr(28,  200, 200),   # yellow: H ≈ 28
    "R": hsv_to_bgr(5,   200, 200),   # red:    H ≈ 5 (low-hue side)
    "O": hsv_to_bgr(15,  200, 200),   # orange: H ≈ 15
    "B": hsv_to_bgr(115, 200, 200),   # blue:   H ≈ 115
    "G": hsv_to_bgr(60,  200, 160),   # green:  H ≈ 60
}

def make_face_image(pattern):
    """
    Build a 300×300 synthetic face image from a 9-letter colour pattern string.
    Each cell is filled with the solid BGR colour for that letter.

    pattern: e.g. "WOGRBYYB W" 9 chars, left->right top->bottom
    """
    size  = 300
    step  = size // 3
    image = np.zeros((size, size, 3), dtype=np.uint8)
    for idx, letter in enumerate(pattern):
        row, col = divmod(idx, 3)
        y1, y2   = row * step, (row + 1) * step
        x1, x2   = col * step, (col + 1) * step
        image[y1:y2, x1:x2] = COLOUR_PIXELS[letter]
    return image

# ── Predetermined test face ───────────────────────────────────────────────────
#
#   W  O  G
#   B  R  Y    ->  face string: "WOGRBYYBW"
#   Y  B  W
#
# This is the known pattern used for the face scan test.

TEST_PATTERN  = "WOGRBYYBW"   
TEST_IMAGE    = make_face_image(TEST_PATTERN)

# ── Tests ─────────────────────────────────────────────────────────────────────

def test_classify_white():
    assert classify_colour(COLOUR_PIXELS["W"]) == "W"

def test_classify_yellow():
    assert classify_colour(COLOUR_PIXELS["Y"]) == "Y"

def test_classify_red():
    assert classify_colour(COLOUR_PIXELS["R"]) == "R"

def test_classify_orange():
    assert classify_colour(COLOUR_PIXELS["O"]) == "O"

def test_classify_blue():
    assert classify_colour(COLOUR_PIXELS["B"]) == "B"

def test_classify_green():
    assert classify_colour(COLOUR_PIXELS["G"]) == "G"

def test_scan_face_matches_known_pattern():
    """
    Scanning the synthetic test face image must return the exact predetermined
    pattern string the core end-to-end check for the colour detection pipeline.
    """
    result = scan_face(TEST_IMAGE)
    assert result == TEST_PATTERN, (
        f"Face scan returned '{result}', expected '{TEST_PATTERN}'"
    )
