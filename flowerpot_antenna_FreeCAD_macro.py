#!/usr/bin/env python3
"""
VHF Airband Flowerpot Antenna - FreeCAD Parametric Macro (v4)
==============================================================
Optimized for 118-136 MHz aircraft band (centered at 127 MHz)
Designed for Bambu Lab X1C, ASA filament

FIXES in v4:
- FIXED: Male plug chamfer now at correct end (insertion tip at z=0)
- FIXED: Bottom cap plug chamfer at correct end
- FIXED: Shoulder is now a small lip, not a constriction
- FIXED: Removed ribs (cause foil wrinkles, complicate assembly)
- FIXED: Simplified groove cutting to single tube cutter
- Cleaner geometry that should boolean reliably in FreeCAD

Run this macro in FreeCAD: Macro → Macros → Execute
"""

import FreeCAD as App
import Part
import math

# =============================================================================
# USER PARAMETERS
# =============================================================================

TARGET_FREQ_MHZ = 127  # Aircraft band center

# Coax: RG-58=5.0, RG-8X=6.1, RG-6=6.8
COAX_OD = 6.1

# Sleeve method: "foil" or "tube"
SLEEVE_METHOD = "foil"

# Sleeve channel ID - where copper foil/tube sits
SLEEVE_CHANNEL_ID = 18.0

# Printer: Bambu X1C
MAX_PRINT_HEIGHT = 240

# Tube dimensions
TUBE_OD = 32.0
WALL_THICKNESS = 2.5
TUBE_ID = TUBE_OD - (WALL_THICKNESS * 2)  # 27mm

# Joints
JOINT_LENGTH = 25.0
JOINT_CLEARANCE = 0.25
CHAMFER_SIZE = 1.5

# Alignment key
KEY_WIDTH = 4.0
KEY_DEPTH = 2.0
KEY_LENGTH = JOINT_LENGTH - 2

# Caps
BOTTOM_CAP_HEIGHT = 20.0
TOP_CAP_HEIGHT = 25.0
DOME_HEIGHT = 12.0

# Drain holes
DRAIN_HOLE_DIA = 3.5
NUM_DRAIN_HOLES = 4

# Coax exit
COAX_HOLE_DIA = COAX_OD + 2.0

# Trim margin
TRIM_FACTOR = 1.02

# =============================================================================
# CALCULATED DIMENSIONS
# =============================================================================

C_MM_PER_SEC = 299792458000
WAVELENGTH = C_MM_PER_SEC / (TARGET_FREQ_MHZ * 1e6)
VF_RADIATOR = 0.95

HALF_WAVE_NOMINAL = (WAVELENGTH / 2) * VF_RADIATOR
QUARTER_WAVE_NOMINAL = WAVELENGTH / 4
HALF_WAVE = HALF_WAVE_NOMINAL * TRIM_FACTOR
QUARTER_WAVE = QUARTER_WAVE_NOMINAL * TRIM_FACTOR
TOTAL_ANTENNA_LENGTH = HALF_WAVE + QUARTER_WAVE

SECTION_BODY_LENGTH = MAX_PRINT_HEIGHT - JOINT_LENGTH
NUM_SECTIONS = math.ceil(TOTAL_ANTENNA_LENGTH / SECTION_BODY_LENGTH)
ACTUAL_SECTION_LENGTH = MAX_PRINT_HEIGHT - JOINT_LENGTH
SLEEVE_SECTIONS = math.ceil(QUARTER_WAVE / ACTUAL_SECTION_LENGTH)

# Derived radii
OUTER_R = TUBE_OD / 2              # 16.0
INNER_R = TUBE_ID / 2              # 13.5
SLEEVE_CHANNEL_R = SLEEVE_CHANNEL_ID / 2  # 9.0

# =============================================================================
# VALIDATION
# =============================================================================

def validate_parameters():
    male_outer_r = INNER_R - JOINT_CLEARANCE
    male_inner_r = INNER_R - WALL_THICKNESS
    
    if male_inner_r >= male_outer_r - 0.5:
        raise ValueError("Male plug wall too thin.")
    
    if SLEEVE_CHANNEL_ID >= TUBE_ID - 2:
        raise ValueError("Sleeve channel ID too large for tube ID.")
    
    if COAX_OD >= SLEEVE_CHANNEL_ID - 4:
        raise ValueError("Coax OD too large for sleeve channel.")
    
    liner_wall = INNER_R - SLEEVE_CHANNEL_R
    print(f"Liner wall thickness: {liner_wall:.1f}mm")
    print("Validation passed.")


# =============================================================================
# HELPERS
# =============================================================================

