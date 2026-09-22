# Wind simulator controller — hardware specification

Revision B.3, 7 September 2026. Compact black PCB with LINDESTAD branding, updated factory-assembled jack and capacitors, and full assembly BOM/CPL. See REVISION-B3.md for the 5.5/2.5 mm TDX-compatible jack and REVISION-B2.md for other sourcing decisions and the previous REVIEW-RESOLUTION.md for retained electrical fixes. Design checks reduce risk; supplier process review and first-hardware qualification remain outstanding.

## Purpose and scope

One USB-connected controller operates four ARCTIC P14 Pro PST 12 V, four-wire PWM fans, one per header with their PST expansion sockets unused arranged as two funnels. SimHub supplies commands; Zephyr RTOS runs on the controller. Four independent physical PWM channels are grouped into left/right pairs in software. This project includes the native KiCad schematic and PCB, BOM, design calculations and verification records. Firmware is implemented in the separate local repository `repository root` (commit `6777767`), built against Zephyr v4.4.2 and tested in software. Its electrical interface and recovery requirements are specified here; actual-board testing remains outstanding.

The first PCB order is intended to produce usable boards, without a separate breadboard/carrier prototype. Simulation and design checks reduce risk but do not replace electrical tests on the manufactured board. No hardware performance or compliance certification is implied by a clean ERC/DRC report.

## Controller and USB

- Espressif ESP32-C3-WROOM-02-N4 module with 4 MB flash, factory assembled on the PCB. Perimeter pads and a factory-built RF/flash subsystem avoid designing a bare-chip RF circuit. See `FIRMWARE.md` for the pin map.
- Zephyr support based on the ESP32-C3 SoC, with a board-specific pin configuration. Radios disabled for normal wired operation.
- USB-C USB 2.0 full-speed data connection through the built-in USB Serial/JTAG interface. Separate 5.1 kohm CC1/CC2 pull-downs, USB ESD protection and short D+/D- routing.
- Controller powered from USB 5 V through a 3.3 V regulator; fans powered only from the barrel input. Grounds are common. No connection between barrel positive and USB VBUS.
- Physical BOOT and RESET pushbuttons. Hold BOOT, press/release RESET, then release BOOT to enter the ROM downloader. Recovery must work on a blank device and independently of Zephyr. USB-only programming must work without fan power.
- BOOT/strapping resistors and EN timing follow Espressif guidance. Native USB reserves GPIO18/19. Do not disable the ROM downloader or burn security eFuses as part of normal provisioning.
- USB suspend, enumeration current and bus-powered consumption must be validated with the firmware; regulator capacity alone is not USB power authorization.

## Fan interfaces

- Four keyed 2.54 mm PC fan headers: pin 1 GND, pin 2 switched +12 V, pin 3 tachometer, pin 4 PWM.
- Nominal fan current 0.35 A each; 1.4 A / 16.8 W combined. Design the common power path for at least 3 A and individual branches for at least 0.75 A.
- PWM frequency 25 kHz, allowed fan range 21–28 kHz. Four transistor open-drain outputs isolate MCU pins from fan pull-ups; firmware accounts for inversion. Design for at least 5 mA sink per fan, low below 0.8 V. Never apply 12 V to PWM.
- Separate tachometer inputs use Q6–Q9 common-gate SI2312-TP level shifters, with 2.2k pull-ups on the MCU side; raw fan signals have no direct resistor path to the MCU rail. Confirm actual fan tach behaviour on first hardware. Two pulses/revolution is an initial firmware assumption to verify.
- Fans specified to stop below 5% PWM. Initialization holds PWM low before enabling fan power. A hardware-default-off enable removes incoming fan power while USB/MCU is absent or resetting. Stored output energy can cause brief residual motion or a twitch; this is not an instantaneous safety stop.

## Power input, filtering and protection

