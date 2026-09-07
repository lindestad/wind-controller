"""Execute the actual C control/output code on the host; no Zephyr mocks of its logic."""
import ctypes as C
import json
from pathlib import Path
import random
import re
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'tests/.build'
BUILD.mkdir(exist_ok=True)
gcc = shutil.which('gcc')
if not gcc:
    raise RuntimeError('A host GCC is required for these executable C tests')
subprocess.run([gcc, '-std=c11', '-Wall', '-Wextra', '-Werror', '-Wconversion', '-O2',
                '-shared', '-I'+str(ROOT/'include'), str(ROOT/'src/control.c'),
                str(ROOT/'src/output.c'), str(ROOT/'tests/host.c'),
                '-o', str(BUILD/'control.dll')], check=True)
lib = C.CDLL(str(BUILD/'control.dll'))
for name, argc in [('host_init',1),('host_byte',2),('host_tick',1),('host_edge',2),
                   ('host_demand',1),('host_target',1),('host_fault',1)]:
    getattr(lib,name).argtypes = [C.c_uint32]*argc
lib.host_starting.restype = C.c_int

def frame(left=600, right=700, now=0):
    raw = f'W,{left},{right}\n'.encode()
    for byte in raw: lib.host_byte(byte,now)

def feed(raw, now=0):
    for byte in raw: lib.host_byte(byte,now)

def outputs(): return [lib.host_demand(i) for i in range(4)]

def run_until(end, start=0, left=600, right=700, tach=True, origin=0):
    for elapsed in range(start,end+1,10):
        now=(origin+elapsed)&0xffffffff
        if elapsed%100==0: frame(left,right,now)
        if tach and elapsed%20==0:
            for i,demand in enumerate(outputs()):
                if demand: lib.host_edge(i,now)
        lib.host_tick(now)

