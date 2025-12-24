# FreeCAD Macro: TPU Strips Only (Side-by-side preview option)
# Creates two TPU solids:
#  1) TPU pocket insert
#  2) TPU long damping strip
#
# PREVIEW_MODE_SIDE_BY_SIDE = True moves them next to each other for viewing/export.

import FreeCAD as App
import Part
from FreeCAD import Vector

# ====== GEOMETRY FROM YOUR MOUNT MACRO (must match) ======
INSIDE_FORWARD_SHIFT = 3.8
HORIZONTAL_LENGTH = 102.0
HORIZONTAL_THICKNESS = 4.0
WIDTH = 54.0

# Pocket params (your macro)
POCKET_X_START = 2.0
POCKET_LENGTH = 24.0
POCKET_Y_MARGIN = 4.0
POCKET_DEPTH = 1.8

# ====== TPU DIMENSIONS ======
TPU_POCKET_THICKNESS = 1.6

TPU_STRIP_LENGTH = 90.0
TPU_STRIP_WIDTH = 20.0
TPU_STRIP_THICKNESS = 1.0

CENTER_STRIP_IN_X = True
CENTER_STRIP_IN_Y = True

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

    z_floor = HORIZONTAL_THICKNESS - POCKET_DEPTH
    pad = Part.makeBox(pocket_len, pocket_w, t)
    pad.translate(Vector(POCKET_X_START, POCKET_Y_MARGIN, z_floor))
    return pad, pocket_len, pocket_w, t

def make_tpu_long_under_strip_shape():
    horizontal_actual_length = HORIZONTAL_LENGTH - INSIDE_FORWARD_SHIFT
    if horizontal_actual_length <= 0:
        raise ValueError("HORIZONTAL_LENGTH must be > INSIDE_FORWARD_SHIFT.")

    strip_len = clamp(TPU_STRIP_LENGTH, 5.0, horizontal_actual_length)
    strip_w = clamp(TPU_STRIP_WIDTH, 5.0, WIDTH)
    strip_t = clamp(TPU_STRIP_THICKNESS, 0.2, 5.0)

    if CENTER_STRIP_IN_X:
        x = INSIDE_FORWARD_SHIFT + (horizontal_actual_length - strip_len) / 2.0
    else:
        x = INSIDE_FORWARD_SHIFT + 2.0

    if CENTER_STRIP_IN_Y:
        y = (WIDTH - strip_w) / 2.0
    else:
        y = 2.0

    z = -strip_t

    strip = Part.makeBox(strip_len, strip_w, strip_t)
    strip.translate(Vector(x, y, z))
    return strip, strip_len, strip_w, strip_t

def place_side_by_side(pad_shape, strip_shape, pad_dims, strip_dims):
    pad_len, pad_w, pad_t = pad_dims
    strip_len, strip_w, strip_t = strip_dims

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
    strip_shape, strip_len, strip_w, strip_t = make_tpu_long_under_strip_shape()

    if PREVIEW_MODE_SIDE_BY_SIDE:
        pad_shape, strip_shape = place_side_by_side(
            pad_shape, strip_shape,
            (pad_len, pad_w, pad_t),
            (strip_len, strip_w, strip_t)
        )

    tpu1 = doc.addObject("Part::Feature", "TPU_Pocket_Insert")
    tpu1.Shape = pad_shape

    tpu2 = doc.addObject("Part::Feature", "TPU_Long_Strip_Under")
    tpu2.Shape = strip_shape

    doc.recompute()

    if App.GuiUp:
        import FreeCADGui
        FreeCADGui.ActiveDocument.ActiveView.viewIsometric()
        FreeCADGui.ActiveDocument.ActiveView.fitAll()

    print("TPU strips created:")
    print(f"  TPU_Pocket_Insert: {pad_len:.2f} x {pad_w:.2f} x {pad_t:.2f} mm")
    print(f"  TPU_Long_Strip_Under: {strip_len:.2f} x {strip_w:.2f} x {strip_t:.2f} mm")
    print(f"  Preview side-by-side: {PREVIEW_MODE_SIDE_BY_SIDE}")

main()
