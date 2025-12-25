# FreeCAD Macro: TPU Strips Only (Side-by-side preview option)
# Updated to match the mount macro with Option B underside damping slot.
#
# Creates two TPU solids:
#  1) TPU pocket insert (for the TOP pocket)
#  2) TPU long damping strip (for the UNDERSIDE slot)
#
# PREVIEW_MODE_SIDE_BY_SIDE = True moves them next to each other for viewing/export.

import FreeCAD as App
import Part
from FreeCAD import Vector

# ====== GEOMETRY FROM YOUR MOUNT MACRO (must match) ======
INSIDE_FORWARD_SHIFT = 3.8
HORIZONTAL_LENGTH = 86.0
HORIZONTAL_THICKNESS = 5.0
WIDTH = 54.0

# ====== TOP POCKET PARAMS (from mount macro) ======
POCKET_X_START = 2.0
POCKET_LENGTH = 24.0
POCKET_Y_MARGIN = 4.0
POCKET_DEPTH = 1.8

# ====== OPTION B UNDERSIDE SLOT PARAMS (from mount macro) ======
UNDERCUT_ENABLE = True
UNDERCUT_X_START = 6.0
UNDERCUT_LENGTH = 60.0
UNDERCUT_Y_MARGIN = 3.0
UNDERCUT_DEPTH = 1.2
UNDERCUT_MIN_FLOOR = 2.0  # used on mount; TPU strip ignores this except for sanity checks

# ====== TPU DIMENSIONS ======
# Pocket insert thickness should be <= POCKET_DEPTH
TPU_POCKET_THICKNESS = 1.6

# Underside strip thickness should be <= UNDERCUT_DEPTH
TPU_UNDERCUT_STRIP_THICKNESS = 1.0

# If True, TPU strip matches the underside slot length/width automatically.
TPU_UNDERCUT_MATCH_SLOT = True

# If TPU_UNDERCUT_MATCH_SLOT is False, these are used (and clamped to fit).
TPU_STRIP_LENGTH = 60.0
TPU_STRIP_WIDTH = 30.0

# Centering controls (only applies when not in preview layout)
CENTER_STRIP_IN_X = False
CENTER_STRIP_IN_Y = False

# ====== PREVIEW / LAYOUT CONTROLS ======
PREVIEW_MODE_SIDE_BY_SIDE = True   # set False to place in "real" mount positions
PREVIEW_GAP = 10.0                 # mm gap between parts in preview mode
PREVIEW_PAD = 5.0                  # extra spacing to avoid touching

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def ensure_doc():
    doc = App.ActiveDocument
    if doc is None:
        doc = App.newDocument("TPU_Strips")
    return doc

def make_tpu_pocket_insert_shape():
    pocket_len = clamp(POCKET_LENGTH, 1.0, HORIZONTAL_LENGTH)
    pocket_w = clamp(WIDTH - 2.0 * POCKET_Y_MARGIN, 1.0, WIDTH)
    t = clamp(TPU_POCKET_THICKNESS, 0.2, POCKET_DEPTH)

    # This places it into the TOP pocket area (same as your old macro)
    z_floor = HORIZONTAL_THICKNESS - POCKET_DEPTH
    pad = Part.makeBox(pocket_len, pocket_w, t)
    pad.translate(Vector(POCKET_X_START, POCKET_Y_MARGIN, z_floor))
    return pad, pocket_len, pocket_w, t

def make_tpu_undercut_strip_shape():
    if not UNDERCUT_ENABLE:
        raise ValueError("UNDERCUT_ENABLE is False in this TPU macro. Enable it to generate the underside strip.")

    horizontal_actual_length = HORIZONTAL_LENGTH - INSIDE_FORWARD_SHIFT
    if horizontal_actual_length <= 0:
        raise ValueError("HORIZONTAL_LENGTH must be > INSIDE_FORWARD_SHIFT.")

    # Match slot dims by default
    if TPU_UNDERCUT_MATCH_SLOT:
        strip_len = clamp(UNDERCUT_LENGTH, 5.0, horizontal_actual_length)
        strip_w = clamp(WIDTH - 2.0 * UNDERCUT_Y_MARGIN, 5.0, WIDTH)
    else:
        strip_len = clamp(TPU_STRIP_LENGTH, 5.0, horizontal_actual_length)
        strip_w = clamp(TPU_STRIP_WIDTH, 5.0, WIDTH)

    strip_t = clamp(TPU_UNDERCUT_STRIP_THICKNESS, 0.2, UNDERCUT_DEPTH)

    # Place strip into the underside slot region:
    # Slot is cut from z=0 upward by UNDERCUT_DEPTH, starting at (UNDERCUT_X_START, UNDERCUT_Y_MARGIN, 0)
    if CENTER_STRIP_IN_X:
        # Center within the horizontal run (not typical for matching slot)
        x = INSIDE_FORWARD_SHIFT + (horizontal_actual_length - strip_len) / 2.0
    else:
        x = clamp(UNDERCUT_X_START, 0.0, HORIZONTAL_LENGTH - strip_len)

    if CENTER_STRIP_IN_Y:
        y = (WIDTH - strip_w) / 2.0
    else:
        y = clamp(UNDERCUT_Y_MARGIN, 0.0, WIDTH - strip_w)

    # Put it flush to the underside (z=0..strip_t). This makes it easy to export/print as a "pad".
    z = 0.0

    strip = Part.makeBox(strip_len, strip_w, strip_t)
    strip.translate(Vector(x, y, z))
    return strip, strip_len, strip_w, strip_t

def place_side_by_side(pad_shape, strip_shape):
    # Move both shapes so their minima start near origin (clean layout)
    pad_bb = pad_shape.BoundBox
    strip_bb = strip_shape.BoundBox

    pad_shape.translate(Vector(-pad_bb.XMin, -pad_bb.YMin, -pad_bb.ZMin))
    strip_shape.translate(Vector(-strip_bb.XMin, -strip_bb.YMin, -strip_bb.ZMin))

    # Place strip to the right of pad with a gap
    pad_bb2 = pad_shape.BoundBox
    dx = pad_bb2.XMax + PREVIEW_GAP + PREVIEW_PAD
    strip_shape.translate(Vector(dx, 0, 0))

    return pad_shape, strip_shape

def main():
    doc = ensure_doc()

    pad_shape, pad_len, pad_w, pad_t = make_tpu_pocket_insert_shape()
    strip_shape, strip_len, strip_w, strip_t = make_tpu_undercut_strip_shape()

    if PREVIEW_MODE_SIDE_BY_SIDE:
        pad_shape, strip_shape = place_side_by_side(pad_shape, strip_shape)

    tpu1 = doc.addObject("Part::Feature", "TPU_Pocket_Insert")
    tpu1.Shape = pad_shape

    tpu2 = doc.addObject("Part::Feature", "TPU_Undercut_Strip")
    tpu2.Shape = strip_shape

    doc.recompute()

    if App.GuiUp:
        import FreeCADGui
        FreeCADGui.ActiveDocument.ActiveView.viewIsometric()
        FreeCADGui.ActiveDocument.ActiveView.fitAll()

    print("TPU strips created:")
    print(f"  TPU_Pocket_Insert: {pad_len:.2f} x {pad_w:.2f} x {pad_t:.2f} mm")
    print(f"  TPU_Undercut_Strip: {strip_len:.2f} x {strip_w:.2f} x {strip_t:.2f} mm")
    print(f"  Undercut match slot: {TPU_UNDERCUT_MATCH_SLOT}")
    print(f"  Preview side-by-side: {PREVIEW_MODE_SIDE_BY_SIDE}")

main()
