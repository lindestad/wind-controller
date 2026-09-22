# Factory placement reference (8 September 2026)

The final factory-adjusted placement was reviewed for all 70 components. The submitted CPL was not rewritten after JLC adjusted it. Always review a new supplier placement against the schematic and pads.

## U4 — the component in the user's image

The assigned part is **TI TPS25970LRPWR, C3662801, VQFN-10-HR, 2 × 2 mm**. Its model in the viewer has sixteen decorative perimeter leads. Those are not the physical terminal pattern and must not be used to rotate the component.

With the model hidden, the actual land pattern has the correct ten electrical terminals: four small terminals on each side and two long inner power lands. It agrees with TI's RPW0010A land-pattern drawing. The model is centered over that pattern; its marking is in the upper-left corner, consistent with the required real pin-1 location. This supports the displayed orientation; the generic model cannot demonstrate the shape of every hidden terminal.

Required pin map, also verified against the native board:

| Position | Pin and function |
|---|---|
| Upper-left | 1 EN, at (24.1, 28.3) |
| Left side downward | 2 OVLO, 3 DNC, 4 FLT |
| Inner long land, left | 5 IN |
| Inner long land, right | 6 OUT |
| Right side upward | 7 DVDT, 8 GND, 9 ILM, 10 ITIMER |

The processed PCB CAM archive retains **16 split paste openings** around U4; these are stencil apertures, not sixteen electrical pins. All 199 paste features and all 22 custom paste-symbol geometries are unchanged between its original and edited CAM steps after resolving reordered symbol indices.

**Disposition:** no U4 rotation or footprint change indicated. The rendering mismatch is visual. The actual laser-cut stencil thickness and assembly machine program are not established by the PCB CAM archive or this generic overlay.