- Center-positive 5.5/2.5 mm XKB DC-005-5A-2.5 barrel jack, catalogue-rated 5 A. Pin 1 is centre positive, pin 3 sleeve ground, pin 2 switched sleeve unused. External regulated 12 V / 3 A supply. Normal design input target 11.70–12.30 V including ripple, with at most 120 mV peak-to-peak ripple at the board; this is a controller/supply target, not an ARCTIC guaranteed fan tolerance.
- Reverse-polarity protection, bulk and ceramic decoupling, and provision for high-frequency filtering. Filter component ratings and damping must be checked; capacitors do not correct sustained DC error or large low-frequency ripple.
- TPS25970LRPWR electronic fuse: resistor-adjustable overvoltage cutoff, active current limiting, controlled power-on slew and separate enable. R11 = 97.6 kohm / R12 = 10 kohm, both 0.1%, give 12.912 V nominal cutoff. R13 = 2.4 kohm, 1%, gives 2.395 A nominal current limit. See `VALIDATION.md` for tolerance limits.
- Separate enable and OVLO pins; active current limiting followed by a latched shutdown if thermal protection operates. An overvoltage event has hysteretic recovery: nominal re-enable voltage is 11.836 V. Returning to exactly 12 V may require unplugging the barrel supply. Do not assume an MCU reset clears OVLO.
- A hardware pull-down keeps the fan power enable off when the MCU is unpowered or high impedance. Startup must remain off in ROM download mode.
- No full 12 V buck-boost regulation. The input includes a 3 A backup fuse, reverse P-MOSFET with a 9.1 V gate clamp, SMBJ15A TVS, 47 uF / 50 V reservoir, 3.5 A ferrite bead and ceramic bypassing. Output reservoir is 470 uF / 25 V. This is a 12 V adapter design, not a universal 24 V input; see the bounded fault assumptions in `VALIDATION.md`.
- Protection threshold adjustment is by resistor substitution, not an exposed user potentiometer.
- C8 = 100 nF and R40 = 100 ohms in series set an approximately 364 ms output ramp. Hold all PWM low for 750 ms after enabling, then start the individual motors sequentially. Current limiting is unchanged.
- Q2–Q9 are MCC SI2312-TP / C6488168, specified at 1.8 V gate drive. Q2–Q5 sink PWM; Q6–Q9 translate tach without inversion. R19 = 1k discharges the 3.3 V rail.

## Firmware contract

- USB serial integration through SimHub Custom Serial Devices initially. Serial enumeration is not automatic compatibility with SimHub's Arduino/ShakeIt protocol.
- Proposed framed ASCII command: `W,<left 0..1000>,<right 0..1000>\n`, periodically sent even when unchanged. Map each side to two PWM channels.
- Reject malformed/out-of-range commands. No fan startup on random serial data, debug logs or device connection alone.
- Start only after a valid command; hardware enforces the overvoltage cutoff. There is no MCU supply-voltage measurement or per-fan current sensing. On stale commands (500 ms initial target), disable fan power. Zero/zero also disables fan power after the PWM stop command.
- Define separate diagnostics and do not mix unsolicited Zephyr console output into the command stream. Require a whole-system watchdog reset with GPIO/peripheral hold disabled; a CPU-only reset is not sufficient.
- Final firmware must test native USB serial, hardware PWM, GPIO/tach interrupts, watchdog and boot recovery on this PCB.

## Mechanical, appearance and assembly

- 70 × 64 mm rectangle, two layers, 1.6 mm FR-4, 1 oz copper. Black solder mask on both faces, white silkscreen. Native slanted LINDESTAD lettering and three wind strokes on the top face; WIND / REV B.3 identification.
- Four 3.2 mm M3 mounting holes with 63 × 57 mm centre spacing. Two separate 1.152 mm assembly tooling holes. Exact locations, mask expansion and ordering instructions are in `MANUFACTURING.md`.
- Four keyed fan headers remain on a 15 mm pitch; their pin-one row is 53 mm from the top edge. Barrel exits left and USB-C right, at their A.1 positions. Both buttons and all plugs remain accessible.
- Move C6 positive pad to (7,26) mm and C9 to (6,36) mm from top-left. Body centres are respectively (8.25,26) and (8.5,36) mm. C6 body diameter 6.3 mm / height 11.2 mm; C9 diameter 10 mm / height 12.5 mm. These are distinct from CPL component origins.
- Factory assembly includes 70 components: 63 SMT and seven through-hole parts (J1, J3–J6, C6 and C9). No user soldering is planned. The four optional PWM pull-up footprints have been removed. Six test points and six holes require no purchased parts.
- Status D3 uses Basic KT-0805G / C2297, green 0805; fault D4 remains Basic KT-0603R / C2286, red 0603. The status brightness must be checked at the retained low-current drive. All 70 purchased components carry specific supplier codes.
- Plated minimum drill 0.3 mm. Module thermal copper lands increased to 0.7 mm for a 0.2 mm annular ring. Preserve the module antenna keepout and the segmented paste geometry.

