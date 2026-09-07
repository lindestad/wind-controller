#include "control.h"
#include <string.h>

static uint32_t age(uint32_t now, uint32_t then) { return now - then; }

static void stop(struct wind_control *s, enum wind_mode mode)
{
    memset(&s->output, 0, sizeof(s->output));
    memset(s->target, 0, sizeof(s->target));
    memset(s->ready, 0, sizeof(s->ready));
    s->starting = -1;
    s->mode = mode;
}

static void expire(struct wind_control *s, uint32_t now)
{
    if (s->used && age(now, s->partial_started) >= WIND_FRAME_MS) {
        s->used = 0;
        s->discard = true;
        s->rejected++;
    }
    if (s->output.enable && age(now, s->last_valid) >= WIND_TIMEOUT_MS) {
        stop(s, WIND_STALE);
        if (s->used) { s->used = 0; s->discard = true; }
    }
}

void wind_init(struct wind_control *s, uint32_t now)
{
    memset(s, 0, sizeof(*s));
    s->last_valid = now;
    stop(s, WIND_OFF);
}

void wind_fault(struct wind_control *s, bool hard)
{
    stop(s, WIND_FAULT);
    s->hard_fault |= hard;
    if (s->used) s->discard = true;
    s->used = 0;
}

static bool number(const unsigned char *p, unsigned length, unsigned *at, uint16_t *out)
{
    unsigned value = 0, digits = 0;
    while (*at < length && p[*at] >= '0' && p[*at] <= '9') {
        if (++digits > 4) return false;
        value = value * 10U + p[(*at)++] - '0';
        if (value > 1000U) return false;
    }
    *out = (uint16_t)value;
    return digits != 0;
}

static void command(struct wind_control *s, uint16_t left, uint16_t right, uint32_t now)
{
    if (s->mode == WIND_FAULT) {
        // Only an exact zero command acknowledges a recoverable fault.
        if (s->hard_fault || left || right) { s->rejected++; return; }
        stop(s, WIND_OFF);
    }
    s->accepted++;
    s->last_valid = now;
    left = left < WIND_MIN_DEMAND ? 0 : left;
    right = right < WIND_MIN_DEMAND ? 0 : right;
    if (!left && !right) { stop(s, WIND_OFF); return; }
    if (!s->output.enable) {
        stop(s, WIND_PRECHARGE);
        s->power_started = now;
        s->output.enable = true;
    }
    for (unsigned i = 0; i < WIND_FANS; ++i) {
        s->target[i] = i < 2 ? left : right;
        if (!s->target[i]) {
            s->ready[i] = false;
            s->output.demand[i] = 0;
            if (s->starting == (int)i) s->starting = -1;
        }
    }
}

void wind_byte(struct wind_control *s, unsigned char byte, uint32_t now)
{
    expire(s, now);
    if (s->discard) { if (byte == '\n') s->discard = false; return; }
    if (byte != '\n') {
        if (s->used == WIND_FRAME_MAX) {
            s->rejected++;
            s->used = 0;
            s->discard = true;
        } else {
            if (!s->used) s->partial_started = now;
            s->frame[s->used++] = byte;
        }
        return;
    }
    uint16_t left = 0, right = 0;
    unsigned at = 2;
    bool valid = s->used >= 5 && s->frame[0] == 'W' && s->frame[1] == ',' &&
                 number(s->frame, s->used, &at, &left) && at < s->used &&
                 s->frame[at++] == ',' && number(s->frame, s->used, &at, &right) &&
                 at == s->used;
    s->used = 0;
    if (valid) command(s, left, right, now); else s->rejected++;
}

void wind_tick(struct wind_control *s, uint32_t now, const struct wind_tach tach[WIND_FANS])
{
    expire(s, now);
    if (!s->output.enable) return;
    if (s->mode == WIND_PRECHARGE) {
        if (age(now, s->power_started) < WIND_PRECHARGE_MS) return;
        s->mode = WIND_ACTIVE;
    }
    for (unsigned i = 0; i < WIND_FANS; ++i) {
        if (s->ready[i]) {
            if (age(now, tach[i].last_ms) >= WIND_STALL_MS) {
                wind_fault(s, false); return;
            }
            s->output.demand[i] = s->target[i];
        }
    }
    if (s->starting >= 0) {
        unsigned i = (unsigned)s->starting;
        uint32_t elapsed = age(now, s->fan_started);
        if (elapsed >= WIND_START_TIMEOUT_MS) { wind_fault(s, false); return; }
        s->output.demand[i] = elapsed < WIND_KICK_MS ? 1000U : s->target[i];
        // Three filtered edges establish two intervals. Old edges cannot
        // qualify startup because the baseline is sampled when the kick starts.
        if (elapsed < WIND_START_GAP_MS || tach[i].count - s->start_count < 3U ||
            age(now, tach[i].last_ms) >= WIND_START_GAP_MS) return;
        s->ready[i] = true;
        s->starting = -1;
    }
    for (unsigned i = 0; i < WIND_FANS; ++i) {
        if (s->target[i] && !s->ready[i]) {
            s->starting = (int)i;
            s->fan_started = now;
            s->start_count = tach[i].count;
            s->output.demand[i] = 1000U;
            return;
        }
    }
}

uint32_t wind_gate_ns(uint16_t demand)
{
    if (demand > 1000U) return WIND_PERIOD_NS; // invalid output fails stopped
    return (1000U - demand) * (WIND_PERIOD_NS / 1000U);
}