Evidence: [U4 with model](U4.png), [actual U4 lands](U4-pads.png), [processed copper](u4-factory.png), [paste audit](paste-audit.json), [TI RPW land drawing](../preorder-review/reviewer-c/sources/tps2597-p52.png), [TI datasheet](https://www.ti.com/lit/ds/symlink/tps2597.pdf).

## Orientation and polarity findings

| References | Final observation and result |
|---|---|
| Q1 | Correct: pin 1/gate upper-left, pin 2/source lower-left, single pin 3/drain right. All three leads overlay the intended pads. The original 180° mismatch is resolved. |
| Q2, Q3, Q4, Q5 | Each individually checked: gate upper-left, source/GND lower-left, drain/PWM right; leads aligned. |
| Q6, Q7, Q8, Q9 | Each individually checked: gate/+3V3 upper-left, source/MCU tach lower-left, drain/fan tach right; leads aligned. |
| U2 | Correct: two terminals at top, three at bottom; pin 1/VIN bottom-left, pin 2/GND bottom-middle, pin 3/EN bottom-right, pin 5/VOUT top-left. |
| U3 | Correct: three terminals on each side, pin 1 upper-left. Pin 2/GND left-middle, pin 5/VBUS right-middle. All six leads aligned. |
| U1 | Correct: antenna toward top edge; module pin 1 upper-left; both nine-pad perimeter rows aligned. The decorative shield dot at bottom-left is not module pin 1. |
| J1 | Correct part DC-005-5A-2.5/C381115; opening left. Asymmetric terminal layout agrees: center-positive pin 1 right, switched pin 2 left, sleeve/GND pin 3 below. |
| J2 | Correct HRO TYPE-C-31-M-12/C165948, opening right. The final drawing's signal contacts overlap their lands; both locating-post markers register with the holes and all four shell features register with their slots. No remaining offset requiring a shift was found. See qualification below. |
| J3, J4, J5, J6 | Each individually checked: electrical pin 1 at left, then +12V, RPM, PWM. Friction lock faces the bottom board edge. Locating feature is above pin 3, over the intended NPTH, rather than on the opposite side as in the old preview. |
| C6 | Positive lead at left (7,26); negative at right (9.5,26). Positive marker and right-side negative stripe agree. |
| C9 | Positive lead at left (6,36); negative at right (11,36). Positive marker and right-side negative stripe agree. |
| D1 | Cathode/band **left**, connected to VIN_PROTECTED; anode right to RP_GATE. Correct. |
| D2 | Cathode/band **bottom**, connected to VIN_PROTECTED; anode top to GND. Correct; the downward cathode is intentional. |
| D3 | Cathode **left** to GND; anode right to LED_A. Correct. |
| D4 | Cathode **left** to FAULT_N; anode right to FAULT_LED_A. Correct. |
| SW1, SW2 | Four leads align; upper and lower contact-pair axis agrees with the footprint. No quarter-turn error. |
| All 32 resistors | Individually checked, both ends on their intended pads. No missing, displaced, or quarter-turn part observed. Reversed lettering on nonpolar parts is harmless. |
| C1–C5, C7, C8, C10, C11 | All nine nonpolar ceramics individually checked; correct part assignment and two-pad alignment. |
| F1, FB1 | Both nonpolar parts individually checked; correct assignment and alignment. |

The UI explicitly flags 14 references as engineer-modified: Q1–Q9, J3–J6 and U3. The final physical orientation was checked for *all* components, including U2 and J2, regardless of whether the UI flagged them.

JLC's [assembly FAQ](https://jlcpcb.com/help/article/pcb-assembly-faqs-part-2) explains that its colored dot denotes a component marking, not universally electrical pin 1; diode `+`/`−` means anode/cathode, and capacitor `+` means positive. Accordingly, the review used actual lead positions and native pad nets as well as these annotations.

### USB-C qualification

[Final component overlay](J2.png) and [bare lands at the same zoom](J2-pads.png) show simultaneous registration of the signal row, posts and shell slots. The exposed gray toe beyond each yellow contact is not, by itself, a displaced contact; a solder land is deliberately longer than the contact.

The retained [exact HRO drawing](../final-checks/C165948.png) specifies 5.78 mm locating-post spacing and 4.18 mm separation between shell rows; these agree with the native geometry. Native post centers are (64.2,21.11) and (64.2,26.89); shell centers have X63.67/67.85 and Y19.68/28.32. All seven connector slots (four USB, three jack) retained their centers, axes and straight centerline lengths during factory CAM processing. No blind model-origin shift or PCB revision is indicated.

This is a dimensional/visual registration check, not a measurement of supplied physical connector tolerances. The supplier model is still not a substitute for its mechanical drawing.

## Factory-file checks

Reproducible scripts and machine-readable results are retained beside this report.

| Check | Result |
|---|---|
| Original layers in factory ZIP versus current submitted manufacturing layers | Byte-identical for every corresponding file, including copper, masks, silk, outline, paste and drills. |
| Source PCB/BOM/CPL/release hashes | Unchanged from the previous reviewed B.3 release; see `hashes.json`. |
| Board outline | Same 70 × 64 mm rectangular centerline; factory line width is plotting width, not an increase in board dimensions. |
| Top and bottom copper | Compared at 20 µm/pixel with a two-pixel (40 µm per-axis) boundary tolerance. No additions beyond that tolerance inside the board. All larger removals are confined to existing non-plated-hole clearance regions. No other trace/pad change was detected at that resolution. |
| Top and bottom solder mask | No differences beyond the same tolerance. |
| Round holes | All 148 intended round-hole centers present, with no extras. Maximum matching error 0.000590 mm. |
| Slotted holes | All seven present; centers, axes and straight centerline lengths match within 0.001 mm. |
| Drill tool diameters | CAM diameters differ by approximately 0, +0.05, +0.13 or +0.15 mm, depending on hole group; slot cutter widths are about +0.151 mm. These are tool/CAM dimensions, not independent measurements of finished plated bores. No center shift or missing hole was found. |
| Paste in embedded CAM archive | All 199 original/edited features match after resolving symbol-index changes; 22 custom aperture geometries unchanged, including U4's 16 split apertures. |

The copper test excludes the outermost 0.30 mm to avoid factory plotting-border differences. It is a raster geometry comparison, **not a formal netlist-equivalence proof**. It does not establish finished-hole tolerances, stencil thickness, solder quantity, AOI/X-ray outcomes, or actual machine-program coordinates. The silkscreen was inspected visually in the final viewer; it was not subjected to the same numerical comparison.

## Recommendation

There is no remaining observed component-orientation, polarity, missing-part or USB/header registration issue that warrants another correction request. U4's generic artwork is not a reason to rotate it or change the PCB. The earlier reference-preview rotation offsets must **not** be applied again to this corrected final placement.

If the user wants additional factory assurance, the remaining targeted subject would be actual U4 stencil/process execution (including the specified 0.100 mm stencil approach), rather than asking for another visual rotation change. This review does not claim that such manufacturing-process assurance has been received. No support contact or approval has been made on the user's behalf.

## Evidence index

- `dfm-final-overview.png`: final live viewer, restored to the full labeled board.
- `sheet-1.png` through `sheet-6.png`: inspection contact sheets; individual full-resolution `<reference>.png` files retain the detailed views for all 70 parts.
- `U4-pads.png`, `J2-pads.png`, `J3-pads.png`: component-hidden views.
- `dfm-rows.json`, `bom-audit.json`: actual final table and automated assignment check.
- `hole-audit.json`, `raster-comparison.json`, `paste-audit.json`, `hashes.json`: factory comparison evidence.
- `factory/`: extracted downloaded ZIP, preserved for traceability.
- Previous native pin and net audit: [pad-audit.json](../placement-review/pad-audit.json).

## Individual component record

Every row below has its own saved browser image. “Aligned” means no visible placement discrepancy found against the intended pads; it does not certify solder-joint quality.


| Reference | Actual assigned part | Assembly | Individual review |
|---|---|---|---|
| [C1](C1.png) | CL10A105KB8NNNC / C15849 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [C2](C2.png) | CL10A105KB8NNNC / C15849 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [C3](C3.png) | GRM21BR61H106KE43L / C440198 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [C4](C4.png) | CC0603KRX7R9BB104 / C14663 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [C5](C5.png) | CL10A105KB8NNNC / C15849 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [C6](C6.png) | EEUFR1H470 / C407950 | Wave Soldering | Positive left, negative stripe right; centered over lead pair. |
| [C7](C7.png) | CL21B105KBFNNNE / C28323 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [C8](C8.png) | CC0603KRX7R9BB104 / C14663 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [C9](C9.png) | EEUFR1E471 / C407944 | Wave Soldering | Positive left, negative stripe right; centered over lead pair. |
| [C10](C10.png) | CL21B105KBFNNNE / C28323 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [C11](C11.png) | CC0603KRX7R9BB104 / C14663 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [D1](D1.png) | BZT52C9V1-7-F / C260913 | SMT Assembly | Cathode/band left; aligned. |
| [D2](D2.png) | SMBJ15A / C83846 | SMT Assembly | Cathode/band bottom; aligned. |
| [D3](D3.png) | KT-0805G / C2297 | SMT Assembly | Cathode left; aligned. |
| [D4](D4.png) | KT-0603R / C2286 | SMT Assembly | Cathode left; aligned. |
| [F1](F1.png) | 0466003.NRHF / C14165 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [FB1](FB1.png) | BLM31PG121SN1L / C85841 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [J1](J1.png) | DC-005-5A-2.5 / C381115 | Wave Soldering | Opening left; correct asymmetric jack registration. |
| [J2](J2.png) | TYPE-C-31-M-12 / C165948 | SMT Assembly | Opening right; signal contacts, both posts and four shell slots register. |
| [J3](J3.png) | 470531000 / C240840 | Wave Soldering | Pin 1 left, locator above pin 3, lock toward bottom; aligned. |
| [J4](J4.png) | 470531000 / C240840 | Wave Soldering | Pin 1 left, locator above pin 3, lock toward bottom; aligned. |
| [J5](J5.png) | 470531000 / C240840 | Wave Soldering | Pin 1 left, locator above pin 3, lock toward bottom; aligned. |
| [J6](J6.png) | 470531000 / C240840 | Wave Soldering | Pin 1 left, locator above pin 3, lock toward bottom; aligned. |
| [Q1](Q1.png) | AO3401A / C15127 | SMT Assembly | Pin 1 upper-left, two terminals left / single drain right; aligned. |
| [Q2](Q2.png) | SI2312-TP / C6488168 | SMT Assembly | Pin 1 upper-left, two terminals left / single drain right; aligned. |
| [Q3](Q3.png) | SI2312-TP / C6488168 | SMT Assembly | Pin 1 upper-left, two terminals left / single drain right; aligned. |
| [Q4](Q4.png) | SI2312-TP / C6488168 | SMT Assembly | Pin 1 upper-left, two terminals left / single drain right; aligned. |
| [Q5](Q5.png) | SI2312-TP / C6488168 | SMT Assembly | Pin 1 upper-left, two terminals left / single drain right; aligned. |
| [Q6](Q6.png) | SI2312-TP / C6488168 | SMT Assembly | Pin 1 upper-left, two terminals left / single drain right; aligned. |
| [Q7](Q7.png) | SI2312-TP / C6488168 | SMT Assembly | Pin 1 upper-left, two terminals left / single drain right; aligned. |
| [Q8](Q8.png) | SI2312-TP / C6488168 | SMT Assembly | Pin 1 upper-left, two terminals left / single drain right; aligned. |
| [Q9](Q9.png) | SI2312-TP / C6488168 | SMT Assembly | Pin 1 upper-left, two terminals left / single drain right; aligned. |
| [R1](R1.png) | 0603WAF5101T5E / C23186 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R2](R2.png) | 0603WAF5101T5E / C23186 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R3](R3.png) | 0603WAF220JT5E / C23345 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R4](R4.png) | 0603WAF220JT5E / C23345 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R5](R5.png) | 0603WAF1002T5E / C25804 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R6](R6.png) | 0603WAF1002T5E / C25804 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R7](R7.png) | 0603WAF1002T5E / C25804 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R8](R8.png) | 0603WAF1002T5E / C25804 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R9](R9.png) | 0603WAF1001T5E / C21190 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R10](R10.png) | 0603WAF4701T5E / C23162 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R11](R11.png) | RT0603BRE0797K6L / C862326 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R12](R12.png) | RT0603BRD0710KL / C95204 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R13](R13.png) | 0603WAF2401T5E / C22940 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R14](R14.png) | 0603WAF1001T5E / C21190 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R15](R15.png) | 0603WAF1002T5E / C25804 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R16](R16.png) | 0603WAF4701T5E / C23162 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R17](R17.png) | 0603WAF1002T5E / C25804 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R18](R18.png) | 0603WAF2201T5E / C4190 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R19](R19.png) | 0603WAF1001T5E / C21190 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R20](R20.png) | 0603WAF1000T5E / C22775 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R21](R21.png) | 0603WAF1003T5E / C25803 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R22](R22.png) | 0603WAF2201T5E / C4190 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R25](R25.png) | 0603WAF1000T5E / C22775 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R26](R26.png) | 0603WAF1003T5E / C25803 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R27](R27.png) | 0603WAF2201T5E / C4190 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R30](R30.png) | 0603WAF1000T5E / C22775 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R31](R31.png) | 0603WAF1003T5E / C25803 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R32](R32.png) | 0603WAF2201T5E / C4190 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R35](R35.png) | 0603WAF1000T5E / C22775 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R36](R36.png) | 0603WAF1003T5E / C25803 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R37](R37.png) | 0603WAF2201T5E / C4190 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [R40](R40.png) | 0603WAF1000T5E / C22775 | SMT Assembly | Nonpolar; both terminations aligned with intended pads. |
| [SW1](SW1.png) | TL3342F160QG / C2886898 | SMT Assembly | Four leads aligned; upper/lower contact-pair axis correct. |
| [SW2](SW2.png) | TL3342F160QG / C2886898 | SMT Assembly | Four leads aligned; upper/lower contact-pair axis correct. |
| [U1](U1.png) | ESP32-C3-WROOM-02-N4 / C2934560 | SMT Assembly | Antenna up; perimeter rows aligned. |
| [U2](U2.png) | AP2112K-3.3TRG1 / C51118 | SMT Assembly | Pin 1 bottom-left; three terminals on bottom; aligned. |
| [U3](U3.png) | USBLC6-2SC6 / C7519 | SMT Assembly | Pin 1 upper-left; GND left-middle / VBUS right-middle; aligned. |
| [U4](U4.png) | TPS25970LRPWR / C3662801 | SMT Assembly | Centered; upper-left marking consistent; generic body. Actual ten-terminal lands checked separately. |