## Manufacturing process and cost target

Black lead-free HASL / JLC Economic top-side assembly is the cost-oriented candidate, subject to the assembler accepting the U4 fine-pitch process. Black ENIG is an alternative requiring Standard assembly and an additional rail/panel design. See `MANUFACTURING.md`; neither process is approved for production by this design check.

The historical revision B JLC quote obtained through the browser on 6 September 2026 was **USD 82.72 before shipping/tax for five PCBs / two SMT assembled**, black lead-free HASL / Economic. Fabrication is $5.20 and SMT parts/assembly $77.52. The two Basic substitutions reduce Extended fees by $6.14 versus A.1. No order was placed; supplier DFM and stock at purchase remain outstanding. Through-hole purchases, power supply, fans, enclosure and firmware work are excluded. See [quote evidence](reports/jlcpcb/QUOTE.md) and `REVISION-B.md` for the comparison and alternative ENIG route.

## Verification and release

The final B cleanup moves TP5 to (46.5, 34.5) mm from the top-left and aligns FAULT right of D4 and STATUS left of D3. Soldered PTH pads require both-face mask openings with 0.05 mm expansion: 23 hand joints and four USB shell attachments. This has been corrected and independently checked in the mask Gerbers. See `FINAL-CLEANUP.md`, the executed `reports/preorder-review/REPORT.md`, and `REVIEW-RESOLUTION.md`. The quoted $82.72 upload predates these changes.

Before manufacture: clean ERC/DRC, exact pad connectivity, schematic/PCB metadata agreement, courtyard/mount/tooling-hole review, manufacturing-file origin and counts, colour and silkscreen inspection, and updated OVLO/current-limit calculations. The full verification record and limitations are in `VALIDATION.md`.

The nominal current limit is 2.395 A. Calculated IC/resistor tolerance corners are 2.134–2.661 A; including the selected resistor's 100 ppm/°C allowance over a -20 to +70 °C calculation gives 2.124–2.673 A. This calculation is not a board operating-temperature qualification or a guarantee of actual fan startup.

First hardware must test blank-device USB flashing, boot recovery, default-off power sequencing, PWM/tach behaviour, supply ripple, all-fan startup, cutoff/current limiting and thermal behaviour. Preserve the acceptance-test list in `VALIDATION.md`. Software feasibility now passes; see `reports/final-checks/REPORT.md` for the build/test evidence and remaining hardware limitations.

## References

- [ARCTIC P14 Pro PST](https://support.arctic.de/en/p14-pro-pst)
- [Espressif ESP32-C3 module](https://www.espressif.com/sites/default/files/documentation/esp32-c3-wroom-02_datasheet_en.pdf)
- [TI TPS2597](https://www.ti.com/lit/ds/symlink/tps2597.pdf)
- [Zephyr ESP32-C3](https://docs.zephyrproject.org/latest/boards/espressif/esp32c3_devkitm/doc/index.html)
- [SimHub Custom Serial Devices](https://github.com/SHWotever/SimHub/wiki/Custom-serial-devices)
- JLC process, tooling, catalogue and pricing sources are linked beside the relevant decisions in `MANUFACTURING.md` and `REVISION-B.md`.

## B.1 manufacturing correction

U4 uses TI-dimensioned split/reduced paste apertures for a 0.100 mm stencil. Copper lands are unchanged; supplier stencil and placement confirmation remains required. Graphical silkscreen is at least 0.15 mm. See [review decisions and remaining limits](REVIEW-RESOLUTION.md).
