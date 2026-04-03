#!/usr/bin/env python3
"""
Scanner Calibration Tool
=========================
Two modes:

1. COLOUR calibration  (default)
   Live HSV readout — point the camera at each sticker colour one at a time
   and note the H/S/V values shown on screen. Update COLOUR_RANGES in
   scanner_pi.py to match.

     python3 calibrate.py

2. ROI calibration  (--roi)
   Manually click the 4 corners of the cube face for each position in the
   scan sequence (U, F, R, B, L). Saves a calibration file that scanner_pi.py
   loads automatically to skip auto-detection.

     python3 calibrate.py --roi

NOTE: Requires a display (HDMI or VNC). Won't work over plain SSH.
"""

import cv2
import numpy as np
import json
import time
import argparse
from picamera2 import Picamera2


SCAN_SEQUENCE = ["U", "F", "R", "B", "L"]

# ─────────────────────────────────────────────────────────────────────────────
# COLOUR CALIBRATION
# ─────────────────────────────────────────────────────────────────────────────

def run_colour_calibration(picam):
    """
    Live HSV readout tool.
    Crosshair shows the H S V values of the pixel region at the frame centre.
    Use this to find the exact ranges for each colour under your lighting.
    Press S to snapshot the current reading to the terminal.
    Press Q to quit.
    """
    print("\n=== COLOUR CALIBRATION ===")
    print("Point the camera at each sticker colour one at a time.")
    print("Note the H S V values and update COLOUR_RANGES in scanner_pi.py.")
    print("S = snapshot current reading to terminal   Q = quit\n")

    print("Starter ranges (your lighting may need adjustments):")
    print("  White:  S < 40,  V > 160")
    print("  Yellow: H 20-35, S 80+, V 80+")
    print("  Red:    H 0-10 or 170-180, S 120+, V 70+")
    print("  Orange: H 11-19, S 100+, V 70+")
    print("  Blue:   H 100-130, S 80+, V 70+")
    print("  Green:  H 40-80, S 80+, V 40+\n")

    cv2.namedWindow("Colour Calibration", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Colour Calibration", 800, 600)

    while True:
        frame     = picam.capture_array()
        frame_bgr = frame                                     # treat raw frame as BGR
        frame_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)   # HSV from BGR

        fh, fw = frame_bgr.shape[:2]
        cx, cy  = fw // 2, fh // 2

        # Sample 10×10 region at centre
        region_hsv = frame_hsv[cy-5:cy+5, cx-5:cx+5]
        region_bgr = frame_bgr[cy-5:cy+5, cx-5:cx+5]
        mean_hsv   = np.mean(region_hsv, axis=(0, 1))
        mean_bgr   = np.mean(region_bgr, axis=(0, 1)).astype(int)
        h_val, s_val, v_val = int(mean_hsv[0]), int(mean_hsv[1]), int(mean_hsv[2])

        display = frame_bgr.copy()

        # Crosshair
        cv2.line(display, (cx-30, cy), (cx+30, cy), (0,255,255), 2)
        cv2.line(display, (cx, cy-30), (cx, cy+30), (0,255,255), 2)

        # HSV readout
        cv2.putText(display, f"H: {h_val:3d}   S: {s_val:3d}   V: {v_val:3d}",
                    (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0,255,255), 2)

        # Colour swatch
        swatch_colour = (int(mean_bgr[0]), int(mean_bgr[1]), int(mean_bgr[2]))
        cv2.rectangle(display, (10, 55), (90, 120), swatch_colour, -1)
        cv2.rectangle(display, (10, 55), (90, 120), (255,255,255), 2)

        cv2.putText(display, "S=snapshot  Q=quit",
                    (10, fh - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180,180,180), 1)

        cv2.imshow("Colour Calibration", display)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('s'):
            print(f"  Snapshot → H={h_val}  S={s_val}  V={v_val}  BGR={tuple(mean_bgr)}")
        elif key == ord('q'):
            break

    cv2.destroyAllWindows()
    print("\nColour calibration done.")
    print("Update COLOUR_RANGES in scanner_pi.py with your values.")

# ─────────────────────────────────────────────────────────────────────────────
# ROI CALIBRATION
# ─────────────────────────────────────────────────────────────────────────────

_clicked = []

