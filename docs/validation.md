# Pre-order firmware verification

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