def create_document():
    doc_name = "FlowerpotAntenna_v4"
    if App.ActiveDocument and App.ActiveDocument.Name == doc_name:
        App.closeDocument(doc_name)
    return App.newDocument(doc_name)


def make_cylinder(radius, height, position=(0, 0, 0)):
    cyl = Part.makeCylinder(radius, height)
    cyl.translate(App.Vector(*position))
    return cyl


def make_tube(outer_r, inner_r, height, position=(0, 0, 0)):
    """Create hollow cylinder. Outer - inner."""
    outer = make_cylinder(outer_r, height, position)
    inner = make_cylinder(inner_r, height + 2, 
                          (position[0], position[1], position[2] - 1))
    return outer.cut(inner)


def make_dome(radius, height, position=(0, 0, 0)):
    sphere = Part.makeSphere(radius)
    mat = App.Matrix()
    mat.scale(1, 1, height / radius)
    sphere = sphere.transformGeometry(mat)
    box = Part.makeBox(radius * 3, radius * 3, radius * 2)
    box.translate(App.Vector(-radius * 1.5, -radius * 1.5, -radius * 2))
    sphere = sphere.cut(box)
    sphere.translate(App.Vector(*position))
    return sphere


def add_alignment_key(shape, radius, length, z_pos, is_male=True):
    """Add key (protrusion) or keyway (slot)."""
    if is_male:
        key = Part.makeBox(KEY_WIDTH, KEY_DEPTH, length)
        key.translate(App.Vector(-KEY_WIDTH/2, radius - KEY_DEPTH, z_pos))
        return shape.fuse(key)
    else:
        clearance = JOINT_CLEARANCE * 2
        slot = Part.makeBox(KEY_WIDTH + clearance, KEY_DEPTH + clearance, length + 1)
        slot.translate(App.Vector(-(KEY_WIDTH + clearance)/2,
                                   radius - KEY_DEPTH - JOINT_CLEARANCE, z_pos - 0.5))
        return shape.cut(slot)


def add_part_to_doc(doc, shape, name, color=(0.7, 0.7, 0.7)):
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    obj.ViewObject.ShapeColor = color
    return obj


# =============================================================================
# TUBE SECTION
# =============================================================================

def create_tube_section(section_num, is_sleeve_section=False, is_feedpoint_section=False):
    """
    Create tube section with male (bottom) and female (top) joints.
    Sleeve sections have a liner that reduces ID for the copper channel.
    """
    length = ACTUAL_SECTION_LENGTH
    
    # --- MAIN TUBE ---
    main_tube = make_tube(OUTER_R, INNER_R, length)
    
    # --- FEMALE SOCKET AT TOP (z = length - JOINT_LENGTH to z = length) ---
    female_r = INNER_R + JOINT_CLEARANCE
    female_socket = make_cylinder(female_r, JOINT_LENGTH + 0.1, 
                                   (0, 0, length - JOINT_LENGTH))
    main_tube = main_tube.cut(female_socket)
    
    # Female entrance chamfer (cone at z = length, opening outward)
    # Cone goes from female_r+CHAMFER at top to female_r at bottom
    chamfer_cone = Part.makeCone(female_r + CHAMFER_SIZE, female_r, CHAMFER_SIZE)
    chamfer_cone.translate(App.Vector(0, 0, length - CHAMFER_SIZE))
    main_tube = main_tube.cut(chamfer_cone)
    
    # Female keyway
    main_tube = add_alignment_key(main_tube, female_r, KEY_LENGTH,
                                   length - JOINT_LENGTH + 1, is_male=False)
    
    # --- MALE PLUG AT BOTTOM (z = -JOINT_LENGTH to z = 0) ---
    male_outer_r = INNER_R - JOINT_CLEARANCE
    male_inner_r = INNER_R - WALL_THICKNESS
    
    male_plug = make_tube(male_outer_r, male_inner_r, JOINT_LENGTH, 
                          (0, 0, -JOINT_LENGTH))
    
    # Male tip chamfer - at the FREE END which is z = -JOINT_LENGTH
    # Cone tapers from (male_outer_r - CHAMFER) at bottom to male_outer_r at top
    tip_chamfer = Part.makeCone(male_outer_r - CHAMFER_SIZE, male_outer_r, CHAMFER_SIZE)
    tip_chamfer.translate(App.Vector(0, 0, -JOINT_LENGTH))
    male_plug = male_plug.cut(tip_chamfer)
    
    main_tube = main_tube.fuse(male_plug)
    
    # Male key (on the plug exterior)
    main_tube = add_alignment_key(main_tube, male_outer_r - 0.3, KEY_LENGTH,
                                   -JOINT_LENGTH + 1, is_male=True)
    
    # --- SLEEVE CHANNEL (liner ring to reduce ID) ---
    if is_sleeve_section:
        # Liner spans middle of section, avoiding joint regions
        liner_start = JOINT_LENGTH + 2
        liner_end = length - JOINT_LENGTH - 2
        liner_length = liner_end - liner_start
        
        if liner_length > 10:
            # Fuse liner ring: reduces ID from INNER_R to SLEEVE_CHANNEL_R
            liner = make_tube(INNER_R - 0.05, SLEEVE_CHANNEL_R, liner_length,
                             (0, 0, liner_start))
            main_tube = main_tube.fuse(liner)
            
            # Small lip at bottom of liner for foil seating
            # This is NOT a constriction - just a tiny step (1mm tall, 1mm thick)
            lip_height = 1.0
            lip_thickness = 1.0
            lip = make_tube(SLEEVE_CHANNEL_R, SLEEVE_CHANNEL_R - lip_thickness,
                           lip_height, (0, 0, liner_start))
            main_tube = main_tube.fuse(lip)
    
    # --- FEEDPOINT FEATURES ---
    if is_feedpoint_section:
        # External groove for hose clamp - cut with single tube shape
        groove_z = length - JOINT_LENGTH - 15
        groove_height = 8.0
        groove_depth = 2.0
        
        # Tube cutter: removes annular ring
        groove_cutter = make_tube(OUTER_R + 0.1, OUTER_R - groove_depth,
                                   groove_height, (0, 0, groove_z))
        main_tube = main_tube.cut(groove_cutter)
        
        # Triple indicator marks (shallow grooves)
        for i in range(3):
            mark_z = groove_z - 5 - (i * 4)
            if mark_z > JOINT_LENGTH + 5:
                mark_cutter = make_tube(OUTER_R + 0.1, OUTER_R - 0.5,
                                        1.5, (0, 0, mark_z))
                main_tube = main_tube.cut(mark_cutter)
    
    return main_tube


