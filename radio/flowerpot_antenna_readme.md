# VHF Airband Flowerpot Antenna (118-136 MHz)

A 3D-printed collinear sleeve antenna optimized for receiving aircraft communications. Works great with RTL-SDR dongles and other software-defined radios for monitoring ATC, ATIS, and aircraft traffic.

## What is a Flowerpot Antenna?

A flowerpot (or coaxial sleeve) antenna is a half-wave vertical with a quarter-wave choke sleeve that acts as a balun. The sleeve blocks common-mode currents on the feedline, giving you a clean omnidirectional pattern without the need for radials.

**Performance:**
- Gain: ~3-4 dBi
- Pattern: Omnidirectional
- Polarization: Vertical
- Bandwidth: Full 118-136 MHz aircraft band

## Printed Parts

| Part | Quantity | Description |
|------|----------|-------------|
| Bottom Cap | 1 | Coax entry, drain holes, cable tie anchor |
| Sleeve Section | 3 | Dark blue - line with copper foil |
| Feedpoint Section | 1 | Orange - has external clamp groove |
| Radiator Section | 4 | Light blue - houses center conductor |
| Top Cap | 1 | Domed, weatherproof, wire exit hole |
| Feedpoint Clamp | 1 | Optional - secures shield-to-sleeve bond |

## Bill of Materials

| Item | Specification | Notes |
|------|---------------|-------|
| Coax cable | RG-8X recommended | RG-58 or RG-6 also work |
| Copper foil tape | 2" wide, conductive adhesive | ~650mm length needed |
| SMA adapter | Depends on your SDR | F-type if using RG-6 |
| Silicone sealant | Any outdoor rated | For sealing joints |
| Hose clamp | 32-38mm | Optional, for feedpoint |

## Print Settings

- **Material:** ASA (recommended for UV resistance) or PETG
- **Layer height:** 0.2mm
- **Walls:** 3-4 perimeters
- **Infill:** 15-20%
- **Supports:** Only needed for top cap dome

Print tubes vertically. Caps print flat side down.

## Critical Dimensions

These are tuned for 127 MHz (aircraft band center) with 2% trim margin:

| Element | Cut Length | Nominal (trim to) |
|---------|------------|-------------------|
| Copper sleeve | 603mm (23.7") | 591mm (23.3") |
| Radiator | 1145mm (45.1") | 1122mm (44.2") |

The parts are designed with a 2% trim margin. Cut to the longer length, test, then trim back toward nominal if needed.

## Assembly Instructions

### 1. Prepare the Copper Sleeve

Cut copper foil tape to 603mm length. Apply inside the three sleeve sections (dark blue), overlapping seams by 50%. The foil should be continuous across all sleeve sections when assembled. Test continuity with a multimeter.

### 2. Assemble the Tube

1. Start with the bottom cap
2. Add sleeve sections (dark blue) - align the keys
3. Add feedpoint section (orange)
4. Add radiator sections (light blue)
5. Finish with top cap

Dry-fit first to check alignment. Joints have alignment keys to maintain orientation.

### 3. Prepare the Coax

1. Route coax up through bottom cap
2. At the **top of the sleeve sections** (603mm from bottom):
   - Strip outer jacket (~30mm)
   - Fold shield braid back
   - This is your **feedpoint**
3. Continue center conductor up through radiator sections
4. Strip center conductor at top (at 1145mm total from feedpoint)

### 4. Make the Feedpoint Connection

The coax shield must bond electrically to the copper sleeve at the feedpoint. Options:

- Solder a wire from shield to copper foil
- Use the included feedpoint clamp with a hose clamp
- Wrap with copper tape and solder

This connection is critical - it's what makes the choke work.

### 5. Seal and Mount

1. Apply silicone sealant to all joints
2. Seal the top cap wire exit with silicone
3. Mount vertically using hose clamps to a PVC mast
4. Route coax with a drip loop

## Tuning (Optional)

For receive-only use, tuning is not critical. The antenna will work well across the entire aircraft band as-is.

If you have a NanoVNA or similar and want to optimize:

1. Check SWR at 127 MHz
2. If resonance is low (SWR dip below 127 MHz): trim the radiator
3. If resonance is high (SWR dip above 127 MHz): radiator is too short (cut a new one slightly longer)

Target: SWR < 2:1 across 118-136 MHz

## Design Notes

**Why the printed tube?**

The plastic tube is just a radome - it protects the antenna and provides structure. The RF-active parts are:
- Copper foil sleeve (the choke)
- Coax center conductor (the radiator)
- Shield-to-sleeve bond (the feedpoint)

**Why sleeve sections have a reduced inner diameter?**

The "liner" in sleeve sections creates a channel where the copper foil sits. This keeps the foil at a consistent diameter and provides a small lip to seat the foil edge.

**Joint design:**

All joints have male/female slip-fit connections with:
- 0.25mm clearance per side
- Lead-in chamfers for easy assembly
- Alignment keys to maintain orientation

## Troubleshooting

**Weak signals:**
- Check continuity of copper sleeve across all joints
- Verify feedpoint connection (shield bonded to sleeve)
- Make sure center conductor reaches the top

**No signals:**
- Check coax continuity
- Verify your SDR is tuned to aircraft band (118-136 MHz, AM mode)
- Try a known-active frequency like your local ATIS

**Water ingress:**
- Reseal joints with silicone
- Check top cap seal around wire exit
- Verify drain holes in bottom cap are clear

## License

This design is released to the public domain. Build it, modify it, share it.

## Acknowledgments

Flowerpot antenna design originally popularized by VK2ZOI. This implementation optimized for 3D printing and VHF airband reception.
