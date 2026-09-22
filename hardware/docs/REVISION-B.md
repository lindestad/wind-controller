# Revision B — layout, sourcing and manufacturing decisions

Historical revision B document. The executed review is in [REPORT.md](reports/preorder-review/REPORT.md); current B.1 corrections and validation are in [REVIEW-RESOLUTION.md](REVIEW-RESOLUTION.md).

6 September 2026. New isolated revision; A.1 is retained unchanged by this task.

## Changes from A.1

Post-quote label/TP5 cleanup and a manufacturing-critical solder-mask correction are documented in [FINAL-CLEANUP.md](FINAL-CLEANUP.md). The current native files and Gerbers supersede those in the $82.72 draft; refresh manufacturing inputs before ordering. BOM and SMT placement counts remain unchanged.

| Item | A.1 | B |
|---|---|---|
| Board | 70 × 76 mm | 70 × 64 mm: 12 mm shorter, 15.79% less area |
| Finish appearance | Green / white | Black / white; native stackup colour and order notes |
| Branding | WIND revision label | Slanted LINDESTAD wordmark with three wind strokes |
| C6 / C9 positive-pad locations, from top-left | (11,37) / (22,43) mm | (7,26) / (6,36) mm |
| Fan-header pin-one row | y = 65 mm | y = 53 mm, same 15 mm horizontal pitch |
| Fan driver groups | Spread over approximately 51–61 mm | Repeated compact placement approximately 43.5–49.4 mm |
| Mounting-hole spacing | 63 × 69 mm | 63 × 57 mm |
| Assembly tooling holes | Supplier-added positions | Two specified 1.152 mm NPTHs, H5/H6 |
| Green status LED D3 | KT-0603G, C12624, Extended | KT-0805G, C2297, Basic; new 0805 footprint |
| Current-limit resistor R13 | 2.32 kΩ, C2933173, Extended | 2.4 kΩ, C22940, Basic |
| Nominal current limit | 2.477 A | 2.395 A |
| Module thermal-hole copper lands | 0.60 mm / 0.30 mm drill | 0.70 mm / 0.30 mm drill; 0.20 mm annular ring |

The initial 62 mm height target was relaxed to 64 mm to retain mounting-head and connector courtyard clearances. Both input connectors and the MCU/USB core keep their positions. The capacitors move in the direction indicated in the supplied image. The four driver groups retain space between packages and fan plugs; through-hole capacitor bodies retain their full physical envelopes. Ground stitching avoids the printed wordmark and labels.

## Cost decisions

D3 and R13 each eliminate an Extended type. The new live quote confirms **a $6.14 Extended-fee reduction per order**, from fifteen to thirteen types ($46.05 → $39.91). Both codes matched as Basic; no additional substitutions were needed. Stock must still be rechecked when purchasing; no parts were reserved. [Green LED](https://jlcpcb.com/partdetail/C2297), [2.4 kΩ resistor](https://jlcpcb.com/partdetail/C22940).

The current-limit change is intentional: R13 retains 1% tolerance and the same footprint. The new calculated minimum is 2.124 A with resistor temperature drift included, above the four fans' 1.4 A combined rating. Actual simultaneous startup still needs measurement. The green LED preserves its colour and cathode numbering, with an appropriate larger footprint. Its brightness at the retained low drive current is not guaranteed by the catalogue's 5 mA brightness rating.

The last **A.1** live quote was $105.13 before shipping/tax, including $21.10 green ENIG fabrication and $84.03 SMT parts/assembly. The **B live quote is $82.72**, including $5.20 black lead-free HASL fabrication and $77.52 SMT parts/assembly. Savings are **$22.41 (21.32%)**: $15.90 from fabrication/finish and $6.51 from assembly/parts. This comparison changes finish as well as the BOM; it does not attribute the full saving to shrinking the board. B remains within the original $80–105 planning allowance. [Full quote evidence](reports/jlcpcb/QUOTE.md).

| B manufacturing route, five PCBs / two assembled | USD before shipping/tax | Decision |
|---|---:|---|
| Black, lead-free HASL, Economic | **82.72 live quote, 6 September 2026** | Cost-oriented candidate; U4 process acceptance required |
| Black, ENIG, Standard with removable rails | Approximately 130–170 | Flatter finish; extra setup, stencil, panel/fixture costs; not yet panelized or quoted |

The Standard allowance uses the published single-side setup $25.56, stencil $8.21 and $1.53 feeders for all thirty MPNs, plus approximate parts and ENIG fabrication. Fixture, inspection, storage and panel charges can alter it. The handling-fee rule is conditional, not an automatic extra $14.93 to add to every estimate. Through-hole purchases, shipping, tax, power supply and enclosure are excluded from both allowances. [Current JLC fee schedule](https://jlcpcb.com/help/article/pcb-assembly-price).

## Parts retained after review

- Retain both bulk capacitors, TVS, backup fuse, reverse-polarity FET/clamp, ferrite, eFuse and USB ESD protection: deleting these changes the requested protection/filtering behaviour.
- Retain precision R11/R12. Ordinary 1% replacements would widen the overvoltage threshold unnecessarily.
- Retain BSS138 PWM transistors. The Basic 2N7002 candidate C8545 advertises on-resistance at 10 V, which is insufficient evidence of worst-case 3.3 V drive performance. A qualified low-voltage replacement could save another feeder fee later. [Candidate listing](https://jlcpcb.com/partdetail/JiangsuChangjingElec-2N7002/C8545).
- Retain BOOT and RESET. USB recovery independent of firmware is a requirement. Cheaper switches need a fresh mechanical/pin review.
- Retain the four DNP pull-up footprints. They cost no components or feeder setups and provide an edge-rate adjustment if measurements require it.
- Retain four separate PWM/tach channels. Combining fan pairs would reduce parts but lose per-fan diagnostics and flexibility.

The greatest remaining cost choice is the assembly process/finish. The current schematic already uses many Basic passives, so removing individual cheap resistors offers little saving at two assembled boards.