# =============================================================================
# BOTTOM CAP
# =============================================================================

def create_bottom_cap():
    """Bottom cap with coax exit, drain holes, cable anchor."""
    height = BOTTOM_CAP_HEIGHT
    
    # Solid cap body
    cap = make_cylinder(OUTER_R, height)
    
    # --- MALE PLUG ON TOP (z = height to z = height + JOINT_LENGTH) ---
    male_outer_r = INNER_R - JOINT_CLEARANCE
    male_inner_r = INNER_R - WALL_THICKNESS
    
    male_plug = make_tube(male_outer_r, male_inner_r, JOINT_LENGTH, (0, 0, height))
    
    # Male tip chamfer - FREE END is at z = height + JOINT_LENGTH
    # Cone tapers from (male_outer_r - CHAMFER) at top to male_outer_r at bottom
    tip_chamfer = Part.makeCone(male_outer_r, male_outer_r - CHAMFER_SIZE, CHAMFER_SIZE)
    tip_chamfer.translate(App.Vector(0, 0, height + JOINT_LENGTH - CHAMFER_SIZE))
    male_plug = male_plug.cut(tip_chamfer)
    
    cap = cap.fuse(male_plug)
    
    # Male key
    cap = add_alignment_key(cap, male_outer_r - 0.3, KEY_LENGTH, height + 1, is_male=True)
    
    # --- INTERNAL CAVITY ---
    cavity_r = male_inner_r
    cavity = make_cylinder(cavity_r, height - WALL_THICKNESS + JOINT_LENGTH,
                           (0, 0, WALL_THICKNESS))
    cap = cap.cut(cavity)
    
    # --- COAX EXIT WITH BOSS ---
    boss_r = COAX_HOLE_DIA / 2 + 3
    boss_length = 5
    
    # Build boss at origin, rotate, translate
    boss = Part.makeCylinder(boss_r, boss_length)
    boss.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), 90)
    boss.translate(App.Vector(-OUTER_R - boss_length, 0, height / 2))
    cap = cap.fuse(boss)
    
    # Coax hole through everything
    coax_hole = Part.makeCylinder(COAX_HOLE_DIA / 2, OUTER_R + boss_length + 5)
    coax_hole.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), 90)
    coax_hole.translate(App.Vector(-OUTER_R - boss_length - 2, 0, height / 2))
    cap = cap.cut(coax_hole)
    
    # Vertical coax routing
    coax_up = make_cylinder(COAX_HOLE_DIA / 2, JOINT_LENGTH + height,
                            (0, 0, WALL_THICKNESS))
    cap = cap.cut(coax_up)
    
    # --- CABLE TIE ANCHOR ---
    anchor_width = 10
    anchor_span = cavity_r * 1.2
    anchor_thickness = 3
    anchor_z = height - 6
    
    anchor = Part.makeBox(anchor_width, anchor_span, anchor_thickness)
    anchor.translate(App.Vector(-anchor_width/2, -anchor_span/2, anchor_z))
    
    # Tie slot
    slot_width = anchor_width - 4
    slot = Part.makeBox(slot_width, 4, anchor_thickness + 2)
    slot.translate(App.Vector(-slot_width/2, -2, anchor_z - 1))
    anchor = anchor.cut(slot)
    
    cap = cap.fuse(anchor)
    
    # --- DRAIN HOLES ---
    for i in range(NUM_DRAIN_HOLES):
        angle = i * (360 / NUM_DRAIN_HOLES) + 45
        rad = math.radians(angle)
        x = (OUTER_R - WALL_THICKNESS) * math.cos(rad)
        y = (OUTER_R - WALL_THICKNESS) * math.sin(rad)
        drain = make_cylinder(DRAIN_HOLE_DIA / 2, WALL_THICKNESS + 2, (x, y, -1))
        cap = cap.cut(drain)
    
    return cap


