# Revision B.2 — full factory assembly

Historical: B.3 supersedes the jack, plug requirement and supplier files below. See [REVISION-B3.md](REVISION-B3.md).

7 September 2026. Supersedes the B.1 sourcing/assembly plan; the reviewed controller circuitry remains unchanged. Black 70 x 64 mm board, white LINDESTAD silkscreen, existing LED labels, mounts and tooling holes retained.

## Parts and cost decisions

| Reference | B.2 part | JLC code | Decision |
|---|---|---|---|
| J1 | XKB DC-005-5A-2.0 | C381116 | Replaces discontinued GCT jack. 5 A rating, standard 5.5 x 2.1 mm centre-positive plug. New manufacturer-derived footprint and pin numbering. |
| C6 | Panasonic EEUFR1H470 | C407950 | Exact existing 47 uF / 50 V FR part; factory THT assembly. |
| C9 | Panasonic EEUFR1E471 | C407944 | Replaces Nichicon UPW1E471MPD. 470 uF / 25 V, 10 mm diameter, 5 mm pitch, shorter 12.5 mm body. 43 milliohm impedance and 1.29 A ripple at 100 kHz. |
| J3-J6 | Molex 470531000 | C240840 | Exact existing 47053-1000 keyed fan connector, natural white; approximately $0.1775 each in the observed JLC catalogue. Black variants were not established as a stocked, documented economical assembly substitute. |
| J2 | HRO TYPE-C-31-M-12 | C165948 | Retained: approximately $0.1856, stocked, already fits the reviewed USB routing. |

Observed JLC stock: C381116 40,365 at $0.2609; C407944 154 at $0.3001; C240840 5,371 at $0.1775. Catalogue observations are unreserved and are not final checkout prices. No generic capacitor or unkeyed fan header substitutes are approved.

## Jack implementation

Manufacturer drawing `reports/full-assembly/sources/C381116.pdf` explicitly specifies a 5.5 mm OD / 2.1 mm ID mating plug with 9 mm insertion depth. Terminal 1 is centre positive; terminal 3 is the sleeve/ground; terminal 2 is the switched sleeve and is intentionally not connected. This numbering differs from the old GCT symbol and was changed in the local schematic symbol, embedded symbol and native PCB.

The drawing's top-view centres relative to terminal 1 are terminal 2: -5.9 mm along the jack axis, terminal 3: -3.0 mm axially / +4.7 mm transversely. All three plated slots are 1.0 x 3.5 mm; land sizes add a nominal 0.5 mm annular margin and both solder masks have 0.05 mm expansion. The body is 14 x 9 x 11 mm. The courtyard follows the body and protruding side terminal separately; this avoids falsely reserving a rectangular empty corner next to R10.

Terminal 1 remains at the old power entry location. All reviewed main power, USB data, protection-gate and fault tracks remain exactly identical. Four old ground spokes to the obsolete sleeve location were removed; the refilled ground planes connect the new sleeve. KiCad connectivity and DRC must pass after this change.

## Assembly and release files

Factory population is **70 components: 63 SMT plus 7 THT**, on the top side. The seven THT components have 23 solder joints per board. USB-C shell joints are part of the factory USB assembly. No separately purchased soldered components remain in this variant.

Upload `manufacturing/windpcb-revb-gerbers.zip`, `manufacturing/assembly/PCBA-BOM.csv` and `manufacturing/assembly/PCBA-CPL.csv`. The full BOM has 33 part-number groups and the CPL has 70 references. `SMT-BOM.csv` and `SMT-CPL.csv` remain partial reference exports, not the full-assembly ordering inputs. `HAND-BOM.csv` is intentionally empty except for its header.

The Gerber ZIP now includes `windpcb-F_Paste.gtp`, so the corrected B.1 U4 stencil geometry is actually supplied with the assembly upload. Preserve that paste data and request placement/stencil confirmation. The prescribed stencil thickness remains 0.100 mm. Factory process acceptance is distinct from CAD checks.

The live JLC preview revealed that the THT library origins differ from KiCad pin-one origins. PCBA-CPL.csv now places capacitors at the lead midpoint, fan headers at the four-pin row midpoint, and the XKB jack at its pad-array midpoint with the JLC-specific 0-degree rotation. The final jack body, sleeve slot, capacitor polarity and four keyed header placements were visually checked against the Gerber overlay. These are supplier-file corrections; native footprint positions and copper did not move. See MANUFACTURING.md for exact offsets.

## Power supply selection

Use a regulated, enclosed, isolated 12 V DC supply, at least 3 A, EU mains plug for Norway, centre-positive 5.5 x 2.1 mm DC plug. A 12 V 4 A or 5 A unit is also acceptable if its voltage/ripple meet the design requirements; its current rating does not force extra current into the fans. Do not select a 2.5 mm centre-hole plug or a 24 V supply.

Mean Well GST36E12-P1J is an established example of this physical format: 12 V / 3 A, EU wall adapter, P1J 5.5 x 2.1 mm centre-positive plug. It is a connector/form-factor reference, not a tested or purchased supply for this project. Its specified +/-3% voltage tolerance does not guarantee the project's tighter 11.70-12.30 V acceptance target; check the chosen unit under load and startup rather than assuming the model name establishes compliance. Ripple target is at most 120 mV peak-to-peak. The PCB filters noise and cuts off overvoltage; it does not regulate the fan rail to 12 V.

AliExpress access was blocked by browser policy. The user will source a matching supply separately; no AliExpress cart action or purchase was performed.

## Render and validation scope

J1, J2 and U4 now have local, representative dimensioned 3D bodies for a populated preview. These are visual aids, not vendor-certified clearance models. C9's original capacitor model is scaled in height to 12.5 mm. The drawing, copper, drills and courtyards remain the mechanical manufacturing authority.

The B.1 electrical audit and simulations remain applicable because the controller topology and reservoir capacitance are unchanged. Rerun ERC, full DRC with schematic parity, all physical pad net checks, both-face PTH mask checks, U4 actual Gerber paste geometry, protected-route equality and the new jack/CPL audit. Hardware startup, thermal, EMI and firmware acceptance are still required on the manufactured boards. Production Zephyr firmware is specified, not yet implemented.

The old $82.72 quote is historical and does not cover B.2. Use the separately recorded B.2 full-assembly quote when available. No order or payment is authorized.

## Sources

- [XKB JLC listing](https://jlcpcb.com/partdetail/XKBConnection-DC_005_5A_20/C381116)
- [Panasonic C9 specifications](https://industrial.panasonic.com/ww/products/pt/aluminum-cap-lead/models/EEUFR1E471)
- [Panasonic C6](https://jlcpcb.com/partdetail/PANASONIC-EEUFR1H470/C407950)
- [Molex fan header](https://jlcpcb.com/partdetail/MOLEX-470531000/C240840)
- [HRO USB-C](https://jlcpcb.com/partdetail/C165948)
- [Mean Well GST36E datasheet](https://www.meanwell.com/Upload/PDF/GST36E/GST36E-SPEC.PDF)
