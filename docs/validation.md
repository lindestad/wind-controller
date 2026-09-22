# Pre-order firmware verification

## 22 September 2026 update: optional fans and USB warnings

The current firmware supersedes the original tach-fault shutdown behaviour described in the historical pre-order results below. Startup without tach and tach loss now set per-header warnings while all commanded outputs continue. The next header starts after either confirmed tach plus 500 ms, or a 2 s timeout. Zero through four connected fans are supported. Command loss, RX-budget exhaustion, actuator failure and the existing hardware power protections are unchanged.

- 25 actual-C host tests PASS, covering all 16 populations of connected fans; no-tach startup progression; one running fan losing tach; three-edge warning recovery; side stop/restart; timer wrap; status encoding; command expiry and hard faults while warnings are present. The original parser/random-traffic/output tests remain included.
- Zephyr target build PASS, 43 configuration/pin/image checks PASS; image size 133,876 bytes. Added interrupt-driven USB TX so status reports do not use blocking character writes in the control loop.
- Flashed on COM4 using the generated Zephyr runner; esptool verified the flash hash (`reports/warning-firmware-flash.log`). No eFuse/security settings were changed.
- Actual-board USB test PASS with **12 V physically disconnected**: repeated OFF reports, precharge, sequential warning masks 1/3/7/F while remaining ACTIVE, command-timeout state, then explicit OFF. Evidence: `reports/warning-usb-smoke.json`; rerun with `tests/usb_smoke.py --port COM4 --no-fan-power` only after physically disconnecting the barrel supply. This tests actual application execution/USB but cannot prove fan voltage, motor rotation or electrical timing.
- The complete stop-before-flash helper was exercised against the board: repeated OFF snapshots for two seconds, successful hash-verified flashing, automatic reset, and OFF reports afterwards (`reports/stop-first-flash.log`). OFF telemetry describes requested outputs; it cannot measure whether the capacitors are discharged. This test used USB only; flashing with 12 V attached has not been physically tested.
- Before this update, the user confirmed that the original firmware started and stopped a single L1 fan during a two-second command test. A sustained two-fan test of the new warning behaviour is still pending.

Remaining checks include real tach warning/recovery with powered motors, both sides, measured output timing and watchdog reset, prolonged USB TX backpressure, current/thermal behaviour and SimHub end-to-end integration. A successful USB status test does not close those items. Routine flashing with the normal 12 V supply connected does not introduce a separate electrical damage or permanent-bricking mechanism; USB supplies the MCU, and ROM download recovery remains enabled. Supply faults and USB interruption are separate from fan motion; an interrupted write normally needs reflashing.

### RPM integration update, 22 September

Added one-second T2 telemetry (per-header estimated RPM/output, uptime, command counters). RPM computation uses actual window duration and 64-bit arithmetic; output formatting is bounded. The existing S1 status frames are retained and the stop-first flash helper ignores T2 records. 26 host tests and 43 target checks PASS. Firmware was hash-verified when flashed with 12 V connected, and actual COM4 idle telemetry returned valid 15-field T2 frames (`reports/rpm-usb-idle.json`). Rig Companion's live smoke test subsequently passed telemetry, SimHub heartbeat, zero requested output, release/reconnect and shutdown. This update does not claim independently measured RPM accuracy or a powered vehicle-speed test.

## Historical pre-order results

7 September 2026, WindPCB B.3. **Software feasibility checks PASS.** These establish a buildable implementation for the existing pins, not physical operation of unmanufactured hardware.

- Clean target build: Zephyr v4.4.2, commit `dccb09599635bdff17633fa7e9dab014b91dce90`, SDK 1.0.1 / RISC-V GCC 14.3.0, Python 3.12.10, west 1.5.0, esptool 5.4.0.
- 42 generated configuration/pin-map/image checks pass. Exact ESP32-C3-WROOM-02-N4 and 4 MiB flash; native USB Serial/JTAG; UART0/1 and radios disabled; PWM channels 0–3 on GPIO4–7 at 25 kHz; tach GPIO0/1/3/20, enable GPIO10, status GPIO21. Pin assignments cross-checked against B.3 master CAD data.
- 19 tests execute the actual control and output C sources using host GCC with warnings treated as errors. They include 20,000 cases checked against an independent parser oracle and 100,000 seeded random events.
- Behavioural checks cover cold boot, noise, partial/overlong frames, 500 ms freshness, timer wrap, 750 ms precharge, 250 ms kicks, at least 500 ms between fan starts, three new tach edges before advancing, side cancellation/rejoining, startup/stall faults, explicit rearm, output polarity and PWM-stop-before-power-disable ordering.
- Output failure injection confirms the power-disable request occurs immediately after a failed PWM write and no subsequent enable request occurs in that transaction.
- Flash image is 133,780 bytes (about 3.19% of the usable 4 MiB flash region). The generated memory regions overlap physical IRAM/DRAM backing; their percentages must not be summed as independent memory pools.

The prior review's development snapshot and prospective firmware were not reused as production proof. The new custom board definition selects the actual WROOM module and carries no development-board UART pin ownership. Zephyr's LEDC driver was inspected: the DTS `inverted` child property selects the initial stopped output level, while runtime flags overwrite that state. Application requests use normal polarity and explicit inverted gate duty exactly once. The watchdog driver maps RESET_SOC to system reset and uses consecutive interrupt/reset stages; actual pin release and latency remain hardware checks.

Dependency installation fetched all default-active Zephyr manifest modules, all Espressif blobs and both Zephyr/module Python requirements. Optional unrelated module groups are not enabled. The existing complete SDK 1.0.1 matches this release's SDK_VERSION, so it was reused. `west update` ultimately passed and `pip check` found no broken dependencies. A shallow-fetch attempt omitted some pinned commits; fetching those exact manifest revisions and rerunning west resolved this without changing release pins. Other workspaces were not updated.

## Remaining physical checks

Blank-flash ROM USB enumeration and BOOT/RESET recovery; native USB command transport on Windows; real PWM frequency/voltage, tach pulse count and filtering; actual fan standby/startup current and ramp behaviour; low-speed tach stability; watchdog reset effects; output timing under USB load; supply ripple/voltage and enclosure temperatures. The user has no PSU measurement equipment; its label/fit are accepted as a purchasing assumption, not a measured PASS.

No hardware schematic or routing change was required by this firmware work. SimHub's intended Custom Serial Devices frame is documented, but the real SimHub-to-board connection cannot be exercised without the board. The source, tests and reproducible scripts are local Git deliverables; no firmware was flashed and no remote repository was created.
