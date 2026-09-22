"""Stop a running controller and require fresh idle reports before resetting it."""
import argparse
import time

import serial
from serial.tools import list_ports


def prepare(port_name):
    ports = {p.device: p for p in list_ports.comports()}
    device = ports.get(port_name)
    if device is None or (device.vid, device.pid) != (0x303A, 0x1001):
        raise RuntimeError(f'{port_name} is not the ESP32 native USB device')
    with serial.Serial(port=None, baudrate=115200, timeout=0.05,
                       write_timeout=0.5) as port:
        port.dtr = False
        port.rts = False
        port.port = port_name
        port.open()
        # Drain queued snapshots before counting responses to the stop command.
        port.reset_input_buffer()
        start = time.monotonic()
        next_stop = start
        pending = bytearray()
        idle_since = None
        last_idle = None
        idle_reports = 0
        while time.monotonic() - start < 5.0:
            now = time.monotonic()
            if now >= next_stop:
                if port.write(b'W,0,0\n') != 6:
                    raise RuntimeError('Incomplete stop command write')
                next_stop = now + 0.1
            pending.extend(port.read(128))
            while b'\n' in pending:
                line, _, tail = pending.partition(b'\n')
                pending = bytearray(tail)
                if line == b'S,1,0,0':
                    if idle_since is None:
                        idle_since = time.monotonic()
                    last_idle = time.monotonic()
                    idle_reports += 1
                else:
                    idle_since = last_idle = None
                    idle_reports = 0
            if len(pending) > 128:
                raise RuntimeError('Unexpected serial stream')
            now = time.monotonic()
            if (idle_since is not None and now - idle_since >= 2.0
                    and idle_reports >= 4 and now - last_idle < 0.75):
                print('Controller reports OFF continuously for 2 seconds; ready to flash.')
                return
        raise RuntimeError('No stable OFF confirmation. Disconnect 12 V and use BOOT/RESET recovery.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True)
    prepare(parser.parse_args().port)
