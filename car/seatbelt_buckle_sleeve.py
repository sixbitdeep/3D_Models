# FreeCAD macro: Rounded seatbelt buckle sleeve - FULLY ENCLOSED (no side opening)
# Outer box minus inner cavity with fillets. Must slide on from top/bottom.

import FreeCAD as App
import Part

doc = App.ActiveDocument
if doc is None:
    doc = App.newDocument("Buckle_Sleeve_Enclosed")

# Clean reruns
for obj_name in ["BuckleSleeveEnclosed", "OuterBox", "InnerCavity"]:
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
bottom_rim_radius = 1.2  # soften bottom rim (0 disables)

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

# 4. Apply fillets to outer vertical edges
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

# 5. Apply fillet to top rim
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

# 6. Apply fillet to bottom rim
if bottom_rim_radius > 0:
    bottom_edges = []
    for edge in shape.Edges:
        bbox = edge.BoundBox
        # Bottom edges are at Z = 0
        if abs(bbox.ZMin) < 0.5 and abs(bbox.ZMax) < 0.5:
            bottom_edges.append(edge)
    
    if bottom_edges:
        try:
            shape = shape.makeFillet(bottom_rim_radius, bottom_edges)
        except Exception as e:
            print(f"Fillet on bottom edges failed: {e}")
            print("Continuing without bottom rim fillet...")

# -----------------------------
# Create the FreeCAD object
# -----------------------------
sleeve_obj = doc.addObject("Part::Feature", "BuckleSleeveEnclosed")
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
print("Seatbelt Buckle Sleeve (ENCLOSED) created!")
print("=" * 50)
print(f"Outer dimensions: {outer_d:.1f} x {outer_w:.1f} x {sleeve_height:.1f} mm")
print(f"Inner cavity: {inner_d:.1f} x {inner_w:.1f} mm (open top & bottom)")
print(f"Wall thickness: {wall:.1f} mm")
print("Fully enclosed - must slide on from top or bottom")
print("=" * 50)
