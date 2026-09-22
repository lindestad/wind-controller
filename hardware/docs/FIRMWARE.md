# Zephyr and SimHub interface

Hardware revision B.3 uses ESP32-C3-WROOM-02-N4 (4 MB flash). Firmware is implemented in the separate local Git repository [wind-controller](../../README.md), commit `6777767`. On 7 September 2026 the actual custom-board build passed with Zephyr v4.4.2 and SDK 1.0.1; 19 host tests and 42 generated-build/hardware-pin checks passed. This is software feasibility evidence, not a test on manufactured hardware. The native USB Serial/JTAG peripheral supports the ROM downloader independently of application firmware; no external USB-UART or debug probe is required.

## Pin map

| Signal | ESP32-C3 GPIO | Module pad | Behaviour |
|---|---:|---:|---|
| L1 PWM drive | 4 | 3 | Transistor gate, inverted relative to fan PWM |
| L2 PWM drive | 5 | 4 | Same |
| R1 PWM drive | 6 | 5 | Same |
| R2 PWM drive | 7 | 6 | Same |
| Fan power enable | 10 | 10 | High enables eFuse; external pull-down and RC |
| L1 tach | 0 | 18 | Non-inverting MOSFET-translated input, 2.2k to 3.3 V |
| L2 tach | 1 | 17 | Same |
| R1 tach | 3 | 15 | Same |
| R2 tach | 20 | 11 | Same; do not enable UART RX here |
| Status LED | 21 | 12 | High lights green LED; ROM UART TX may pulse it |
| USB D− | 18 | 13 | Dedicated native USB |
| USB D+ | 19 | 14 | Dedicated native USB |
| BOOT | 9 | 8 | Pull-up, button shorts to ground |
| Other boot straps | 8 / 2 | 7 / 16 | Pull-ups; reserve these GPIOs |
| RESET | EN | 2 | Pull-up/RC, button shorts to ground |

The red FAULT LED and TP5 report the eFuse fault signal. **It is not connected to an MCU input.** The hardware has no voltage ADC, current telemetry or automatic fault classification. Tach readings can detect a fan that remains stopped after a commanded startup, but cannot identify every cause.

## First flash and recovery

1. Connect USB-C with a data-capable cable; barrel power is unnecessary.
2. Hold BOOT, press and release RESET, then release BOOT. This enters the ROM USB downloader even with blank or broken firmware.
3. Flash through the enumerated USB serial port using Zephyr's Espressif runner/esptool. The implemented custom board target is `wind_controller/esp32c3`, with 4 MB flash and this pin map. Build instructions and generated-runner evidence are in the firmware repository.
4. Press RESET to run. If the runner leaves the C3 in download mode, use its documented watchdog-reset option or press RESET; ordinary serial RTS/DTR assumptions from USB-UART boards do not always apply.

Do not disable ROM download mode, USB Serial/JTAG, or burn security eFuses during ordinary provisioning. Do not use deep sleep, which can disconnect native USB. A COM port is expected; arbitrary USB HID/composite emulation is not the purpose of the C3's fixed Serial/JTAG peripheral.

## Required application behaviour

- Disable radios and configure the native USB Serial/JTAG UART driver; do not blindly reuse the DevKitM external UART console configuration. Keep diagnostic logging out of the command stream.
- Leave fan enable low during all initialization. Configure four LEDC PWM outputs at 25 kHz, initially with their **GPIO gates high**, which holds the fan PWM pins low. Enable power only after a valid command. Hold all four PWM pins at zero for 750 ms after enable, allowing the approximately 364 ms nominal ramp to finish. Then start individual fans as described below; actual spin-up takes longer.
- A 100% fan command means the transistor remains off (gate low). A 0% fan command means gate high. PWM flags or duty conversion must account for this inversion exactly once.
- Use hardware PWM, not a thread repeatedly toggling GPIOs. All four outputs use the same frequency and can share a suitable timer.
- Tach inputs are independent. Start with two pulses per revolution, verify on the actual fans, and calculate `RPM = pulse_frequency × 30` only after that verification. Debounce/filter implausibly short pulses in software.
- Never start on enumeration, console noise, malformed input or button use alone. Reject out-of-range values and overlong frames. Use a whole-system watchdog reset, no GPIO hold and no retained PWM/enable state. CPU-only reset is insufficient. Verify the actual reset domain and pin waveforms on hardware.
- Initial command timeout: 500 ms. On timeout, command PWM stop and disable fan power. No endless fault auto-retry. Output capacitance discharges over time; electrical power removal is not instantaneous.

## SimHub contract

