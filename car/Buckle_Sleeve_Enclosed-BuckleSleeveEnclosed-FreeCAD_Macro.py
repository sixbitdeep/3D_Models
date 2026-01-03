# FreeCAD macro: Rounded seatbelt buckle sleeve - FULLY ENCLOSED
# With ROUNDED INNER CORNERS to match buckle shape (no gaps!)
# Outer box minus inner cavity with fillets on both outer AND inner corners.

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
buckle_width = 48.6      # Y direction (left-right), your measured OUTER width
buckle_depth = 32.3      # X direction (front-back), your measured OUTER depth
sleeve_height = 28.4     # Adjust This Z direction, how tall the sleeve is

clearance = 0.8          # fit tolerance around buckle
wall = 2.5               # wall thickness

# Corner radii
outer_corner_radius = 6.0      # outer corner rounding
inner_corner_radius = 8.0      # Adjust Me INNER CORNERS rounding to match buckle's rounded corners
                               # Adjust this to match your buckle's actual corner radius!
top_rim_radius = 1.2           # soften top rim (0 disables)
bottom_rim_radius = 1.2        # soften bottom rim (0 disables)

# -----------------------------
# Derived sizes
# -----------------------------
inner_w = buckle_width + 2 * clearance   # inner cavity width (Y)
inner_d = buckle_depth + 2 * clearance   # inner cavity depth (X)
outer_w = inner_w + 2 * wall             # outer width (Y)
outer_d = inner_d + 2 * wall             # outer depth (X)

# -----------------------------
# Build the sleeve using rounded rectangles
# -----------------------------

def make_rounded_box(length_x, width_y, height_z, corner_r):
    """Create a box with rounded vertical corners (filleted edges)"""
    # Clamp radius to max possible
    max_r = min(length_x, width_y) / 2 - 0.1
    r = min(corner_r, max_r) if corner_r > 0 else 0
    
    if r > 0:
        # Create a 2D rounded rectangle and extrude it
        # Build the profile with arcs at corners
        import math
        
        # Corner centers
        c1 = App.Vector(r, r, 0)                      # bottom-left
        c2 = App.Vector(length_x - r, r, 0)          # bottom-right
        c3 = App.Vector(length_x - r, width_y - r, 0) # top-right
        c4 = App.Vector(r, width_y - r, 0)           # top-left
        
        # Create edges: lines and arcs
        edges = []
        
        # Bottom edge
        edges.append(Part.makeLine(App.Vector(r, 0, 0), App.Vector(length_x - r, 0, 0)))
        # Bottom-right arc
        edges.append(Part.makeCircle(r, c2, App.Vector(0, 0, 1), -90, 0))
        # Right edge
        edges.append(Part.makeLine(App.Vector(length_x, r, 0), App.Vector(length_x, width_y - r, 0)))
        # Top-right arc
        edges.append(Part.makeCircle(r, c3, App.Vector(0, 0, 1), 0, 90))
        # Top edge
        edges.append(Part.makeLine(App.Vector(length_x - r, width_y, 0), App.Vector(r, width_y, 0)))
        # Top-left arc
        edges.append(Part.makeCircle(r, c4, App.Vector(0, 0, 1), 90, 180))
        # Left edge
        edges.append(Part.makeLine(App.Vector(0, width_y - r, 0), App.Vector(0, r, 0)))
        # Bottom-left arc
        edges.append(Part.makeCircle(r, c1, App.Vector(0, 0, 1), 180, 270))
        
        wire = Part.Wire(edges)
        face = Part.Face(wire)
        solid = face.extrude(App.Vector(0, 0, height_z))
        return solid
    else:
        return Part.makeBox(length_x, width_y, height_z)

# 1. Create outer shape with rounded corners
outer = make_rounded_box(outer_d, outer_w, sleeve_height, outer_corner_radius)

# 2. Create inner cavity with rounded corners (to match buckle!)
#    Goes through BOTH top and bottom - it's a sleeve!
inner = make_rounded_box(inner_d, inner_w, sleeve_height + 2.0, inner_corner_radius)
inner.translate(App.Vector(wall, wall, -1.0))

# 3. Cut cavity from outer
shape = outer.cut(inner)

# 4. Apply fillet to top rim edges
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

# 5. Apply fillet to bottom rim edges
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
print("Seatbelt Buckle Sleeve (ENCLOSED + ROUNDED INNER) created!")
print("=" * 50)
print(f"Outer dimensions: {outer_d:.1f} x {outer_w:.1f} x {sleeve_height:.1f} mm")
print(f"Inner cavity: {inner_d:.1f} x {inner_w:.1f} mm (open top & bottom)")
print(f"Wall thickness: {wall:.1f} mm")
print(f"Outer corner radius: {outer_corner_radius:.1f} mm")
print(f"Inner corner radius: {inner_corner_radius:.1f} mm  <-- matches buckle corners!")
print("=" * 50)
print("\nADJUST inner_corner_radius if gaps remain or fit is too tight.")
print("Measure your buckle's corner radius with calipers if possible.")
print("=" * 50)
