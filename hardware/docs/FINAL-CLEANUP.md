# Revision B — final labels and solder-pad correction

Historical revision B document. The executed review is in [REPORT.md](reports/preorder-review/REPORT.md); current B.1 corrections and validation are in [REVIEW-RESOLUTION.md](REVIEW-RESOLUTION.md).

6 September 2026, after the $82.72 quotation. Current board/manufacturing files supersede the uploaded Gerbers. No new quote or order was submitted in this cleanup.

## Labels and test point

TP5 (FAULT_N) moved 3.5 mm right: (43, 34.5) to (46.5, 34.5) mm from the top-left outline. FAULT is now right of D4, aligned with the LED; STATUS is left of D3. The FAULT_N branch and nearby 3.3 V track bends were adjusted locally and pours refilled. Position metadata is updated. Circuit topology, values, outline and SMT placements did not change.

## Missing 3D body

The boxed component is **U4, TPS25970LRPWR**, the fan-power protection IC. Its ten numbered pads, nets, custom footprint, schematic symbol, BOM entry C3662801 and SMT placement are present. It has no attached 3D model, so KiCad displays lands without a body. JLC included U4 in the quote. J2 also lacks a local 3D body. Neither absence means an omitted component; use manufacturer dimensions to review mechanical envelopes.

## Underside rings: real solder-mask defect

The soldered through-hole pads had copper layers but **no F.Mask or B.Mask openings**, in both board and project footprint copies. The copper itself was not unusually narrow; mask would cover the soldering surface. The render exposed a genuine manufacturing defect that the earlier clean ERC/DRC did not detect.

Restored both-face mask openings with **0.05 mm expansion per edge** for all 23 hand-solder joints and four USB-C shell pads. Updated local libraries as well as the board. Copper sizes, drills and paste geometry are unchanged. U1's deliberately covered thermal holes are excluded.

| Feature | Copper pad, mm | Hole/slot, mm | Narrowest nominal ring |
|---|---|---|---:|
| J3–J6 fan contacts | 2.03 × 1.73 | 1.02 round | 0.355 mm |
| C6 | 1.60 × 1.60 | 0.80 round | 0.400 mm |
| C9 | 2.00 × 2.00 | 1.00 round | 0.500 mm |
| J1 contact 1 | 4.60 × 2.00 | 3.60 × 1.00 slot | 0.500 mm |
| J1 other contacts | 4.20 × 2.00, rotated as appropriate | 3.20 × 1.00 slot | 0.500 mm |
| J2 shell tabs, factory assembly | 2.10 × 1.00 or 1.60 × 1.00 | 1.70 × 0.60 or 1.20 × 0.60 slot | 0.200 mm |

These are nominal dimensions before fabrication tolerances. The 0.355–0.500 mm hand-solder rings provide enough nominal land to retain the copper geometry; mask exposure was the required correction. USB shell pads retain their narrower connector lands, now exposed. Ground thermal reliefs remain. NPTH mounts/locators/tooling holes did not acquire copper.

## Verification and release

- Regenerated ERC, full DRC/parity and exact pad-net comparison: pass, no violations or unconnected items.
- Audited all 27 soldered PTH pads in board and local libraries for mask layers/expansion.
- Parsed both mask Gerbers and checked **54 pad openings**, coordinates and aperture dimensions. See `reports/solder-pad-mask-audit.json`; `tools/validate_b.py` repeats this audit.
- Inspected updated top/underside renders, including LED labels and exposed solder surfaces.
- Regenerated Gerbers, drills, drawings, board-only STEP, previews and hashes. BOM and SMT CPL remain identical to the quoted versions; TP5 has no purchased component.
- Added `PREORDER-REVIEW-PLAN.md`, a proposed agent review and testing workflow that has not been executed.

Old quoted files/manifest are in `reports/jlcpcb/quoted-inputs/`. Use the current `manufacturing/windpcb-revb-gerbers.zip` for a later submission; the JLC draft still contains older Gerbers. A.1 is retained unchanged and has not received this fix. Cost inputs are unchanged, but a revised live price has not been verified.

![Corrected underside](reports/board-bottom.png)