def _on_click(event, x, y, flags, param):
    global _clicked
    if event == cv2.EVENT_LBUTTONDOWN:
        _clicked.append([x, y])
        print(f"  Point {len(_clicked)}: ({x}, {y})")


def run_roi_calibration(node_id: str, picam):
    """
    For each face in the scan sequence, click the 4 corners of the cube face.
    Rotate the physical cube between faces so it's in the same position it
    will be during a real scan.

    Click order per face:
      Top-left → Top-right → Bottom-right → Bottom-left

    ENTER = confirm face   R = redo face   Q = quit
    """
    global _clicked
    calibration = {}

    print("\n=== ROI CALIBRATION ===")
    print("For each face, rotate the cube to that position, then click the")
    print("4 corners of the face IN ORDER:")
    print("  1) Top-left  2) Top-right  3) Bottom-right  4) Bottom-left")
    print("ENTER = confirm   R = redo   Q = quit\n")

    cv2.namedWindow("ROI Calibration", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("ROI Calibration", 960, 720)
    cv2.setMouseCallback("ROI Calibration", _on_click)

    for face in SCAN_SEQUENCE:
        print(f"─── Face: {face} ───")
        print(f"  Rotate cube so face {face} is head-on to the camera, then click.")
        _clicked = []

        while True:
            frame     = picam.capture_array()
            frame_bgr = frame  # already RGB, skip the BGR conversion
            display   = frame_bgr.copy()

            # Draw clicked points
            for i, pt in enumerate(_clicked):
                cv2.circle(display, tuple(pt), 8, (0, 255, 0), -1)
                cv2.putText(display, str(i+1), (pt[0]+10, pt[1]-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

            # Connect points into quad when all 4 are clicked
            if len(_clicked) == 4:
                pts_arr = np.array(_clicked, np.int32).reshape((-1, 1, 2))
                cv2.polylines(display, [pts_arr], True, (0, 255, 0), 2)

            # Status text
            n = len(_clicked)
            cv2.putText(display, f"Face {face}: {n}/4 corners clicked",
                        (10, 38), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,255), 2)
            if n == 4:
                cv2.putText(display, "ENTER=confirm   R=redo",
                            (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,200,0), 2)

            cv2.imshow("ROI Calibration", display)
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                cv2.destroyAllWindows()
                print("Calibration aborted.")
                return

            if n == 4:
                key2 = cv2.waitKey(0) & 0xFF
                if key2 == 13:  # ENTER
                    calibration[face] = _clicked.copy()
                    print(f"  Saved corners for {face}: {_clicked}")
                    _clicked = []
                    break
                elif key2 == ord('r'):
                    print("  Retrying...")
                    _clicked = []

    cv2.destroyAllWindows()

    # Save calibration file
    out_path = f"calibration_{node_id}.json"
    with open(out_path, "w") as f:
        json.dump(calibration, f, indent=2)

    print(f"\n[CAL] Saved to {out_path}")
    print("[CAL] scanner_pi.py will load this automatically on next start.")
    print("[CAL] Re-run this any time the camera or cube fixture is moved.")

# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Scanner calibration tool")
    parser.add_argument("--node-id", default="scanner_pi_1",
                        help="Must match --node-id used in scanner_pi.py")
    parser.add_argument("--roi",     action="store_true",
                        help="Run ROI corner calibration instead of colour calibration")
    args = parser.parse_args()

    print("[INIT] Starting PiCamera2...")
    picam = Picamera2()
    cfg   = picam.create_preview_configuration(
        main={"size": (1280, 960), "format": "RGB888"}
    )
    picam.configure(cfg)
    picam.start()
    time.sleep(2)

    # Lock exposure and white balance so HSV readings are stable
    picam.set_controls({
        "AeEnable": False,           # disable auto exposure
        "AwbEnable": False,          # disable auto white balance
        "ExposureTime": 500000,       # fixed exposure in microseconds — adjust if too dark/bright
        "AnalogueGain": 8.0,         # fixed gain — adjust if image is too dark
    })
    time.sleep(1)  # let the settings take effect

    print("[INIT] Camera ready.\n")

    try:
        if args.roi:
            run_roi_calibration(args.node_id, picam)
        else:
            run_colour_calibration(picam)
    finally:
        picam.stop()


if __name__ == "__main__":
    main()