# =============================================================================
# TOP CAP
# =============================================================================

def create_top_cap():
    """Top cap with dome, sealed for outdoor use."""
    height = TOP_CAP_HEIGHT
    
    cap = make_cylinder(OUTER_R, height)
    
    # Dome
    dome = make_dome(OUTER_R, DOME_HEIGHT, (0, 0, height))
    cap = cap.fuse(dome)
    
    # --- FEMALE SOCKET AT BOTTOM ---
    female_r = INNER_R + JOINT_CLEARANCE
    female_socket = make_cylinder(female_r, JOINT_LENGTH + 1, (0, 0, -1))
    cap = cap.cut(female_socket)
    
    # Female entrance chamfer
    chamfer_cone = Part.makeCone(female_r + CHAMFER_SIZE, female_r, CHAMFER_SIZE)
    chamfer_cone.translate(App.Vector(0, 0, -CHAMFER_SIZE))
    cap = cap.cut(chamfer_cone)
    
    # Female keyway
    cap = add_alignment_key(cap, female_r, KEY_LENGTH, 1, is_male=False)
    
    # --- INTERNAL CAVITY (solid top for weather seal) ---
    cavity_height = height - WALL_THICKNESS * 2
    cavity = make_cylinder(INNER_R - WALL_THICKNESS, cavity_height, (0, 0, JOINT_LENGTH))
    cap = cap.cut(cavity)
    
    # --- RADIATOR WIRE EXIT (small hole at apex) ---
    wire_hole_dia = 4.0
    wire_hole = make_cylinder(wire_hole_dia / 2, WALL_THICKNESS * 2 + DOME_HEIGHT + 1,
                              (0, 0, height - WALL_THICKNESS))
    cap = cap.cut(wire_hole)
    
    return cap


# =============================================================================
# ACCESSORIES
# =============================================================================

def create_coax_guide():
    """Coax centering clip for inside sleeve channel."""
    guide_or = SLEEVE_CHANNEL_R - 0.5
    guide_ir = COAX_OD / 2 + 0.5
    guide_height = 10.0
    
    ring = make_tube(guide_or, guide_ir, guide_height)
    
    # Flex slots
    for i in range(3):
        angle = i * 120
        slot = Part.makeBox(3.0, guide_or * 2.5, guide_height + 2)
        slot.translate(App.Vector(-1.5, -guide_or * 1.25, -1))
        slot.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), angle)
        ring = ring.cut(slot)
    
    return ring


def create_feedpoint_clamp():
    """Split clamp for feedpoint connection."""
    clamp_or = SLEEVE_CHANNEL_R + 4
    clamp_ir = SLEEVE_CHANNEL_R + 0.3
    clamp_height = 12.0
    
    clamp = make_tube(clamp_or, clamp_ir, clamp_height)
    
    # Split
    split = Part.makeBox(2.0, clamp_or * 2, clamp_height + 2)
    split.translate(App.Vector(-1.0, 0, -1))
    clamp = clamp.cut(split)
    
    # Bolt holes
    bolt_r = 1.6  # M3 clearance
    for z in [clamp_height * 0.25, clamp_height * 0.75]:
        for y_sign in [1, -1]:
            hole = Part.makeCylinder(bolt_r, 20)
            hole.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), 90)
            hole.translate(App.Vector(0, y_sign * (clamp_or - 2), z))
            clamp = clamp.cut(hole)
    
    return clamp


