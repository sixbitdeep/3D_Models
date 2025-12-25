# FreeCAD Macro: Sliding Window Camera Mount (Clip Style)
# Adds: Guy-wire string holes (2 top IN THE LIP + 2 bottom) to reduce wind shake
# Adds (Option B): Dedicated long underside damping slot (wide, centered) to accept TPU/foam strip
# Top holes: drilled through clip lip in Z (guaranteed through)
# No gussets (keeps window-closing clearance)
# Fillet off by default to avoid OCC segfaults

import FreeCAD as App
import Part
from FreeCAD import Vector

# ============== PARAMETERS (adjust these) ==============
INSIDE_HEIGHT = 39.20
INSIDE_THICKNESS = 4.0

INSIDE_FORWARD_SHIFT = 3.8
INSIDE_TOP_SEGMENT_HEIGHT = 8.0
INSIDE_CONNECT_HEIGHT = 4.0

BACK_TRIM_ENABLE = True
BACK_TRIM_TO_X = INSIDE_FORWARD_SHIFT
BACK_TRIM_EXTRA = 0.0
BACK_TRIM_KEEP_BELOW_CONNECT = True

LIP_LENGTH = 16.35
LIP_THICKNESS = 4.0

HORIZONTAL_LENGTH = 86.0  # original print 102.0 reduced 16mm
HORIZONTAL_THICKNESS = 5.0

OUTSIDE_LENGTH = 70.0
OUTSIDE_THICKNESS = 5.0

WIDTH = 54.0

HOLE_DIAMETER = 6.35
HOLE_OFFSET_FROM_BOTTOM = 20.0

SECOND_HOLE = True
HOLE_SPACING_Y = 35.35
HOLE_2_OFFSET = 3.5
HOLE_PAIR_SHIFT = -1.75
MIN_EDGE_MARGIN_Y = 2.5

CENTER_HOLES_Z = True

FILLET_RADIUS = 0.0
REFINE_AFTER_BOOLEANS = True

# --------- COMPRESSION ZONE (CUT-IN POCKET) ---------
POCKET_ENABLE_TOP = True
POCKET_ENABLE_BOTTOM = False

POCKET_X_START = 2.0
POCKET_LENGTH = 24.0
POCKET_Y_MARGIN = 4.0

POCKET_DEPTH = 1.8
MIN_FLOOR_THICKNESS = 1.2
# ----------------------------------------------------

# --------- UNDERSIDE DAMPING SLOT (LONG CUT) ---------
# Option B: Dedicated long underside slot (wide, centered) to accept TPU/foam strip
UNDERCUT_ENABLE = True
UNDERCUT_X_START = 6.0
UNDERCUT_LENGTH = 60.0
UNDERCUT_Y_MARGIN = 3.0
UNDERCUT_DEPTH = 1.2
UNDERCUT_MIN_FLOOR = 2.0
# -----------------------------------------------------

# --------- GUY-WIRE HOLES (string/cord brace) ---------
GUY_ENABLE = True

GUY_HOLE_DIAMETER = 4.0
GUY_EDGE_MARGIN_Y = 4.0

# Top holes in the LIP (drill down through Z)
GUY_TOP_IN_LIP = True
GUY_TOP_LIP_X_FRAC = 0.55   # 0..1 along lip length (0 = near inside wall, 1 = near lip tip)

# Bottom holes placement: "outside_arm" or "horizontal"
GUY_BOTTOM_MODE = "outside_arm"

# If outside_arm: hole goes through outside arm thickness (X direction)
GUY_BOTTOM_Z_FRAC = 0.70     # 0..1 along outside arm height (0=bottom, 1=top)

# If horizontal: hole goes through horizontal thickness (Z direction)
GUY_BOTTOM_X_BACKOFF = 10.0  # mm back from outside arm toward inside if using horizontal mode
# -----------------------------------------------------

