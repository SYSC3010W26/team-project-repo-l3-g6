# Scanner Subsystem
## SYSC3010 L3-G6 | Rubik's Cube Solver
**Author: Basil Thotapilly**

---

## Overview

The Scanner Pi captures the colour state of a scrambled Rubik's cube one
face at a time and produces a validated 54-character state string for the
solver. The two scripts that make up the scanner are:

- **`Scanner.py`** - the main scanning script
- **`calibrate.py`** - HSV colour tuning tool

---

## Hardware

- Raspberry Pi 4
- Raspberry Pi Camera Module v2 (PiCamera v2)
- Black backdrop behind and under the cube

---

## Dependencies

```bash
sudo apt install python3-picamera2 python3-opencv -y
pip3 install numpy --break-system-packages
```

---

## calibrate.py — Colour Calibration

Run this before scanning any time lighting conditions change or the scanner
is moved. There are two modes:

### Colour calibration (default)

```bash
python3 calibrate.py
```

Opens a live camera window with a crosshair at the centre and an HSV readout.
Point the crosshair at each sticker colour one at a time and press **S** to
snapshot the H S V values to the terminal. Press **Q** to quit.

Once you have readings for all 6 colours, update `COLOUR_RANGES` at the top
of `Scanner.py` with your values. Set the lower bound slightly below your
reading and the upper bound slightly above to give tolerance for variation
across the sticker surface.

```
Controls:
    S — snapshot current H S V reading to terminal
    Q — quit
```

### Camera settings in calibrate.py

Exposure and white balance are locked before calibrating so HSV readings are
stable. If the image is too dark or too bright, adjust these values at the
bottom of `calibrate.py`:

```python
picam.set_controls({
    "ExposureTime": 500000,   # increase if too dark, decrease if too bright
    "AnalogueGain": 8.0,      # increase if too dark
})
```

Use the same values in `Scanner.py` so both scripts see identical brightness.

---

## Scanner.py - Main Scanner

### Running the scanner

```bash
python3 Scanner.py
```

Scans all 6 faces in the fixed sequence **U → R → F → D → L → B**. Rotate
the cube between each face. After all 6 faces are confirmed the state string
is validated, assembled, and saved to disk.

### Centre colour prompt

Before each face is scanned, an overlay screen appears asking you to declare
the centre colour of that face. This is required because the physical centre
caps are removed for motor attachment, leaving a grey screw that cannot be
colour-classified.

Press the key matching the centre colour of the face you are about to scan:

| Key | Colour |
|-----|--------|
| W | White |
| Y | Yellow |
| R | Red |
| O | Orange |
| B | Blue |
| G | Green |

The declared colour is injected at position 4 (the centre cell) of the face
regardless of what the camera sees there.

### Scanning a face

1. After declaring the centre colour, the scanning window opens showing the
   live camera feed with a 3×3 grid overlay.
2. Position the cube face head-on to the camera within the grid. The grid
   snaps automatically to the cube face using colour detection, and its size
   adjusts dynamically based on how far the cube is from the camera.
3. Press **SPACE** to detect all 9 cells. Coloured dots and letters appear
   on the grid showing what colour each cell was classified as.
4. Review the result shown at the bottom of the screen.
5. Press **ENTER** to confirm and move to the next face, or use one of the
   correction options below if something went wrong.

### Controls

| Key | Action |
|-----|--------|
| SPACE | Detect colours at current grid position |
| ENTER | Confirm face and advance to next |
| R | Retake - clears detection and re-prompts centre colour |
| M | Manual entry - type the face string directly in terminal |
| Q | Quit |

### Manual entry (M key - demo failsafe)

If colour detection produces wrong results for a face, press **M** to enter
the 9-character face string manually via the terminal. The OpenCV window
minimises while you type.

```
Enter 9 colours for face F
Positions: 0 1 2 / 3 4 5 / 6 7 8
Letters:   W Y R O B G
Centre position (4) will be forced to <declared colour>
Enter 9 letters: WGRBOYWRG
```

The declared centre colour is always forced at position 4 regardless of what
is typed, so the state mapping stays consistent. After entry the window
returns to the normal confirmation flow.

### Colour detection pipeline

```
PiCamera v2 frame (1280x960, locked exposure + white balance)
        |
HSV colour mask built from COLOUR_RANGES
        |
Largest colour blob found in centre region of frame
        |
3x3 grid snapped to blob bounding box
        |
Centre of each cell sampled (20x20 pixel average)
        |
BGR -> HSV -> colour letter  (W / Y / R / O / B / G / ?)
        |
Declared centre injected at position 4
        |
9-character face string  e.g.  "WGRBOYYRG"
```

### Colour ranges

Defined in `COLOUR_RANGES` at the top of `Scanner.py`. Edit directly on
the Pi after running `calibrate.py`:

```bash
nano Scanner.py
```

Each entry is `"letter": ([H_min, S_min, V_min], [H_max, S_max, V_max])`.
Red is split into two entries (`R` and `R2`) because it wraps around both
ends of the HSV hue wheel.

### Output files

After a successful scan two files are written to the working directory:

| File | Contents |
|---|---|
| `cube_state.json` | Raw colour data per face — `{"U": ["W","G",...], "R": [...], ...}` |
| `cube_string.txt` | 54-character state string — `"UUUUUUUUURRR...BBB"` |

### State string format

The 54-character string is assembled in face order **U R F D L B**, with
each face reading left-to-right top-to-bottom:

```
Positions:  0- 8  -> U (top)
            9-17  -> R (right)
           18-26  -> F (front)
           27-35  -> D (bottom)
           36-44  -> L (left)
           45-53  -> B (back)

Each face:  0 1 2
            3 4 5   <- position 4 is always the declared centre colour
            6 7 8
```

Characters are face letters (U/R/F/D/L/B), not colour codes. The declared
centre colours are used to build a colour to face letter mapping — for example
if white was declared as the U face then every white sticker on the cube
becomes U in the string.

### Validation

Before saving, the scanner checks:
- All 6 faces are present
- Each face has exactly 9 stickers
- Each of the 6 colours appears exactly 9 times across all faces
- All 6 declared centre colours are unique

If validation fails the scan is rejected and must be redone.

---

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `Device or resource busy` | Another process has the camera | Stop any other script using the camera before running `Scanner.py` |
| `?` cells in face string | Colour outside HSV range | Run `calibrate.py` and update `COLOUR_RANGES` |
| Grid not snapping to cube | Background too similar to cube | Use black backdrop behind and under cube |
| Wrong colour detected | Lighting changed since calibration | Re-run `calibrate.py` |
| Colours look correct but string is wrong | Brightness different between scripts | Make sure `ExposureTime` and `AnalogueGain` match in both files |
| Validation fails after scanning | Incorrect colour detected on one face | Use M key to manually correct the problem face |