Use **Custom Serial Devices**, with the implemented frame `W,<left>,<right>\n`, where both values are integers 0–1000. Examples: `W,0,0\n`, `W,500,500\n`, `W,1000,700\n`. The `\n` here denotes an actual LF byte, not two literal characters. End-to-end SimHub/USB operation remains a first-board check.

Send complete fresh frames at 10 Hz or faster, even if unchanged; disable Changes only. A paid SimHub configuration may use 20 Hz. Malformed or partial traffic must never refresh the 500 ms timer. Map left to L1/L2 and right to R1/R2. SimHub's actual wind-effect expressions and the Zephyr parser must be implemented and tested together. A serial port alone does not implement SimHub's Arduino/ShakeIt protocol; no compatibility with that protocol is claimed.

References: [Zephyr ESP32-C3](https://docs.zephyrproject.org/latest/boards/espressif/esp32c3_devkitm/doc/index.html), [Espressif native USB](https://docs.espressif.com/projects/esp-idf/en/stable/esp32c3/api-guides/usb-serial-jtag-console.html), [SimHub Custom Serial Devices](https://github.com/SHWotever/SimHub/wiki/Custom-serial-devices).

## B.1 startup, stop and fault sequence

The following contract is implemented in the separate firmware repository. Updated 22 September 2026: missing/stalled tach is a warning rather than a global shutdown, allowing any number of fans. The current firmware passes 25 host tests and 43 build checks and has been flashed and USB-tested on the first board. See the firmware repository's `docs/validation.md` for exact physical-test scope.

1. Earliest initialization: FAN_ENABLE low, four PWM sink gates high, radios disabled. Disable UART0 on the reused tach/status pins and reserve the native USB pins. Do not assert fan enable in bootloader or console initialization.
2. A complete valid nonzero frame starts PRECHARGE: keep all fan PWM pins low, assert enable and wait 750 ms. Continue processing command freshness throughout the wait; never sleep in a way that blocks the safety loop. Zero/zero or a 500 ms timeout immediately takes the stop path.
3. Attempt one commanded header at a time, in L1, L2, R1, R2 order. Apply a 250 ms 100% startup kick, then transition to requested duty. Advance after three new filtered tach edges and at least 500 ms, or after 2 s without qualified tach. On timeout set a no-tach warning for that header and continue starting the others; keep its requested PWM without repeated kicks. These provisional timing limits must be calibrated on the actual P14 Pro PST. Skip a stopped side.
4. Valid recurring frames update targets/freshness without restarting the precharge timer or startup stage. If a previously stopped fan is requested while others run, pass it through the same sequential startup queue. Never assume simultaneous motors' startup current equals their rated current.
5. Stop path: drive all four sink gates high (fan PWM = 0%), then deassert enable. A safety-loop service interval at most 10 ms gives an intended stale-command response within 510 ms of the last completed valid frame. Keep PWM low while logic power remains. On abrupt reset or USB loss, stored capacitor energy may cause a brief twitch/coasting; no instantaneous mechanical-stop promise is made.
6. Tach loss for 2 s raises a per-header warning and leaves outputs running. Three new edges clear it; stopping a side clears its warnings and a later start checks again. Missing fan, stall and broken tach wire cannot be distinguished. RX-budget exhaustion and actuator failures still stop operation and require reset. U4 FLT is not connected to the MCU, and OVLO does not assert FLT: tach alone cannot classify power faults. OVLO may require barrel power cycling.
7. Feed the hardware watchdog only when the control/safety loop is healthy. Logging, USB congestion or parser work must not block deadlines. On recovery discard buffered commands. The simple W frame has no session authentication or anti-replay claim; neither is required for this locally connected accessory.

Tach polarity is unchanged by the common-gate level shifters. Two pulses/revolution remains a first-board measurement, not a guaranteed value inferred from connector convention.

USB now transmits `S,1,<mode>,<mask>\n` every 500 ms using bounded interrupt-driven TX. Mode 0=OFF, 1=PRECHARGE, 2=ACTIVE (possibly warning), 3=STALE, 4=FAULT. Mask is one uppercase hexadecimal digit with L1/L2/R1/R2 bits 1/2/4/8. Console logging remains disabled. A warning display in SimHub requires receiver integration. STATUS still indicates requested fan power; FAULT is still the independent hardware LED.

For routine updates, the firmware repository provides `scripts/flash.ps1 -Port COM4`: send stop, require repeated OFF reports for two seconds, then run the generated Zephyr flash command. USB powers the MCU independently of the 12 V fan rail, so normal 12 V power may remain connected during flashing. ROM recovery is retained and no security/eFuse settings are changed. Reset may allow brief residual fan movement; unplug 12 V if no movement is required. The helper cannot confirm OFF on older, blank or broken firmware; use BOOT/RESET recovery in that case.