def clamp(val, lo, hi):
    return max(lo, min(hi, val))

def refine_if_enabled(shape):
    if not REFINE_AFTER_BOOLEANS:
        return shape
    try:
        return shape.removeSplitter()
    except Exception:
        return shape

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
            return shape
        return shape.makeFillet(radius, edges)
    except Exception:
        return shape

def guy_y_positions():
    r = GUY_HOLE_DIAMETER / 2.0
    min_y = r + GUY_EDGE_MARGIN_Y
    max_y = WIDTH - r - GUY_EDGE_MARGIN_Y
    if min_y >= max_y:
        raise ValueError("Guy-hole Y margins too large for WIDTH.")
    return (min_y, max_y)

def cut_top_guy_holes_in_lip(bracket):
    # Two holes through the lip thickness (drill along +Z)
    r = GUY_HOLE_DIAMETER / 2.0
    yL, yR = guy_y_positions()

    # Lip is located at:
    # x = INSIDE_THICKNESS .. INSIDE_THICKNESS + LIP_LENGTH
    # y = 0 .. WIDTH
    # z = HORIZONTAL_THICKNESS + INSIDE_HEIGHT - LIP_THICKNESS .. +INSIDE_HEIGHT
    x_lip_start = INSIDE_THICKNESS
    x_lip = x_lip_start + clamp(GUY_TOP_LIP_X_FRAC, 0.10, 0.90) * LIP_LENGTH

    z_lip_bottom = HORIZONTAL_THICKNESS + INSIDE_HEIGHT - LIP_THICKNESS
    z_lip_center = z_lip_bottom + (LIP_THICKNESS / 2.0)

    # Drill cylinder along Z, long enough to clear the lip
    drill_h = LIP_THICKNESS + 2.0

    holes = [
        Part.makeCylinder(r, drill_h, Vector(x_lip, yL, z_lip_bottom - 1.0), Vector(0, 0, 1)),
        Part.makeCylinder(r, drill_h, Vector(x_lip, yR, z_lip_bottom - 1.0), Vector(0, 0, 1)),
    ]

    for h in holes:
        bracket = bracket.cut(h)
    return refine_if_enabled(bracket)

def cut_bottom_guy_holes(bracket):
    r = GUY_HOLE_DIAMETER / 2.0
    yL, yR = guy_y_positions()

    if GUY_BOTTOM_MODE == "outside_arm":
        z0 = -OUTSIDE_LENGTH + HORIZONTAL_THICKNESS
        z_bottom_hole = z0 + clamp(GUY_BOTTOM_Z_FRAC, 0.10, 0.95) * OUTSIDE_LENGTH

        xh = HORIZONTAL_LENGTH - OUTSIDE_THICKNESS - 0.5
        holes = [
            Part.makeCylinder(r, OUTSIDE_THICKNESS + 2.0, Vector(xh, yL, z_bottom_hole), Vector(1, 0, 0)),
            Part.makeCylinder(r, OUTSIDE_THICKNESS + 2.0, Vector(xh, yR, z_bottom_hole), Vector(1, 0, 0)),
        ]
        for h in holes:
            bracket = bracket.cut(h)
        return refine_if_enabled(bracket)

    if GUY_BOTTOM_MODE == "horizontal":
        xh = HORIZONTAL_LENGTH - OUTSIDE_THICKNESS - clamp(GUY_BOTTOM_X_BACKOFF, 6.0, 40.0)
        holes = [
            Part.makeCylinder(r, HORIZONTAL_THICKNESS + 2.0, Vector(xh, yL, -1.0), Vector(0, 0, 1)),
            Part.makeCylinder(r, HORIZONTAL_THICKNESS + 2.0, Vector(xh, yR, -1.0), Vector(0, 0, 1)),
        ]
        for h in holes:
            bracket = bracket.cut(h)
        return refine_if_enabled(bracket)

    raise ValueError('GUY_BOTTOM_MODE must be "outside_arm" or "horizontal".')

