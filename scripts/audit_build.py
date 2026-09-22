"""Audit generated configuration, DTS, linked image and the B.3 hardware pin map."""
import argparse
import hashlib
import json
from pathlib import Path
import pickle
import re
import subprocess
import sys

p=argparse.ArgumentParser()
p.add_argument('--workspace',type=Path,required=True)
p.add_argument('--hardware',type=Path,default=Path.home()/'KiCad/windpcb-revb')
a=p.parse_args()
root=Path(__file__).resolve().parents[1]; z=a.workspace/'zephyr'; b=root/'build/zephyr'
sys.path.insert(0,str(z/'scripts/dts/python-devicetree/src'))
edt=pickle.loads((b/'edt.pickle').read_bytes())
config=dict(re.findall(r'^(CONFIG_\w+)=(.*)$',(b/'.config').read_text(),re.M))
checks=[]
def check(name,ok):
    assert ok,name
    checks.append(name)
for option in ['SOC_ESP32C3_WROOM_02_N4','GPIO','PWM','WATCHDOG','SERIAL_ESP32_USB','UART_INTERRUPT_DRIVEN']:
    check(option,config.get('CONFIG_'+option)=='y')
for option in ['CONSOLE','UART_CONSOLE','PRINTK','LOG','BOOT_BANNER','WIFI','BT','NETWORKING','PM','PM_DEVICE']:
    check(option+' disabled',config.get('CONFIG_'+option,'n')=='n')
for label in ['uart0','uart1','wifi','esp32_bt_hci']:
    check(label+' disabled',edt.label2node[label].status=='disabled')
for label in ['usb_serial','wdt0','ledc0']:
    check(label+' enabled',edt.label2node[label].status=='okay')
check('4 MiB flash',edt.label2node['flash0'].regs[0].size==4194304)
u=edt.get_node('/zephyr,user')
for prop,pins in [('fan-enable-gpios',[10]),('status-gpios',[21]),('tach-gpios',[0,1,3,20])]:
    values=u.props[prop].val
    check(prop,[v.data['pin'] for v in values]==pins and all(v.data['flags']==0 for v in values))
    check(prop+' gpio0',all(v.controller is edt.label2node['gpio0'] for v in values))
pwms=u.props['pwms'].val
check('four 25kHz normal-polarity channels',len(pwms)==4 and all(v.data=={'channel':i,'period':40000,'flags':0} for i,v in enumerate(pwms)))
mux=edt.label2node['wind_pwm'].children['group1'].props['pinmux'].val
check('PWM pins 4/5/6/7',[v&63 for v in mux]==[4,5,6,7])
sig_header=(z/'include/zephyr/dt-bindings/pinctrl/esp32c3-gpio-sigmap.h').read_text()
signals=[int(re.search(r'#define\s+ESP_LEDC_LS_SIG_OUT'+str(i)+r'\s+(\d+)',sig_header)[1]) for i in range(4)]
check('PWM matrix CH0/1/2/3',[(v>>15)&511 for v in mux]==signals)
for i,child in enumerate(edt.label2node['ledc0'].children.values()):
    check('PWM channel '+str(i)+' idle high / shared timer',child.props['inverted'].val and child.props['timer'].val==0)
check('no default UART console',edt.chosen_node('zephyr,console') is None)
expected={'3':'PWM_L1_DRV','4':'PWM_L2_DRV','5':'PWM_R1_DRV','6':'PWM_R2_DRV',
          '10':'FAN_ENABLE','11':'TACH_R2','12':'STATUS_DRV','13':'USB_DN',
          '14':'USB_DP','15':'TACH_R1','17':'TACH_L2','18':'TACH_L1'}
hardware_data=a.hardware/'tools/design-data.json'
if hardware_data.exists():
    data=json.loads(hardware_data.read_text())
    nets=next(x['nets'] for x in data if x['ref']=='U1')
    check('B.3 module pad net map',all(nets[k]==v for k,v in expected.items()))
else:
    raise RuntimeError('Provide --hardware pointing to the current WindPCB source for the cross-check')
check('ELF exists',(b/'zephyr.elf').stat().st_size>0)
check('flash image exists',(b/'zephyr.bin').stat().st_size>0)
check('no radios linked',not any(t in (b/'zephyr.map').read_text(errors='replace') for t in ['libnet80211.a(','libbt.a(']))
revision=subprocess.check_output(['git','-C',str(z),'rev-parse','HEAD'],text=True).strip()
check('pinned Zephyr 4.4.2',revision=='dccb09599635bdff17633fa7e9dab014b91dce90')
files=[b/'zephyr.elf',b/'zephyr.bin',b/'.config',b/'zephyr.dts']
report={'status':'PASS','checks':checks,'zephyr_commit':revision,'sdk':'1.0.1',
        'board':'wind_controller/esp32c3','application_bytes':(b/'zephyr.bin').stat().st_size,
        'hardware_data_sha256':hashlib.sha256(hardware_data.read_bytes()).hexdigest(),
        'artifacts':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},
        'limitations':['No flashing or physical USB enumeration','No real fan tach, PWM, startup or temperature measurement','No runtime deadline/watchdog reset measurement']}
(root/'reports/build-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS:',len(checks),'generated configuration, pin-map and binary checks;',report['application_bytes'],'application bytes')
