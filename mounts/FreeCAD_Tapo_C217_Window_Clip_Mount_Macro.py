# FreeCAD Macro: Sliding Window Camera Mount (Clip Style)
# House window use: "compression zone" is a CUT-IN POCKET for gasket/foam tape.

import FreeCAD as App
import Part
from FreeCAD import Vector

# ============== PARAMETERS (adjust these) ==============
INSIDE_HEIGHT = 39.20
INSIDE_THICKNESS = 3.0

# Move ONLY the lower inside wall forward, while keeping the top clip area in place
INSIDE_FORWARD_SHIFT = 3.8
INSIDE_TOP_SEGMENT_HEIGHT = 8.0
INSIDE_CONNECT_HEIGHT = 4.0

# New: trim the "back piece" near the bottom (removes material behind the shifted wall)
BACK_TRIM_ENABLE = True
BACK_TRIM_TO_X = INSIDE_FORWARD_SHIFT   # trim anything with x < this (flush to shifted lower wall back)
BACK_TRIM_EXTRA = 0.0                  # set to 0.2 if you want extra clearance
BACK_TRIM_KEEP_BELOW_CONNECT = True    # keep the connector area; only trim below it

LIP_LENGTH = 16.35
LIP_THICKNESS = 2.0

HORIZONTAL_LENGTH = 105.0
HORIZONTAL_THICKNESS = 4.0

OUTSIDE_LENGTH = 70.0
OUTSIDE_THICKNESS = 4.0

WIDTH = 54.0  # Widened from 47.0 to accommodate shifted hole 2 with offset

HOLE_DIAMETER = 6.35
HOLE_OFFSET_FROM_BOTTOM = 20.0

SECOND_HOLE = True
HOLE_SPACING_Y = 35.35
HOLE_2_OFFSET = 3.5  # Additional offset for hole 2 toward outer edge (+Y direction)
HOLE_PAIR_SHIFT = -1.75  # Shifts both holes together toward +Y edge (use negative to shift toward Y=0)
MIN_EDGE_MARGIN_Y = 2.5

CENTER_HOLES_Z = True

# Set to 0.0 while iterating if you still see instability
FILLET_RADIUS = 3.0

# --------- COMPRESSION ZONE (CUT-IN POCKET) ---------
POCKET_ENABLE_TOP = True
POCKET_ENABLE_BOTTOM = False

POCKET_X_START = 2.0
POCKET_LENGTH = 24.0
POCKET_Y_MARGIN = 4.0

POCKET_DEPTH = 1.8
MIN_FLOOR_THICKNESS = 1.2
# ----------------------------------------------------

def clamp(val, lo, hi):
    return max(lo, min(hi, val))

def safe_fillet(shape, radius):
    if radius <= 0:
        return shape

    try:
        shape = shape.removeSplitter()
    except Exception:
        pass

    try:
        edges = []
        for e in shape.Edges:
            bb = e.BoundBox
            if bb.XLength < 0.25 and bb.YLength < 0.25 and bb.ZLength < 0.25:
                continue
            if max(bb.XLength, bb.YLength, bb.ZLength) >= 15.0:
                edges.append(e)

        if not edges:
            print("Note: No safe edges detected for fillet; skipping fillet")
            return shape

        return shape.makeFillet(radius, edges)
    except Exception:
        print("Note: Fillet failed; skipping fillet")
        return shape

