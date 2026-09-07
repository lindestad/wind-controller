#include "control.h"

int wind_apply(const struct wind_output *out, const struct wind_io *io)
{
    int error = 0;
    // PWM stop must reach all fan inputs before power is disabled. On any
    // write failure disable the eFuse immediately, then try remaining stops.
    for (unsigned i = 0; i < WIND_FANS; ++i) {
        uint16_t demand = out->enable ? out->demand[i] : 0U;
        int rc = io->pwm(io->context, i, wind_gate_ns(demand));
        if (rc && !error) { error = rc; (void)io->enable(io->context, false); }
    }
    int rc = io->enable(io->context, !error && out->enable);
    return error ? error : rc;
}
