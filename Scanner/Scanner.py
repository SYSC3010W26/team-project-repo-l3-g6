#!/usr/bin/env python3
"""
Rubik's Cube Scanner — Diagnostic
SYSC3010 L3-G6

Controls:
    SPACE  — detect colours in the grid
    ENTER  — confirm face and move to next
    R      — retake current face (re-prompts centre colour too)
    Q      — quit
"""

import cv2
import numpy as np
import time
import json
from picamera2 import Picamera2

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

CAMERA_INDEX   = 0
CAPTURE_WIDTH  = 1280
CAPTURE_HEIGHT = 960

FACE_ORDER  = ["U", "R", "F", "D", "L", "B"]
STATE_ORDER = ["U", "R", "F", "D", "L", "B"]

GRID_SIZE   = 240
ROI_PADDING = 150

# ─────────────────────────────────────────────────────────────────────────────
# COLOUR RANGES  — update with calibrate.py readings
# ─────────────────────────────────────────────────────────────────────────────

COLOUR_RANGES = {
    "W":  ([0,   0,   150], [180, 45,  255]),
    "Y":  ([13,  100, 150], [30,  255, 255]),
    "R":  ([170, 150, 100], [180, 255, 255]),
    "R2": ([0,   150, 100], [5,   255, 255]),
    "O":  ([6,   150, 150], [15,  255, 255]),
    "B":  ([108, 200, 100], [122, 255, 255]),
    "G":  ([64,  150, 60],  [79,  255, 255]),
}

COLOUR_DISPLAY = {
    "W": (255, 255, 255), "Y": (0,   255, 255),
    "R": (0,   0,   255), "O": (0,   128, 255),
    "B": (255, 0,   0  ), "G": (0,   200, 0  ),
    "?": (80,  80,  80 ),
}

# ─────────────────────────────────────────────────────────────────────────────
# COLOUR CLASSIFICATION
# ─────────────────────────────────────────────────────────────────────────────

def classify_colour(bgr):
    pixel = np.uint8([[bgr]])
    hsv   = cv2.cvtColor(pixel, cv2.COLOR_BGR2HSV)[0][0]
    h, s, v = int(hsv[0]), int(hsv[1]), int(hsv[2])

    if s < 45 and v > 150:
        return "W"

    for colour, (lo, hi) in COLOUR_RANGES.items():
        if colour == "R2":
            continue
        if lo[0] <= h <= hi[0] and lo[1] <= s <= hi[1] and lo[2] <= v <= hi[2]:
            return colour

    if (COLOUR_RANGES["R"][0][0]  <= h <= COLOUR_RANGES["R"][1][0] or
            COLOUR_RANGES["R2"][0][0] <= h <= COLOUR_RANGES["R2"][1][0]):
        if s >= COLOUR_RANGES["R"][0][1] and v >= COLOUR_RANGES["R"][0][2]:
            return "R"

    return "?"

# ─────────────────────────────────────────────────────────────────────────────
# GRID HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def get_grid_origin(frame):
    h, w = frame.shape[:2]
    ox = w // 2 - GRID_SIZE // 2
    oy = h // 2 - GRID_SIZE // 2 + 100
    return ox, oy

