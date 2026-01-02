# FreeCAD macro: Rounded slip-on seatbelt buckle sleeve WITH SIDE OPENING (C-shape)
# Outer box minus inner cavity, fillet outside, then cut a side slot so it can slip on.

import FreeCAD as App
import Part

doc = App.ActiveDocument
if doc is None:
    doc = App.newDocument("Buckle_Sleeve_Cshape")

# Clean reruns
for obj_name in ["BuckleSleeveC", "OuterBox", "InnerCavity", "SlotCutter", "LeadInCutter"]:
    if doc.getObject(obj_name):
        doc.removeObject(obj_name)
doc.recompute()

# -----------------------------
# Parameters (mm)
# -----------------------------
buckle_width = 51.6      # Y direction (left-right), your measured OUTER width
buckle_depth = 33.3      # X direction (front-back), your measured OUTER depth
sleeve_height = 25.0     # Z direction, how tall the sleeve is

clearance = 0.8          # fit tolerance around buckle
wall = 2.5               # wall thickness
corner_radius = 6.0      # outer corner rounding
top_rim_radius = 1.2     # soften top rim (0 disables)

# Bottom lead-in for easy insertion
lead_in = 1.0            # extra clearance at bottom opening
lead_in_height = 6.0     # height of the tapered section

# Side opening (the "gap" that lets it slip on from the side)
slot_width = 14.0        # opening size across the side wall - needs to be wide enough for belt
slot_side = "right"      # "left" or "right" when looking from front (X axis)
slot_relief = 0.0        # 0 = simple slot. Try 0.6 for flexible lips

# -----------------------------
# Derived sizes
# -----------------------------
inner_w = buckle_width + 2 * clearance   # inner cavity width (Y)
inner_d = buckle_depth + 2 * clearance   # inner cavity depth (X)
outer_w = inner_w + 2 * wall             # outer width (Y)
outer_d = inner_d + 2 * wall             # outer depth (X)

# -----------------------------
# Build the sleeve
# -----------------------------

# 1. Create outer box
outer = Part.makeBox(outer_d, outer_w, sleeve_height)

# 2. Create inner cavity (goes through BOTH top and bottom - it's a sleeve!)
inner = Part.makeBox(inner_d, inner_w, sleeve_height + 2.0)
inner.translate(App.Vector(wall, wall, -1.0))

# 3. Cut cavity from outer
shape = outer.cut(inner)

# 4. Lead-in not needed - bottom is fully open for the buckle to function
#    (keeping parameter in case you want to add chamfered edges later)

# 5. Create side slot (C-shape opening)
# The slot runs the full height and cuts through one side wall
if slot_side == "right":
    # Right side = high Y values
    slot_y_start = wall + inner_w - slot_relief
else:
    # Left side = low Y values  
    slot_y_start = -1.0

slot_x_start = (outer_d - slot_width) / 2.0  # center the slot in X

slot_cutter = Part.makeBox(
    slot_width,                    # X dimension
    wall + 2.0 + slot_relief,      # Y dimension (through the wall + extra)
    sleeve_height + 2.0            # Z dimension (full height + extra)
)
slot_cutter.translate(App.Vector(slot_x_start, slot_y_start, -1.0))

shape = shape.cut(slot_cutter)

# 6. Apply fillets to outer vertical edges
edges_to_fillet = []
for edge in shape.Edges:
    # Find vertical edges on the outer perimeter
    if edge.Length > sleeve_height * 0.8:  # roughly full-height edges
        bbox = edge.BoundBox
        # Check if it's a vertical edge (small X and Y extent, large Z extent)
        if bbox.XLength < 0.1 and bbox.YLength < 0.1:
            # Check if it's on the outer perimeter (not inner cavity)
            mid_x = (bbox.XMin + bbox.XMax) / 2
            mid_y = (bbox.YMin + bbox.YMax) / 2
            # Outer corners are at 0, outer_d (X) and 0, outer_w (Y)
            if mid_x < wall/2 or mid_x > outer_d - wall/2:
                if mid_y < wall/2 or mid_y > outer_w - wall/2:
                    edges_to_fillet.append(edge)

if edges_to_fillet and corner_radius > 0:
    try:
        shape = shape.makeFillet(corner_radius, edges_to_fillet)
    except Exception as e:
        print(f"Fillet on vertical edges failed: {e}")
        print("Continuing without vertical fillets...")

# 7. Apply fillet to top rim
if top_rim_radius > 0:
    top_edges = []
    for edge in shape.Edges:
        bbox = edge.BoundBox
        # Top edges are at Z = sleeve_height
        if abs(bbox.ZMin - sleeve_height) < 0.5 and abs(bbox.ZMax - sleeve_height) < 0.5:
            top_edges.append(edge)
    
    if top_edges:
        try:
            shape = shape.makeFillet(top_rim_radius, top_edges)
        except Exception as e:
            print(f"Fillet on top edges failed: {e}")
            print("Continuing without top rim fillet...")

# -----------------------------
# Create the FreeCAD object
# -----------------------------
sleeve_obj = doc.addObject("Part::Feature", "BuckleSleeveC")
sleeve_obj.Shape = shape

doc.recompute()

# Set view if GUI is available
try:
    import FreeCADGui as Gui
    Gui.activeDocument().activeView().viewIsometric()
    Gui.SendMsgToActiveView("ViewFit")
except:
    pass

print("=" * 50)
print("Seatbelt Buckle Sleeve (C-shape) created!")
print("=" * 50)
print(f"Outer dimensions: {outer_d:.1f} x {outer_w:.1f} x {sleeve_height:.1f} mm")
print(f"Inner cavity: {inner_d:.1f} x {inner_w:.1f} mm (open top & bottom)")
print(f"Wall thickness: {wall:.1f} mm")
print(f"Side slot width: {slot_width:.1f} mm on {slot_side} side")
print("Open bottom allows buckle to function normally!")
print("=" * 50)