def create_camera_mount():
    doc = App.ActiveDocument
    if doc is None:
        doc = App.newDocument("CameraMount")

    top_h = clamp(INSIDE_TOP_SEGMENT_HEIGHT, 1.0, INSIDE_HEIGHT)
    bot_h = max(0.1, INSIDE_HEIGHT - top_h)

    inside_bottom = Part.makeBox(INSIDE_THICKNESS, WIDTH, bot_h)
    inside_bottom.translate(Vector(INSIDE_FORWARD_SHIFT, 0, HORIZONTAL_THICKNESS))

    inside_top = Part.makeBox(INSIDE_THICKNESS, WIDTH, top_h)
    inside_top.translate(Vector(0.0, 0, HORIZONTAL_THICKNESS + bot_h))

    conn_h = clamp(INSIDE_CONNECT_HEIGHT, 0.5, top_h)
    connector = Part.makeBox(INSIDE_FORWARD_SHIFT + INSIDE_THICKNESS, WIDTH, conn_h)
    connector.translate(Vector(0.0, 0, HORIZONTAL_THICKNESS + bot_h - conn_h))

    inside_arm = inside_bottom.fuse(inside_top).fuse(connector)
    inside_arm = refine_if_enabled(inside_arm)

    if BACK_TRIM_ENABLE:
        trim_to_x = BACK_TRIM_TO_X - BACK_TRIM_EXTRA
        if BACK_TRIM_KEEP_BELOW_CONNECT:
            z_top_trim = HORIZONTAL_THICKNESS + bot_h - conn_h
        else:
            z_top_trim = HORIZONTAL_THICKNESS + bot_h

        trim_box = Part.makeBox(400.0, WIDTH + 40.0, z_top_trim + 80.0)
        trim_box.translate(Vector(-400.0, -20.0, -80.0))
        trim_box.translate(Vector(trim_to_x, 0.0, 0.0))

        inside_arm = inside_arm.cut(trim_box)
        inside_arm = refine_if_enabled(inside_arm)

    clip_lip = Part.makeBox(LIP_LENGTH, WIDTH, LIP_THICKNESS)
    clip_lip.translate(Vector(
        INSIDE_THICKNESS,
        0,
        HORIZONTAL_THICKNESS + INSIDE_HEIGHT - LIP_THICKNESS
    ))

    horizontal_start_x = INSIDE_FORWARD_SHIFT
    horizontal_actual_length = HORIZONTAL_LENGTH - INSIDE_FORWARD_SHIFT
    if horizontal_actual_length <= 5.0:
        raise ValueError("HORIZONTAL_LENGTH too small vs INSIDE_FORWARD_SHIFT.")

    horizontal = Part.makeBox(horizontal_actual_length, WIDTH, HORIZONTAL_THICKNESS)
    horizontal.translate(Vector(horizontal_start_x, 0, 0))

    outside_arm = Part.makeBox(OUTSIDE_THICKNESS, WIDTH, OUTSIDE_LENGTH)
    outside_arm.translate(Vector(
        HORIZONTAL_LENGTH - OUTSIDE_THICKNESS,
        0,
        -OUTSIDE_LENGTH + HORIZONTAL_THICKNESS
    ))

    bracket = inside_arm.fuse(horizontal).fuse(outside_arm).fuse(clip_lip)
    bracket = refine_if_enabled(bracket)

    # Compression pockets
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
        bracket = refine_if_enabled(bracket)

    if POCKET_ENABLE_BOTTOM:
        bottom_pocket = Part.makeBox(pocket_len, pocket_w, depth)
        bottom_pocket.translate(Vector(x0, y0, 0.0))
        bracket = bracket.cut(bottom_pocket)
        bracket = refine_if_enabled(bracket)

    # Option B: Dedicated underside damping slot (long, wide cut)
    if UNDERCUT_ENABLE:
        ux0 = clamp(UNDERCUT_X_START, 0.0, max(0.0, HORIZONTAL_LENGTH - 2.0))
        ux1 = clamp(ux0 + UNDERCUT_LENGTH, ux0 + 2.0, HORIZONTAL_LENGTH)
        ulen = ux1 - ux0

        uy0 = clamp(UNDERCUT_Y_MARGIN, 0.0, WIDTH / 2.0)
        uw = max(1.0, WIDTH - 2.0 * uy0)

        umax_depth = max(0.1, HORIZONTAL_THICKNESS - UNDERCUT_MIN_FLOOR)
        udepth = clamp(UNDERCUT_DEPTH, 0.1, umax_depth)

        undercut = Part.makeBox(ulen, uw, udepth)
        undercut.translate(Vector(ux0, uy0, 0.0))  # bottom face
        bracket = bracket.cut(undercut)
        bracket = refine_if_enabled(bracket)

    # Camera mount holes (your original pair)
    xh = HORIZONTAL_LENGTH - OUTSIDE_THICKNESS - 1
    hole_offset = (OUTSIDE_LENGTH / 2.0) if CENTER_HOLES_Z else HOLE_OFFSET_FROM_BOTTOM
    zh = -OUTSIDE_LENGTH + HORIZONTAL_THICKNESS + hole_offset

    y_center = WIDTH / 2.0
    y1 = y_center + HOLE_PAIR_SHIFT - (HOLE_SPACING_Y / 2.0)
    y2 = y_center + HOLE_PAIR_SHIFT + (HOLE_SPACING_Y / 2.0) + HOLE_2_OFFSET

    hole_r = HOLE_DIAMETER / 2.0
    min_y = hole_r + MIN_EDGE_MARGIN_Y
    max_y = WIDTH - hole_r - MIN_EDGE_MARGIN_Y

    if y1 < min_y:
        raise ValueError(f"Hole 1 too close to edge (y1={y1:.2f}, min={min_y:.2f}).")
    if SECOND_HOLE and y2 > max_y:
        raise ValueError(f"Hole 2 too close to edge (y2={y2:.2f}, max={max_y:.2f}).")

    holes = [Part.makeCylinder(hole_r, OUTSIDE_THICKNESS + 2, Vector(xh, y1, zh), Vector(1, 0, 0))]
    if SECOND_HOLE:
        holes.append(Part.makeCylinder(hole_r, OUTSIDE_THICKNESS + 2, Vector(xh, y2, zh), Vector(1, 0, 0)))

    for h in holes:
        bracket = bracket.cut(h)
    bracket = refine_if_enabled(bracket)

    # Guy-wire holes
    if GUY_ENABLE and GUY_TOP_IN_LIP:
        bracket = cut_top_guy_holes_in_lip(bracket)
    if GUY_ENABLE:
        bracket = cut_bottom_guy_holes(bracket)

    bracket = safe_fillet(bracket, FILLET_RADIUS)

    mount = doc.addObject("Part::Feature", "WindowCameraMount")
    mount.Shape = bracket
    doc.recompute()

    if App.GuiUp:
        import FreeCADGui
        FreeCADGui.ActiveDocument.ActiveView.viewIsometric()
        FreeCADGui.ActiveDocument.ActiveView.fitAll()

    print("WindowCameraMount created with underside damping slot + TOP lip guy-wire holes!")
    print(f"  Undercut: enable={UNDERCUT_ENABLE}, depth={UNDERCUT_DEPTH}mm, min_floor={UNDERCUT_MIN_FLOOR}mm")
    print(f"  Top holes: lip Z-drill, d={GUY_HOLE_DIAMETER}mm, x_frac={GUY_TOP_LIP_X_FRAC}")
    print(f"  Bottom holes: mode={GUY_BOTTOM_MODE}, d={GUY_HOLE_DIAMETER}mm")
    return mount

create_camera_mount()