def find_face_in_roi(frame):
    """Colour-mask based face finder. Snaps grid to cube face"""
    global GRID_SIZE
    h, w = frame.shape[:2]

    roi_x1 = max(w // 2 - GRID_SIZE // 2 - ROI_PADDING, 0)
    roi_x2 = min(w // 2 + GRID_SIZE // 2 + ROI_PADDING, w)
    roi_y1 = max(h // 2 - GRID_SIZE // 2 - ROI_PADDING + 100, 0)
    roi_y2 = min(h // 2 + GRID_SIZE // 2 + ROI_PADDING + 100, h)

    roi     = frame[roi_y1:roi_y2, roi_x1:roi_x2]
    hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    cube_mask = np.zeros(roi.shape[:2], dtype=np.uint8)
    for colour, (lo, hi) in COLOUR_RANGES.items():
        m = cv2.inRange(hsv_roi, np.array(lo), np.array(hi))
        cube_mask = cv2.bitwise_or(cube_mask, m)

    kernel    = np.ones((12, 12), np.uint8)
    cube_mask = cv2.morphologyEx(cube_mask, cv2.MORPH_CLOSE, kernel)
    cube_mask = cv2.morphologyEx(cube_mask, cv2.MORPH_OPEN,  kernel)

    contours, _ = cv2.findContours(cube_mask, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < 8000:
        return None

    x, y, bw, bh = cv2.boundingRect(largest)
    detected_size = min(bw, bh)
    GRID_SIZE     = max(150, min(detected_size, 500))

    ox = roi_x1 + x + (bw - GRID_SIZE) // 2
    oy = roi_y1 + y + (bh - GRID_SIZE) // 2
    ox = max(0, min(ox, w - GRID_SIZE))
    oy = max(0, min(oy, h - GRID_SIZE))

    return ox, oy

def draw_grid(frame, detected=None, origin=None):
    ox, oy    = origin if origin else get_grid_origin(frame)
    cell_size = GRID_SIZE // 3

    for row in range(3):
        for col in range(3):
            x = ox + col * cell_size
            y = oy + row * cell_size
            is_centre  = (row == 1 and col == 1)
            thickness  = 3 if is_centre else 2
            border_col = (0, 255, 255) if is_centre else (0, 255, 0)
            cv2.rectangle(frame, (x, y), (x + cell_size, y + cell_size),
                          border_col, thickness)

            if detected:
                idx        = row * 3 + col
                letter     = detected[idx]
                dot_colour = COLOUR_DISPLAY.get(letter, (80, 80, 80))
                cx         = x + cell_size // 2
                cy         = y + cell_size // 2
                cv2.circle(frame, (cx, cy), 22, dot_colour, -1)
                cv2.circle(frame, (cx, cy), 22, (0, 0, 0), 1)
                cv2.putText(frame, letter, (cx - 8, cy + 7),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2)

def detect_colours(frame, origin=None):
    ox, oy    = origin if origin else get_grid_origin(frame)
    cell_size = GRID_SIZE // 3
    detected  = []

    for row in range(3):
        for col in range(3):
            cx = ox + col * cell_size + cell_size // 2
            cy = oy + row * cell_size + cell_size // 2
            x1 = max(cx - 10, 0)
            x2 = min(cx + 10, frame.shape[1])
            y1 = max(cy - 10, 0)
            y2 = min(cy + 10, frame.shape[0])
            region = frame[y1:y2, x1:x2]
            mean   = cv2.mean(region)
            bgr    = (int(mean[0]), int(mean[1]), int(mean[2]))
            detected.append(classify_colour(bgr))

    return detected

# ─────────────────────────────────────────────────────────────────────────────
# CENTRE COLOUR PROMPT
# Declare the centre colour before scan
# ─────────────────────────────────────────────────────────────────────────────

CENTRE_KEY_MAP = {
    ord('w'): "W", ord('y'): "Y", ord('r'): "R",
    ord('o'): "O", ord('b'): "B", ord('g'): "G",
}

def prompt_centre_colour(cam, face_name, face_index):
    """
    Show a live camera feed and ask the user to press the key matching
    the centre colour of the face they are about to scan.
    Returns the declared colour letter, or None if Q is pressed.
    """
    print(f"\n[CENTRE] Declare centre colour for face {face_name}")
    print("         W=white  Y=yellow  R=red  O=orange  B=blue  G=green")

    while True:
        raw     = cam.capture_array()
        display = raw.copy()

        overlay = display.copy()
        cv2.rectangle(overlay, (0, 0), (display.shape[1], display.shape[0]),
                      (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.45, display, 0.55, 0, display)

        cv2.putText(display,
                    f"Face {face_index + 1}/{len(FACE_ORDER)}: {face_name}",
                    (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 255), 2)
        cv2.putText(display,
                    "Centre cap removed — what colour is the centre?",
                    (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

        labels = [("W", "White",  (255,255,255)), ("Y", "Yellow", (0,255,255)),
                  ("R", "Red",    (0,0,255)),     ("O", "Orange", (0,128,255)),
                  ("B", "Blue",   (255,0,0)),     ("G", "Green",  (0,200,0))]
        for i, (key, name, colour) in enumerate(labels):
            x = 30 + i * 155
            y = 160
            cv2.circle(display, (x, y), 28, colour, -1)
            cv2.circle(display, (x, y), 28, (255, 255, 255), 2)
            cv2.putText(display, key, (x - 10, y + 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
            cv2.putText(display, f"Press {key}", (x - 30, y + 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        cv2.imshow("Cube Scanner", display)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            return None

        if key in CENTRE_KEY_MAP:
            chosen = CENTRE_KEY_MAP[key]
            print(f"[CENTRE] Face {face_name} centre declared as: {chosen}")
            return chosen

# ─────────────────────────────────────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

def validate_cube_state(cube_state, declared_centres):
    """Validate the 6-face colour dict using declared centre colours."""
    if len(cube_state) != 6:
        return False, f"Need 6 faces, have {len(cube_state)}"

    if set(cube_state.keys()) != set(FACE_ORDER):
        return False, "Missing or extra faces"

    colour_counts = {"W": 0, "R": 0, "O": 0, "Y": 0, "G": 0, "B": 0}

    for face, colours in cube_state.items():
        if len(colours) != 9:
            return False, f"Face {face} has {len(colours)} colours (need 9)"
        for colour in colours:
            if colour not in colour_counts:
                return False, f"Invalid colour '{colour}' on face {face}"
            colour_counts[colour] += 1

    for colour, count in colour_counts.items():
        if count != 9:
            return False, f"Colour {colour} appears {count} times (need 9)"

    centre_colours = list(declared_centres.values())
    if len(set(centre_colours)) != 6:
        return False, f"Declared centre colours are not all unique: {declared_centres}"

    return True, "OK"

def build_state_string(scanned_faces, declared_centres):
    """
    Convert {face: [colour_list]} → 54-char face-letter string.
    Uses declared_centres {face: colour} to build the colour→face mapping.
    """
    colour_to_face = {colour: face for face, colour in declared_centres.items()}

    if len(colour_to_face) != 6:
        raise ValueError("Duplicate declared centre colours — each face must have a unique colour.")

    state_string = ""
    for face in STATE_ORDER:
        for colour in scanned_faces[face]:
            if colour not in colour_to_face:
                raise ValueError(
                    f"Colour '{colour}' on face {face} has no face mapping. "
                    f"Check declared centres: {declared_centres}"
                )
            state_string += colour_to_face[colour]

    if len(state_string) != 54:
        raise ValueError(f"State string is {len(state_string)} chars, expected 54.")

    return state_string

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("[INIT] Starting camera...")
    cam = Picamera2(CAMERA_INDEX)
    cam.configure(cam.create_preview_configuration(
        main={"size": (CAPTURE_WIDTH, CAPTURE_HEIGHT), "format": "RGB888"}
    ))
    cam.start()
    time.sleep(2)
    cam.set_controls({
        "AeEnable":     False,
        "AwbEnable":    False,
        "ExposureTime": 500000,
        "AnalogueGain": 8.0,
    })
    time.sleep(1)
    print("[INIT] Camera ready.")
    print("SPACE=detect  ENTER=confirm  R=retake  Q=quit\n")

    cv2.namedWindow("Cube Scanner", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Cube Scanner", 960, 720)

    scanned_faces    = {}
    declared_centres = {}
    face_index       = 0
    current          = None
    confirmed        = False
    centre_colour    = None

    while face_index < len(FACE_ORDER):
        face_name = FACE_ORDER[face_index]

        # Prompt for centre colour before scanning each face
        if centre_colour is None:
            centre_colour = prompt_centre_colour(cam, face_name, face_index)
            if centre_colour is None:
                break
            current   = None
            confirmed = False

        raw   = cam.capture_array()
        frame = raw
        display = frame.copy()

        detected_origin = find_face_in_roi(frame)
        grid_ox, grid_oy = detected_origin if detected_origin else get_grid_origin(frame)

        draw_grid(display, current if confirmed else None,
                  origin=(grid_ox, grid_oy))

        # Top bar
        centre_bgr = COLOUR_DISPLAY.get(centre_colour, (150, 150, 150))
        cv2.rectangle(display, (0, 0), (display.shape[1], 50), (0, 0, 0), -1)
        cv2.putText(display,
                    f"Face {face_index + 1}/{len(FACE_ORDER)}: {face_name}  |  "
                    f"Centre = {centre_colour}  —  Align to grid, press SPACE",
                    (10, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (0, 255, 255), 2)
        cv2.circle(display, (display.shape[1] - 35, 25), 18, centre_bgr, -1)
        cv2.circle(display, (display.shape[1] - 35, 25), 18, (255, 255, 255), 2)

        # Bottom bar
        cv2.rectangle(display,
                      (0, display.shape[0] - 45),
                      (display.shape[1], display.shape[0]), (0, 0, 0), -1)

        if confirmed and current:
            unknowns   = current.count("?")
            face_str   = "".join(current)
            status_col = (0, 255, 0) if unknowns == 0 else (0, 100, 255)
            cv2.putText(display,
                        f"{face_str}  |  "
                        f"{'ENTER=confirm  R=retake' if unknowns == 0 else f'{unknowns} unknown — R=retake'}",
                        (10, display.shape[0] - 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_col, 2)
        else:
            cv2.putText(display, "SPACE=scan  R=retake  Q=quit",
                        (10, display.shape[0] - 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (180, 180, 180), 1)

        cv2.imshow("Cube Scanner", display)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break

        elif key == ord(' '):
            snap   = find_face_in_roi(frame)
            origin = snap if snap else get_grid_origin(frame)
            current    = detect_colours(frame, origin=origin)
            current[4] = centre_colour   # inject declared centre at position 4
            confirmed  = True
            print(f"  Detected {face_name}: {''.join(current)}  (centre={centre_colour})")

        elif key == 13 and confirmed:
            scanned_faces[face_name]    = current
            declared_centres[face_name] = centre_colour
            print(f"  Confirmed {face_name}: {''.join(current)}")
            face_index   += 1
            current       = None
            confirmed     = False
            centre_colour = None

        elif key == ord('r'):
            current       = None
            confirmed     = False
            centre_colour = None
            print(f"  Retaking {face_name}...")

    cam.stop()
    cv2.destroyAllWindows()

    # ── Results ───────────────────────────────────────────────────────────────
    if len(scanned_faces) < 6:
        print(f"\n  Only {len(scanned_faces)}/6 faces scanned — exiting.")
        return

    print("\n── Scan Results ───────────────────────────")
    for face in FACE_ORDER:
        print(f"  {face}: {''.join(scanned_faces[face])}")
    print(f"  Centres: {declared_centres}")

    valid, reason = validate_cube_state(scanned_faces, declared_centres)
    if not valid:
        print(f"\n  Validation FAILED: {reason}")
        print("  Please rescan the cube.")
        return

    try:
        state_string = build_state_string(scanned_faces, declared_centres)
    except ValueError as e:
        print(f"\n  State string error: {e}")
        return

    all_colours = [c for face in scanned_faces.values() for c in face]
    confidence  = sum(1 for c in all_colours if c != "?") / len(all_colours)

    print(f"\n  State string: {state_string}")
    print(f"  Confidence:   {confidence:.2%}")
    print(f"  Validation:   OK")

    with open("cube_state.json", "w") as f:
        json.dump(scanned_faces, f, indent=2)
    with open("cube_string.txt", "w") as f:
        f.write(state_string)
    print("  Saved: cube_state.json  cube_string.txt")
    print("──────────────────────────────────────────")


if __name__ == "__main__":
    main()
