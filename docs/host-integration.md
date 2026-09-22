# SimHub and Rig Companion

The Windows UI is maintained in [lindestad/rig-companion](https://github.com/lindestad/rig-companion).
It owns the physical USB serial port, displays fan RPM/warnings and maps vehicle speed
to left/right PWM demand. The firmware remains responsible for startup sequencing,
tach warnings, watchdog and command timeout.

## Recreate the software setup

1. Clone Rig Companion and follow its README to build/install the Windows app with Rust.
2. Install SimHub. The tested SDK/runtime is **SimHub 9.12.4**, .NET Framework 4.8.
3. Build the bridge source included in `integrations/simhub`:
   `dotnet build integrations/simhub/RigCompanion.WindBridge.csproj -c Release`.
   Pass `-p:SimHubPath=...` for a non-default SimHub installation. Proprietary SDK DLLs
   are referenced from that installation and are not redistributed here.
4. Exit SimHub and copy the built `RigCompanion.WindBridge.dll` to the SimHub directory.
   Start SimHub and enable **Rig Companion Wind Bridge** in its plugin list.
5. Connect the board with a USB data cable, open Rig Companion's Wind simulator page,
   choose channels/run mode/limits/curve, and apply. No virtual COM driver is needed.
   Do not configure SimHub to open this same physical COM port.

The bridge snapshot is maintained upstream in Rig Companion. Update both PC programs
together: protocol v2 adds game and car identity to the v1 speed-only heartbeat.
Only loopback UDP `127.0.0.1:29814` is used, at 100 ms intervals:

```json
{"version":2,"running":true,"speed_kmh":123.4,"game":"IRacing","car_id":"formulavee","car_model":"Formula Vee","car_class":"Formula Vee"}
```

The companion bundles approximate iRacing car top speeds. Full curve output occurs at
estimated top speed **minus 15 km/h**, capped by the selected maximum fan percentage.
The default curve exponent is 0.60; 1.00 is linear. The UI graph and slider edit the
curve, and a manual estimate handles unknown cars or unusual setups. Missing/stale
game data produces minimum airflow within the selected run mode. See the companion's
`docs/wind-car-speeds.md` for sources, formula, fallback rules and validation.

Firmware commands remain `W,left,right\n`, with each demand 0–1000. Any custom host
can implement this protocol directly; keep commands flowing every 100 ms. This source
repository contains the full board and firmware; the companion repository contains
the complete application rather than a copied, diverging second application tree.
