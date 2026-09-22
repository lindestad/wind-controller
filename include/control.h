#ifndef WIND_CONTROL_H
#define WIND_CONTROL_H
#include <stdbool.h>
#include <stdint.h>

#define WIND_FANS 4U
#define WIND_PERIOD_NS 40000U
#define WIND_TIMEOUT_MS 500U
#define WIND_FRAME_MS 100U
#define WIND_PRECHARGE_MS 750U
#define WIND_KICK_MS 250U
#define WIND_START_GAP_MS 500U
#define WIND_START_TIMEOUT_MS 2000U
#define WIND_STALL_MS 2000U
#define WIND_MIN_DEMAND 50U
#define WIND_FRAME_MAX 11U
#define WIND_STATUS_BYTES 8U
#define WIND_STATUS_MS 500U

enum wind_mode { WIND_OFF, WIND_PRECHARGE, WIND_ACTIVE, WIND_STALE, WIND_FAULT };
struct wind_tach { uint32_t count, last_ms; };
struct wind_output { bool enable; uint16_t demand[WIND_FANS]; };
struct wind_control {
    enum wind_mode mode;
    struct wind_output output;
    uint16_t target[WIND_FANS];
    bool ready[WIND_FANS], discard, hard_fault;
    uint8_t no_tach_mask;
    uint32_t tach_baseline[WIND_FANS];
    int starting;
    uint32_t last_valid, power_started, fan_started, start_count;
    uint32_t partial_started, accepted, rejected;
    unsigned used;
    unsigned char frame[WIND_FRAME_MAX];
};
void wind_init(struct wind_control *s, uint32_t now);
void wind_tick(struct wind_control *s, uint32_t now, const struct wind_tach tach[WIND_FANS]);
void wind_byte(struct wind_control *s, unsigned char byte, uint32_t now);
void wind_fault(struct wind_control *s, bool hard);
uint32_t wind_gate_ns(uint16_t demand);
void wind_status(const struct wind_control *s, unsigned char out[WIND_STATUS_BYTES]);

struct wind_io {
    void *context;
    int (*pwm)(void *context, unsigned channel, uint32_t gate_ns);
    int (*enable)(void *context, bool enabled);
};
int wind_apply(const struct wind_output *out, const struct wind_io *io);
#endif
