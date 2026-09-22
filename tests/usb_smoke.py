"""Exercise real USB/status/timeout with the 12 V supply physically disconnected."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import time

import serial
from serial.tools import list_ports

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--port', required=True)
parser.add_argument('--no-fan-power', action='store_true', required=True,
                    help='Confirm 12 V has been physically disconnected')
args = parser.parse_args()
devices = [p for p in list_ports.comports() if p.device == args.port]
assert len(devices) == 1 and (devices[0].vid, devices[0].pid) == (0x303a, 0x1001)
report = {'time': datetime.now().astimezone().isoformat(), 'port': args.port,
          'supply': '12 V disconnected by user; no motor movement test', 'phases': {},
          'status': 'FAIL'}
port = serial.Serial(port=None, baudrate=115200, timeout=0.01, write_timeout=0.5)
port.dtr = port.rts = False
port.port = args.port
port.open()
pending = bytearray()


def phase(name, seconds, command):
    start = next_send = time.monotonic()
    frames = []
    report['phases'][name] = frames
    while time.monotonic() - start < seconds:
        now = time.monotonic()
        if command is not None and now >= next_send:
            assert port.write(command) == len(command)
            next_send = now + 0.1
        pending.extend(port.read(128))
        while b'\n' in pending:
            line, _, tail = pending.partition(b'\n')
            pending[:] = tail
            frames.append({'elapsed': round(time.monotonic() - start, 3),
                           'frame': line.decode('ascii', errors='replace')})
        assert len(pending) <= 128, 'Unframed serial output'
    return [entry['frame'] for entry in frames]


try:
    port.reset_input_buffer()
    idle = phase('idle', 2.0, b'W,0,0\n')
    assert idle.count('S,1,0,0') >= 2, f'No stable idle telemetry: {idle}'
    active = phase('all_headers_no_tach', 10.0, b'W,300,300\n')
    assert 'S,1,1,0' in active, 'No precharge report'
    for mask in ('1', '3', '7', 'F'):
        assert f'S,1,2,{mask}' in active, f'No active warning {mask}: {active}'
    assert active[-1] == 'S,1,2,F', 'Did not remain active with all tach absent'
    stale = phase('command_timeout', 1.5, None)
    assert stale[-1] == 'S,1,3,0', f'No command timeout: {stale}'
    stopped = phase('explicit_stop', 1.0, b'W,0,0\n')
    assert stopped[-1] == 'S,1,0,0', f'No stopped state: {stopped}'
    report['status'] = 'PASS'
finally:
    try:
        for _ in range(5):
            port.write(b'W,0,0\n')
            time.sleep(0.1)
    finally:
        port.close()
        path = Path(__file__).resolve().parents[1] / 'reports/warning-usb-smoke.json'
        path.write_text(json.dumps(report, indent=2) + '\n')
        print(f"{report['status']}: {path}")
