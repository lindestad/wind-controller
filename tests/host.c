#include "control.h"
#include <assert.h>
#include <stdio.h>

static struct wind_control s;
static struct wind_tach tach[WIND_FANS];
void host_init(uint32_t now) { wind_init(&s, now); for (unsigned i=0;i<4;i++) tach[i]=(struct wind_tach){0}; }
void host_byte(unsigned byte, uint32_t now) { wind_byte(&s, (unsigned char)byte, now); }
void host_tick(uint32_t now) { wind_tick(&s, now, tach); }
void host_edge(unsigned i, uint32_t now) { assert(i<4); tach[i].count++; tach[i].last_ms=now; }
unsigned host_demand(unsigned i) { assert(i<4); return s.output.demand[i]; }
unsigned host_target(unsigned i) { assert(i<4); return s.target[i]; }
unsigned host_enable(void) { return s.output.enable; }
unsigned host_accepted(void) { return s.accepted; }
unsigned host_mode(void) { return s.mode; }
unsigned host_warnings(void) { return s.no_tach_mask; }
void host_status(unsigned char *out) { wind_status(&s, out); }
unsigned host_rpm(unsigned count, unsigned elapsed) { return wind_rpm(count, elapsed); }
unsigned host_telemetry(unsigned char *out, unsigned capacity) {
    uint32_t rpm[4] = {0, 1200, 1500, 3000};
    return wind_telemetry(&s, rpm, 123456, out, capacity);
}
int host_starting(void) { return s.starting; }
void host_fault(unsigned hard) { wind_fault(&s, hard != 0); }

struct event { int channel; uint32_t value; };
struct recorder { struct event e[16]; unsigned n; int fail_channel; };
static int record_pwm(void *ctx, unsigned channel, uint32_t value)
{
    struct recorder *r=ctx;
    r->e[r->n++]=(struct event){(int)channel,value};
    return r->fail_channel==(int)channel ? -1 : 0;
}
static int record_enable(void *ctx, bool on)
{
    struct recorder *r=ctx;
    r->e[r->n++]=(struct event){-1,on};
    return 0;
}
int host_output_tests(void)
{
    struct recorder r={.fail_channel=-2};
    struct wind_io io={&r,record_pwm,record_enable};
    struct wind_output out={.enable=false,.demand={1000,1000,1000,1000}};
    assert(!wind_apply(&out,&io));
    assert(r.n==5);
    for(unsigned i=0;i<4;i++) assert(r.e[i].channel==(int)i && r.e[i].value==40000);
    assert(r.e[4].channel==-1 && r.e[4].value==0);
    r.n=0; out.enable=true; out.demand[0]=0; out.demand[1]=250; out.demand[2]=750;
    assert(!wind_apply(&out,&io));
    assert(r.e[0].value==40000 && r.e[1].value==30000 && r.e[2].value==10000 && r.e[3].value==0);
    assert(r.e[4].channel==-1 && r.e[4].value==1);
    for(int bad=0;bad<4;bad++) {
        r.n=0; r.fail_channel=bad;
        assert(wind_apply(&out,&io)==-1);
        assert(r.e[bad+1].channel==-1 && r.e[bad+1].value==0);
        for(unsigned i=0;i<r.n;i++) if(r.e[i].channel==-1) assert(r.e[i].value==0);
    }
    assert(wind_gate_ns(1001)==40000);
    return 0;
}
