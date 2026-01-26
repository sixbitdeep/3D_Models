# FreeCAD Macro: 1090MHz_Antenna_Tools.FCMacro
# Creates two printable tools:
# 1) 45-degree angle gauge (solid wedge)
# 2) Length cutting jig with slot + cut notch (default 68.8 mm)
#
# Units: millimeters

import FreeCAD as App
import Part
import math

DOC_NAME = "1090MHz_Tools"

# -------------------------
# Parameters (edit these)
# -------------------------

# Length jig (this is your "69mm height tool" target length)
ELEMENT_LEN = 68.5   # target length for your elements (use 69.0 if you prefer)
JIG_EXTRA   = 20.0   # extra base length beyond the element
JIG_W       = 25.0   # base width (Y)
JIG_H       = 8.0    # base height (Z)
SLOT_W      = 3.0    # slot width (Y) ~= rod_diameter + 0.3
OFFSET_LEFT = 10.0   # where the slot starts from left edge (X)
NOTCH_W     = 1.5    # cut indicator notch width (X)

# Angle gauge (solid wedge)
ANGLE_DEG = 45.0

# Angle gauge dimensions (compact size, independent of element length)
GAUGE_W = 50.0  # X (width) matches your element length
GAUGE_D = JIG_W          # Y (depth)
GAUGE_H = 25.0         # Z (height)

# Keep parts separated in the workspace
SPACING_X = 20.0


def ensure_doc(name: str):
    if name in App.listDocuments():
        doc = App.getDocument(name)
    else:
        doc = App.newDocument(name)
    App.setActiveDocument(doc.Name)
    return doc


def add_part(doc, name: str, shape: Part.Shape, placement_vec=None):
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    if placement_vec:
        obj.Placement.Base = placement_vec
    return obj


def make_angle_gauge_wedge():
    """
    Build a solid wedge by extruding a 2D profile in X-Z, then extrude along Y.
    The sloped face is at ANGLE_DEG from the base.

    Geometry:
    slope run = H / tan(angle)
    We place the slope so it meets the top at x = GAUGE_W and the base at x = GAUGE_W - run.
    """
    if ANGLE_DEG <= 0 or ANGLE_DEG >= 89.9:
        raise ValueError("ANGLE_DEG must be between 0 and 90 (exclusive).")

    angle_rad = math.radians(ANGLE_DEG)
    run = GAUGE_H / math.tan(angle_rad)

    if run >= GAUGE_W:
        raise ValueError(
            f"Angle/height combination makes run={run:.2f}mm >= GAUGE_W={GAUGE_W}mm. "
            "Increase GAUGE_W or reduce GAUGE_H or increase ANGLE_DEG."
        )

    x0 = 0.0
    x1 = GAUGE_W - run
    x2 = GAUGE_W

    # Profile in X-Z plane (z up)
    # Points: (0,0) -> (x1,0) -> (x2,H) -> (0,H)
    p1 = App.Vector(x0, 0, 0)
    p2 = App.Vector(x1, 0, 0)
    p3 = App.Vector(x2, 0, GAUGE_H)
    p4 = App.Vector(x0, 0, GAUGE_H)

    wire = Part.makePolygon([p1, p2, p3, p4, p1])
    face = Part.Face(wire)

    # Extrude along +Y
    solid = face.extrude(App.Vector(0, GAUGE_D, 0))
    return solid


def make_length_jig():
    base_len = ELEMENT_LEN + JIG_EXTRA
    base = Part.makeBox(base_len, JIG_W, JIG_H)

    # Slot (centered in Y)
    slot_y = (JIG_W - SLOT_W) / 2.0
    slot = Part.makeBox(ELEMENT_LEN, SLOT_W, JIG_H + 1.0)
    slot.translate(App.Vector(OFFSET_LEFT, slot_y, 0))
    shaped = base.cut(slot)

    # Cut indicator notch at end of element length
    notch = Part.makeBox(NOTCH_W, JIG_W, JIG_H + 1.0)
    notch.translate(App.Vector(OFFSET_LEFT + ELEMENT_LEN, 0, 0))
    shaped = shaped.cut(notch)

    # Clean up
    shaped = shaped.removeSplitter()
    return shaped


def main():
    doc = ensure_doc(DOC_NAME)

    gauge = make_angle_gauge_wedge()
    jig = make_length_jig()

    add_part(doc, f"AngleGauge_{ANGLE_DEG:.0f}deg_{GAUGE_W:.1f}mmW", gauge, App.Vector(0, 0, 0))
    add_part(doc, f"LengthJig_{ELEMENT_LEN:.1f}mm", jig, App.Vector(GAUGE_W + SPACING_X, 0, 0))

    doc.recompute()

    # Fit view if GUI exists
    try:
        import FreeCADGui as Gui
        Gui.ActiveDocument.ActiveView.viewAxometric()
        Gui.SendMsgToActiveView("ViewFit")
    except Exception:
        pass


main()
