# LINDESTAD wind controller

Zephyr application for WindPCB B.3, ESP32-C3-WROOM-02-N4, four ARCTIC P14 Pro PST fans. Uses native USB Serial/JTAG, four 25 kHz hardware PWM outputs and four tach inputs. No external programmer is required for blank-flash recovery.

This implements the hardware-dependent startup and shutdown contract, with host-executed tests. It has not been flashed or electrically tested on a manufactured board. Fan startup timing, tach pulse rate, low-speed stability, USB enumeration, watchdog reset pin states and temperature still need first-board qualification.

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

Use SimHub **Custom Serial Devices**, sending ASCII `W,<left>,<right>\n` with integer demands 0–1000. The final character is one LF byte. Send every 100 ms or faster, including unchanged values. There is no Arduino/ShakeIt protocol emulation. USB carries commands only: diagnostics are disabled on the command interface.

Zero and demands below 50 stop that side. A nonzero request first precharges for 750 ms, then starts required fans individually. Each fan gets a 250 ms full-speed kick; at least 500 ms and three filtered tach edges are required before the next starts. Failure to establish tach within 2 s, or 2 s without tach after successful startup, latches off. These starting values require adjustment only if actual fan testing justifies it.

Only valid complete frames refresh the 500 ms command deadline. Overlong, malformed and partial frames are rejected. A recoverable fan fault needs an exact zero/zero command followed by a new nonzero command. RX-budget saturation and output failures require reset; they do not cause endless retry. Commanded stop sets all PWM inputs low before removing fan power. Abrupt USB loss/reset can still cause the documented brief capacitor-powered twitch/coasting.

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
