# Revision B.3 — 5.5 × 2.5 mm power input

7 September 2026. User requested the board jack match the existing TDX-1204000 supply: labelled 12 V / 4 A, centre-positive, measured approximately 5.5 mm outside / 2.5 mm inside / 10 mm barrel length. This replaces B.2's 2.1 mm input requirement. Actual adapter voltage, ripple and under-load performance are not yet measured.

## Selected component

J1 is **XKB DC-005-5A-2.5, JLC/LCSC C381115**, black, right-angle through-hole, catalogue rated 5 A / 24 V. JLC lists wave soldering and Economic/Standard assembly support. The manufacturer's drawing explicitly shows a 5.5 mm mating barrel, the 2.5 mm centre-pin option and 9 mm insertion depth. The catalogue's 6.5 mm dimension describes the jack opening, not the required plug outside diameter. A 10 mm metal barrel can leave approximately 1 mm exposed when fully inserted; enclosure clearance and actual retention require a physical fit check.

- [JLC assembly listing](https://jlcpcb.com/partdetail/XKBConnection-DC_005_5A_25/C381115)
- [Manufacturer drawing mirrored by distributor](https://img.iceasy.com/product/product/files/202107/C381115_F2190B40D933B9992A6C1A8F3C065453.pdf), retained in `reports/jack-25/sources/C381115.pdf`.

The part remains in the same cost class as B.2. [LCSC's observed small-quantity listing](https://www.lcsc.com/product-detail/C381115.html) was about $0.27 per component, but this is not a JLC PCBA checkout price or stock reservation. The subsequent B.3 browser quote is $91.80 before shipping/tax and any review surcharges; see `reports/final-checks/REPORT.md`.

## Footprint and assembly changes

New local footprint: `Wind:BarrelJack_XKB_DC-005-5A-2.5`. The drawing is a **bottom view** and must be mirrored for the board's top view. Relative to pin 1, pin 2 is 6.0 mm toward the opening; pin 3 is 3.0 mm toward the opening and 4.7 mm sideways. Pin 1 remains centre positive / VIN_RAW, pin 3 remains sleeve / GND, and pin 2 is the unused sleeve switch.

Pin 1 remains at absolute 114.2,115.0 mm and pin 3 at 111.2,119.7 mm. Pin 2 moves from 108.3,115.0 to 108.2,115.0 mm. Plated slots match the drawing: pin 1 is 3.5 × 1.0 mm in the mounted board orientation; pin 2 is 3.0 × 1.0 mm; pin 3 is 1.0 × 3.0 mm. Existing copper land sizes are retained, giving at least 0.5 mm nominal annular margin. Both-face mask expansion remains 0.05 mm. Body envelope is updated to 14.4 × 9 × 11 mm; the courtyard and representative 3D body follow it.

All tracks, vias and other component pad geometry remain unchanged. Black 70 × 64 mm board, white LINDESTAD branding and FAULT/STATUS labels are retained. The revision silkscreen reads WIND / REV B.3. The schematic, native board, local footprint, master design data, BOM and generated full PCBA BOM identify C381115 consistently. Population remains 63 SMT + 7 THT = 70 components / 33 MPN groups.

The new J1 CPL insertion point is the new pad-array midpoint: **X 11.20, Y 46.65 mm, rotation 0°**, with the existing bottom-left manufacturing origin. The subsequent C381115-specific JLC underside preview confirms registration of all three terminals with the B.3 slots; see `reports/final-checks/jlc-jack-bottom.png`. Final factory placement review remains required.

## Release and verification

Use the regenerated `manufacturing/windpcb-revb-gerbers.zip`, `manufacturing/assembly/PCBA-BOM.csv` and `PCBA-CPL.csv`. The subsequent B.3 cart draft **[historical order reference omitted]** contains these exact inputs and C381115; all 33 part groups match. The older Y2/B.2 cart remains unselected: **do not order it as B.3**. Factory process acceptance and USB-C footprint disposition remain open. No order or payment has been made. See `reports/final-checks/REPORT.md`.

Run `tools/export.py`, `validate_b.py`, `validate_b1.py`, `validate_b3.py`, then `package_release.py` with KiCad's Python. Checks cover ERC, full DRC/schematic parity, all pad nets, both-face PTH mask openings, retained protection/USB routing, unchanged full track/via geometry, new jack geometry and 70-place BOM/CPL agreement. Evidence is in `reports/jack-25/validation.json` and the current final reports. B.2 evidence remains historical. Electrical simulations do not need new models for this connector-only substitution; actual PSU and first-board tests remain outstanding.