def create_camera_mount():
    doc = App.ActiveDocument
    if doc is None:
        doc = App.newDocument("CameraMount")

    # ---------------- Inside wall as TWO segments ----------------
    top_h = clamp(INSIDE_TOP_SEGMENT_HEIGHT, 1.0, INSIDE_HEIGHT)
    bot_h = max(0.1, INSIDE_HEIGHT - top_h)

    # Bottom segment: shifted forward
    inside_bottom = Part.makeBox(INSIDE_THICKNESS, WIDTH, bot_h)
    inside_bottom.translate(Vector(
        INSIDE_FORWARD_SHIFT,
        0,
        HORIZONTAL_THICKNESS
    ))

    # Top segment: stays in original position (X=0)
    inside_top = Part.makeBox(INSIDE_THICKNESS, WIDTH, top_h)
    inside_top.translate(Vector(
        0.0,
        0,
        HORIZONTAL_THICKNESS + bot_h
    ))

    # Connector block (step bridge)
    conn_h = clamp(INSIDE_CONNECT_HEIGHT, 0.5, top_h)
    connector = Part.makeBox(INSIDE_FORWARD_SHIFT + INSIDE_THICKNESS, WIDTH, conn_h)
    connector.translate(Vector(
        0.0,
        0,
        HORIZONTAL_THICKNESS + bot_h - conn_h
    ))

    inside_arm = inside_bottom.fuse(inside_top).fuse(connector)

    # Trim the back piece near the bottom: remove anything behind the shifted wall
    if BACK_TRIM_ENABLE:
        trim_to_x = BACK_TRIM_TO_X - BACK_TRIM_EXTRA

        # Only trim up to just below the connector (so the connector remains)
        if BACK_TRIM_KEEP_BELOW_CONNECT:
            z_top = HORIZONTAL_THICKNESS + bot_h - conn_h
        else:
            z_top = HORIZONTAL_THICKNESS + bot_h

        # Cutter covers x < trim_to_x, for low Z only
        trim_box = Part.makeBox(
            400.0,            # big X span
            WIDTH + 40.0,     # big Y span
            z_top + 80.0      # cover from below up to z_top
        )
        trim_box.translate(Vector(
            -400.0,   # starts far left in X
            -20.0,
            -80.0
        ))

        # Shift cutter so its "right face" lands at trim_to_x
        trim_box.translate(Vector(trim_to_x, 0.0, 0.0))

        inside_arm = inside_arm.cut(trim_box)
    # ------------------------------------------------------------

    # Clip lip at top of inside arm (KEEP ORIGINAL POSITION)
    clip_lip = Part.makeBox(LIP_LENGTH, WIDTH, LIP_THICKNESS)
    clip_lip.translate(Vector(
        INSIDE_THICKNESS,
        0,
        HORIZONTAL_THICKNESS + INSIDE_HEIGHT - LIP_THICKNESS
    ))

    # Horizontal arm - starts at INSIDE_FORWARD_SHIFT to align flush with lower wall
    horizontal_start_x = INSIDE_FORWARD_SHIFT
    horizontal_actual_length = HORIZONTAL_LENGTH - INSIDE_FORWARD_SHIFT
    horizontal = Part.makeBox(horizontal_actual_length, WIDTH, HORIZONTAL_THICKNESS)
    horizontal.translate(Vector(horizontal_start_x, 0, 0))

    # Outside vertical arm
    outside_arm = Part.makeBox(OUTSIDE_THICKNESS, WIDTH, OUTSIDE_LENGTH)
    outside_arm.translate(Vector(
        HORIZONTAL_LENGTH - OUTSIDE_THICKNESS,
        0,
        -OUTSIDE_LENGTH + HORIZONTAL_THICKNESS
    ))

    # Fuse base bracket
    bracket = inside_arm.fuse(horizontal).fuse(outside_arm).fuse(clip_lip)

    # -------- COMPRESSION POCKET CUTS --------
    x0 = clamp(POCKET_X_START, 0.0, max(0.0, HORIZONTAL_LENGTH - 1.0))
    x1 = clamp(x0 + POCKET_LENGTH, x0 + 1.0, HORIZONTAL_LENGTH)
    pocket_len = x1 - x0

    y0 = clamp(POCKET_Y_MARGIN, 0.0, WIDTH / 2.0)
    pocket_w = max(1.0, WIDTH - 2.0 * y0)

    max_depth_allowed = max(0.1, HORIZONTAL_THICKNESS - MIN_FLOOR_THICKNESS)
    depth = clamp(POCKET_DEPTH, 0.1, max_depth_allowed)

    if POCKET_ENABLE_TOP:
        top_pocket = Part.makeBox(pocket_len, pocket_w, depth)
        top_pocket.translate(Vector(x0, y0, HORIZONTAL_THICKNESS - depth))
        bracket = bracket.cut(top_pocket)

    if POCKET_ENABLE_BOTTOM:
        bottom_pocket = Part.makeBox(pocket_len, pocket_w, depth)
        bottom_pocket.translate(Vector(x0, y0, 0.0))
        bracket = bracket.cut(bottom_pocket)
    # ----------------------------------------

    # -------- HOLE PLACEMENT --------
    xh = HORIZONTAL_LENGTH - OUTSIDE_THICKNESS - 1
    hole_offset = (OUTSIDE_LENGTH / 2.0) if CENTER_HOLES_Z else HOLE_OFFSET_FROM_BOTTOM
    zh = -OUTSIDE_LENGTH + HORIZONTAL_THICKNESS + hole_offset

    y_center = WIDTH / 2.0
    y1 = y_center + HOLE_PAIR_SHIFT - (HOLE_SPACING_Y / 2.0)
    y2 = y_center + HOLE_PAIR_SHIFT + (HOLE_SPACING_Y / 2.0) + HOLE_2_OFFSET  # Shifted toward outer edge

    hole_r = HOLE_DIAMETER / 2.0
    min_y = hole_r + MIN_EDGE_MARGIN_Y
    max_y = WIDTH - hole_r - MIN_EDGE_MARGIN_Y

    # Validate hole 1 position
    if y1 < min_y:
        raise ValueError(
            f"Hole 1 at y1={y1:.2f} is too close to edge (min={min_y:.2f}). "
            f"Increase WIDTH or reduce HOLE_SPACING_Y."
        )

    # Validate hole 2 position (with offset)
    if SECOND_HOLE and y2 > max_y:
        raise ValueError(
            f"Hole 2 at y2={y2:.2f} is too close to edge (max={max_y:.2f}). "
            f"Increase WIDTH or reduce HOLE_2_OFFSET."
        )

    holes = []
    holes.append(Part.makeCylinder(hole_r, OUTSIDE_THICKNESS + 2, Vector(xh, y1, zh), Vector(1, 0, 0)))
    if SECOND_HOLE:
        holes.append(Part.makeCylinder(hole_r, OUTSIDE_THICKNESS + 2, Vector(xh, y2, zh), Vector(1, 0, 0)))

    for h in holes:
        bracket = bracket.cut(h)
    # ----------------------------------------

    bracket = safe_fillet(bracket, FILLET_RADIUS)

    mount = doc.addObject("Part::Feature", "WindowCameraMount")
    mount.Shape = bracket
    doc.recompute()

    if App.GuiUp:
        import FreeCADGui
        FreeCADGui.ActiveDocument.ActiveView.viewIsometric()
        FreeCADGui.ActiveDocument.ActiveView.fitAll()

    print("Clip-style camera mount created!")
    print(f"  WIDTH: {WIDTH}mm")
    print(f"  Lower inside wall forward shift: {INSIDE_FORWARD_SHIFT}mm")
    print(f"  Horizontal arm starts at X={INSIDE_FORWARD_SHIFT}mm (flush with lower wall)")
    print(f"  Hole 1 at Y={y1:.2f}mm, Hole 2 at Y={y2:.2f}mm")
    print(f"  Pair shift: {HOLE_PAIR_SHIFT}mm, Hole 2 offset: +{HOLE_2_OFFSET}mm")
    if BACK_TRIM_ENABLE:
        print(f"  Back trim: remove x < {BACK_TRIM_TO_X - BACK_TRIM_EXTRA:.2f} (low section only)")
    return mount

create_camera_mount()