class ControlTests(unittest.TestCase):
    def setUp(self): lib.host_init(0)

    def test_boot_and_console_noise_cannot_start(self):
        feed(b'ESP-ROM:esp32c3\nhello\nW,-1,0\nW,1001,0\n')
        self.assertFalse(lib.host_enable()); self.assertEqual(lib.host_accepted(),0)
        self.assertEqual(outputs(),[0]*4)

    def test_precharge_and_250ms_kick(self):
        run_until(740)
        self.assertTrue(lib.host_enable()); self.assertEqual(outputs(),[0]*4)
        run_until(750,750); self.assertEqual(outputs(),[1000,0,0,0])
        run_until(990,760); self.assertEqual(outputs(),[1000,0,0,0])
        run_until(1000,1000); self.assertEqual(outputs(),[600,0,0,0])

    def test_four_fans_start_at_least_500ms_apart(self):
        first=[None]*4
        for ms in range(0,2510,10):
            run_until(ms,ms)
            for i,d in enumerate(outputs()):
                if d and first[i] is None: first[i]=ms
        self.assertEqual(first,[750,1250,1750,2250])
        self.assertEqual(outputs(),[600,600,700,700])

    def test_no_tach_latches_fault_and_never_retries(self):
        run_until(2750,tach=False)
        self.assertEqual(lib.host_mode(),4); self.assertFalse(lib.host_enable())
        run_until(7000,2760,tach=False)
        self.assertEqual(lib.host_mode(),4); self.assertFalse(lib.host_enable())
        frame(0,0,7010); self.assertEqual(lib.host_mode(),0)
        frame(500,0,7020); lib.host_tick(7020)
        self.assertTrue(lib.host_enable()); self.assertEqual(outputs(),[0]*4)

    def test_two_edges_are_not_two_periods(self):
        run_until(750,tach=False)
        lib.host_edge(0,800); lib.host_edge(0,900)
        run_until(1250,760,tach=False)
        self.assertEqual(lib.host_starting(),0); self.assertEqual(outputs()[1],0)
        lib.host_edge(0,1260); lib.host_tick(1260)
        self.assertEqual(lib.host_starting(),1)

    def test_old_edges_do_not_qualify_new_start(self):
        for _ in range(20): lib.host_edge(0,0)
        run_until(1250,tach=False)
        self.assertEqual(lib.host_starting(),0)

    def test_timeout_during_precharge_and_kick(self):
        frame(500,500,0); lib.host_tick(499); self.assertTrue(lib.host_enable())
        lib.host_tick(500); self.assertFalse(lib.host_enable())
        lib.host_init(0); run_until(800)
        feed(b'bad\n',1000); lib.host_tick(1300)
        self.assertFalse(lib.host_enable()); self.assertEqual(outputs(),[0]*4)

    def test_zero_stops_and_new_request_recharges(self):
        run_until(1800)
        frame(0,0,1810); self.assertFalse(lib.host_enable()); self.assertEqual(outputs(),[0]*4)
        frame(500,500,1820); lib.host_tick(1820)
        self.assertEqual(lib.host_mode(),1); self.assertEqual(outputs(),[0]*4)

    def test_starting_side_cancel_and_later_rejoin(self):
        run_until(800)
        frame(0,700,810); lib.host_tick(810)
        self.assertEqual(outputs(),[0,0,1000,0]); self.assertEqual(lib.host_starting(),2)
        run_until(2400,820,left=0)
        frame(600,700,2410); lib.host_tick(2410)
        self.assertEqual(outputs()[0],1000); self.assertEqual(outputs()[1],0)

    def test_zero_side_never_kicked(self):
        run_until(2000,left=0,right=900)
        self.assertEqual(outputs(),[0,0,900,900])

    def test_below_fan_stop_threshold(self):
        frame(49,0,0); self.assertFalse(lib.host_enable())
        frame(50,0,10); self.assertTrue(lib.host_enable())

    def test_stall_after_successful_start(self):
        run_until(3000)
        run_until(5000,3010,tach=False)
        self.assertEqual(lib.host_mode(),4); self.assertEqual(outputs(),[0]*4)

    def test_time_wrap_during_staging(self):
        origin=0xffffff00
        lib.host_init(origin)
        run_until(3000,origin=origin)
        self.assertEqual(outputs(),[600,600,700,700])
        lib.host_tick((origin+3500)&0xffffffff)
        self.assertFalse(lib.host_enable())

    def test_partial_deadline_discards_through_delimiter(self):
        feed(b'W,500',0); feed(b',500\n',100)
        self.assertEqual(lib.host_accepted(),0)
        frame(300,0,101); self.assertEqual(lib.host_accepted(),1)

    def test_overlong_and_embedded_valid_suffix_rejected(self):
        feed(b'xxxxxxxxxxxxxxxxW,1000,1000\n',0)
        self.assertEqual(lib.host_accepted(),0)
        frame(now=1); self.assertEqual(lib.host_accepted(),1)

    def test_hard_fault_requires_reset(self):
        frame(); lib.host_fault(1)
        frame(0,0,1); frame(500,500,2)
        self.assertEqual(lib.host_mode(),4); self.assertFalse(lib.host_enable())

    def test_gate_polarity_and_hardware_write_order(self):
        self.assertEqual(lib.host_output_tests(),0)

    def test_parser_against_independent_regex_oracle(self):
        rng=random.Random(0xB3)
        oracle=re.compile(rb'W,([0-9]{1,4}),([0-9]{1,4})\Z')
        for n in range(20000):
            if n%3==0:
                raw=f'W,{rng.randrange(1200)},{rng.randrange(1200)}'.encode()
            else:
                raw=bytes(rng.choice(b'W,0123456789-+ \r\x00XYZ') for _ in range(rng.randrange(25)))
            m=oracle.fullmatch(raw)
            valid=bool(m and int(m[1])<=1000 and int(m[2])<=1000)
            lib.host_init(0); feed(raw+b'\n')
            self.assertEqual(lib.host_accepted(),int(valid),raw)
            if valid:
                self.assertEqual(lib.host_enable(),int(int(m[1])>=50 or int(m[2])>=50))

    def test_random_traffic_never_exceeds_output_bounds(self):
        rng=random.Random(1214)
        now=0
        for n in range(100000):
            now+=rng.randrange(4)
            if n%97==0: frame(rng.randrange(1001),rng.randrange(1001),now)
            else: lib.host_byte(rng.randrange(256),now)
            lib.host_tick(now)
            self.assertTrue(all(0<=x<=1000 for x in outputs()))
            if not lib.host_enable(): self.assertEqual(outputs(),[0]*4)

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ControlTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={'status':'PASS' if result.wasSuccessful() else 'FAIL', 'tests':result.testsRun,
            'failures':len(result.failures),'errors':len(result.errors),
            'parser_oracle_frames':20000,'random_events':100000,
            'scope':'Actual C host execution; no physical ESP32/fan timing or USB enumeration proved.'}
    (ROOT/'reports').mkdir(exist_ok=True)
    (ROOT/'reports/host-tests.json').write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit(not result.wasSuccessful())