def create_sleeve_gauge():
    """Length gauge for cutting copper sleeve."""
    width = 15
    thickness = 3
    length = QUARTER_WAVE + 30
    
    gauge = Part.makeBox(width, length, thickness)
    
    # Notch at nominal
    n1 = Part.makeBox(width + 2, 2, 1.5)
    n1.translate(App.Vector(-1, QUARTER_WAVE_NOMINAL, thickness - 1.2))
    gauge = gauge.cut(n1)
    
    # Notch at cut length
    n2 = Part.makeBox(width + 2, 3, 2)
    n2.translate(App.Vector(-1, QUARTER_WAVE, thickness - 1.8))
    gauge = gauge.cut(n2)
    
    # Start mark
    n0 = Part.makeBox(width + 2, 2, 1)
    n0.translate(App.Vector(-1, 5, thickness - 0.8))
    gauge = gauge.cut(n0)
    
    return gauge


# =============================================================================
# MAIN
# =============================================================================

def main():
    validate_parameters()
    
    print("=" * 70)
    print("VHF AIRBAND FLOWERPOT ANTENNA v4")
    print("=" * 70)
    print(f"Frequency:        {TARGET_FREQ_MHZ} MHz")
    print(f"Radiator (½λ):    {HALF_WAVE:.1f}mm ({HALF_WAVE/25.4:.1f}\")")
    print(f"Sleeve (¼λ):      {QUARTER_WAVE:.1f}mm ({QUARTER_WAVE/25.4:.1f}\")")
    print(f"Total length:     {TOTAL_ANTENNA_LENGTH:.1f}mm ({TOTAL_ANTENNA_LENGTH/25.4:.1f}\")")
    print("-" * 70)
    print(f"Tube OD/ID:       {TUBE_OD}/{TUBE_ID}mm")
    print(f"Sleeve channel:   {SLEEVE_CHANNEL_ID}mm ID")
    print(f"Sections:         {NUM_SECTIONS} total, {SLEEVE_SECTIONS} sleeve")
    print("=" * 70)
    
    doc = create_document()
    
    spacing = 50
    z = 0
    
    # Bottom cap
    print("Creating: Bottom Cap")
    bc = create_bottom_cap()
    bc.translate(App.Vector(0, 0, z))
    add_part_to_doc(doc, bc, "BottomCap", (0.2, 0.6, 0.2))
    z += BOTTOM_CAP_HEIGHT + JOINT_LENGTH + spacing
    
    # Sections
    for i in range(NUM_SECTIONS):
        is_sleeve = i < SLEEVE_SECTIONS
        is_fp = i == SLEEVE_SECTIONS - 1
        
        name = f"Section_{i+1:02d}"
        if is_sleeve:
            name += "_Sleeve"
        if is_fp:
            name += "_FP"
        
        print(f"Creating: {name}")
        sec = create_tube_section(i, is_sleeve, is_fp)
        sec.translate(App.Vector(0, 0, z))
        
        color = (0.9, 0.5, 0.1) if is_fp else (0.2, 0.4, 0.7) if is_sleeve else (0.5, 0.7, 0.9)
        add_part_to_doc(doc, sec, name, color)
        z += ACTUAL_SECTION_LENGTH + spacing
    
    # Top cap
    print("Creating: Top Cap")
    tc = create_top_cap()
    tc.translate(App.Vector(0, 0, z))
    add_part_to_doc(doc, tc, "TopCap", (0.8, 0.2, 0.2))
    
    # Accessories
    print("Creating: Accessories")
    for i in range(4):
        g = create_coax_guide()
        g.translate(App.Vector(60, i * 20, 0))
        add_part_to_doc(doc, g, f"CoaxGuide_{i+1}", (0.9, 0.9, 0.3))
    
    clamp = create_feedpoint_clamp()
    clamp.translate(App.Vector(60, 100, 0))
    add_part_to_doc(doc, clamp, "FeedpointClamp", (0.9, 0.5, 0.1))
    
    gauge = create_sleeve_gauge()
    gauge.translate(App.Vector(100, 0, 0))
    add_part_to_doc(doc, gauge, "SleeveGauge", (0.6, 0.6, 0.6))
    
    doc.recompute()
    
    if App.GuiUp:
        import FreeCADGui
        FreeCADGui.activeDocument().activeView().viewAxonometric()
        FreeCADGui.SendMsgToActiveView("ViewFit")
    
    print("=" * 70)
    print("DONE - Export each part as STL: select part → File → Export")
    print("=" * 70)
    
    return doc


if __name__ == "__main__":
    main()
elif App.GuiUp:
    main()
