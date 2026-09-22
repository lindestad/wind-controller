# LINDESTAD wind controller

Zephyr application for WindPCB B.3, ESP32-C3-WROOM-02-N4, four ARCTIC P14 Pro PST fans. Uses native USB Serial/JTAG, four 25 kHz hardware PWM outputs and four tach inputs. No external programmer is required for blank-flash recovery.

This implements the hardware-dependent startup and shutdown contract, with host-executed tests. On 22 September 2026 the first board was flashed, USB communication was stable, and the user confirmed one L1 fan started and stopped during a two-second test. Electrical timing, tach pulse rate, low-speed stability, watchdog reset pin states and temperature still need first-board qualification.

## Build

Windows workspace: `../wind-zephyr`, pinned to Zephyr **v4.4.2**. The required complete Zephyr SDK **1.0.1** is installed under `~/zephyr-sdk-1.0.1`. This project is a separate Git repository; SDK and dependency repositories are outside it.

```powershell
./scripts/build.ps1 -Pristine
../wind-zephyr/.venv/Scripts/python.exe tests/test_control.py
```

`build/zephyr/zephyr.bin` is the application build output. Use the Zephyr runner's generated flash configuration rather than guessing offsets. Build provenance and configuration checks are recorded in `reports/`. See `docs/validation.md` for scope and hardware acceptance items.

To recreate dependencies, create a Python 3.12 virtual environment in `../wind-zephyr/.venv`, install `west`, initialize the official Zephyr manifest at v4.4.2, run `west update`, install `zephyr/scripts/requirements.txt`, and run `west blobs fetch hal_espressif`. Use SDK 1.0.1. The frozen manifest is stored in `reports/west-frozen.yml`. No global Zephyr workspace was changed.

## USB and SimHub

Hold BOOT, press/release RESET, release BOOT. The ROM downloader should enumerate through USB-C even if application flash is blank. Connect a data-capable cable; barrel power is unnecessary for flashing. Run `west flash --esp-device COMx` from this workspace with the build directory specified, then press RESET if needed. The exact runner command is documented by `west flash -H -r esp32` and must match the installed esptool version. No eFuse/security programming or UART bridge is required.

Use SimHub **Custom Serial Devices**, sending ASCII `W,<left>,<right>\n` with integer demands 0–1000. The final character is one LF byte. Send every 100 ms or faster, including unchanged values. There is no Arduino/ShakeIt protocol emulation. USB returns the structured status frames below; Zephyr console/log noise remains disabled. Displaying warnings in SimHub needs a receiver/integration; transmission alone does not create a SimHub warning UI.

Zero and demands below 50 stop that side. A nonzero request first precharges for 750 ms, then attempts the commanded headers individually. Each gets a 250 ms full-speed kick; the next starts after at least 500 ms and three new filtered tach edges, or after a 2 s timeout if tach is absent. That timeout raises a per-header warning and advances the sequence, without stopping any output. Losing tach for 2 s after startup also warns while maintaining the requested duty. One to four fans may occupy any headers; no fan-count setting is required. Even zero fans produces warnings rather than a shutdown. Missing headers can delay later fans by 2 s each (up to 6.75 s from command to the fourth header's kick).

An empty header, stalled motor and broken tach wire cannot be distinguished electrically. Warnings mean **no tach while commanded**, not a confirmed missing fan. There are no repeated automatic startup kicks. Three new edges clear a warning; stopping that side clears its warning and the next start checks again. Do not hot-plug fans; switch off supplies before moving connectors.

Every 500 ms, USB transmits `S,1,<mode>,<mask>\n` (8 ASCII bytes). Version is 1; mode is `0` off, `1` precharging, `2` active (including warnings), `3` command timeout, or `4` fault. Mask is one uppercase hexadecimal digit: bits `1/2/4/8` correspond to L1/L2/R1/R2 without tach. For example `S,1,2,A\n` means active, with L2 and R2 warnings. Warnings are live and only apply after a startup attempt, so a clear mask at boot does not prove a fan is connected. STATUS stays lit when fan power is enabled. The red FAULT LED remains controlled by the hardware eFuse, not these firmware warnings.

Status transmission uses a bounded interrupt-driven buffer; a host that stops reading cannot block the control loop or command timeout. Pending reports can be stale after a host pause; a receiver must wait for fresh periodic reports before relying on them. Reports describe requested controller state, not measured fan-supply voltage or verified motor motion.

Only valid complete demand frames refresh the 500 ms command deadline. Overlong, malformed and partial frames are rejected. RX-budget saturation and output failures still stop operation and require reset; warnings do not bypass these protections. Commanded stop sets all PWM inputs low before removing fan power. Abrupt USB loss/reset can still cause the documented brief capacitor-powered twitch/coasting.

## Extended telemetry

Extended telemetry is also sent about once per second: `T,2,<mode>,<warning_hex>,<uptime_ms>,<accepted>,<rejected>,<rpm_L1>,<rpm_L2>,<rpm_R1>,<rpm_R2>,<pwm_L1>,<pwm_L2>,<pwm_R1>,<pwm_R2>\n`. RPM uses edge-count differences over the actual sample interval and assumes two pulses per revolution; absolute accuracy needs independent measurement. PWM values are per-header 0–1000 output demands including startup kicks. No supply voltage/current/temperature measurement exists. The existing S1 reports remain unchanged; consumers should ignore recognized additional report types. Rig Companion now owns USB and receives SimHub vehicle speed through its localhost bridge; see `C:\Users\danie\dev\rig-companion\docs\wind-simulator.md`.

## Routine firmware updates

After building, close SimHub/other serial programs and run `./scripts/flash.ps1 -Port COM4` (substitute the current port). The helper sends stop commands, requires repeated OFF reports for two seconds, then invokes the generated Zephyr flash runner. It aborts if it cannot confirm OFF. Firmware starts with fan power disabled and needs a new valid demand before running. Never resume the command sender during flashing.

The board's external enable pull-down is intended to keep incoming fan power off in ROM download/reset. This makes leaving 12 V connected a supported design intent for routine updates with the stop-first helper, **not a measured guarantee of no movement**: the MCU cannot measure output capacitor voltage, and reset can release PWM before stored energy drains. Disconnect 12 V whenever zero fan movement matters, or for blank/corrupt firmware recovery. The helper cannot work on older firmware without status reports. Hold BOOT/RESET and use the ordinary Zephyr runner with 12 V disconnected in that case.

The watchdog requests a whole-system reset. The ESP32 driver uses an interrupt stage followed by a reset stage; a configured 500 ms stage interval is approximately 1 s to hardware reset, not a 500 ms reset guarantee. The ordinary command timeout runs separately. No hardware runtime timing guarantee is claimed before measurement.

## Pin map

| Function | GPIO |
|---|---|
| L1/L2/R1/R2 PWM sink gates | 4 / 5 / 6 / 7 |
| L1/L2/R1/R2 tach | 0 / 1 / 3 / 20 |
| Fan power enable | 10 |
| Status LED | 21 |
| Native USB D− / D+ | 18 / 19 |
| BOOT | 9 |
| Reserved boot straps | 2 / 8 |

The DTS uses the WROOM N4 module definition, not a development board with UART0 on GPIO20/21. UART0/1, radios, logging and power management are disabled. The eFuse FLT signal is not wired to the MCU, so firmware cannot classify its faults or measure supply voltage/current.

The LEDC child `inverted` property initializes the stopped output high. Runtime requests use normal polarity and `(1000 − fan_demand) × 40 ns` gate pulse width; the transistor provides the physical inversion. The pinned driver's implementation was checked to distinguish initial idle level from runtime polarity flags.
