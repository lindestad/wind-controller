#include "control.h"
#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/pwm.h>
#include <zephyr/drivers/uart.h>
#include <zephyr/drivers/watchdog.h>
#include <string.h>

#define USER DT_PATH(zephyr_user)
static const struct gpio_dt_spec enable = GPIO_DT_SPEC_GET(USER, fan_enable_gpios);
static const struct gpio_dt_spec status = GPIO_DT_SPEC_GET(USER, status_gpios);
static const struct gpio_dt_spec tach_pin[] = {
    GPIO_DT_SPEC_GET_BY_IDX(USER, tach_gpios, 0), GPIO_DT_SPEC_GET_BY_IDX(USER, tach_gpios, 1),
    GPIO_DT_SPEC_GET_BY_IDX(USER, tach_gpios, 2), GPIO_DT_SPEC_GET_BY_IDX(USER, tach_gpios, 3),
};
static const struct pwm_dt_spec pwm[] = {
    PWM_DT_SPEC_GET_BY_IDX(USER, 0), PWM_DT_SPEC_GET_BY_IDX(USER, 1),
    PWM_DT_SPEC_GET_BY_IDX(USER, 2), PWM_DT_SPEC_GET_BY_IDX(USER, 3),
};
static const struct device *const usb = DEVICE_DT_GET(DT_NODELABEL(usb_serial));
static const struct device *const watchdog = DEVICE_DT_GET(DT_NODELABEL(wdt0));
static struct gpio_callback tach_cb;
static volatile struct wind_tach tach[WIND_FANS];
static unsigned char status_frame[WIND_TELEMETRY_BYTES];
static unsigned status_sent, status_size;

static void status_irq(const struct device *dev, void *context)
{
    ARG_UNUSED(context);
    if (!uart_irq_update(dev) || !uart_irq_tx_ready(dev)) return;
    if (status_sent < status_size) {
        int sent = uart_fifo_fill(dev, status_frame + status_sent,
                                 (int)(status_size - status_sent));
        if (sent > 0) status_sent += (unsigned)sent;
    }
    if (status_sent == status_size) uart_irq_tx_disable(dev);
}

static void publish_status(const unsigned char *frame, unsigned size)
{
    // Keep at most one pending snapshot. Never wait for a host to read USB:
    // blocking poll_out can delay command expiry when USB is backpressured.
    unsigned key = irq_lock();
    if (status_sent == status_size) {
        memcpy(status_frame, frame, size);
        status_size = size;
        status_sent = 0;
        uart_irq_tx_enable(usb);
    }
    irq_unlock(key);
}

static void tach_edge(const struct device *dev, struct gpio_callback *cb, uint32_t pins)
{
    ARG_UNUSED(dev); ARG_UNUSED(cb);
    uint32_t now = k_uptime_get_32();
    for (unsigned i = 0; i < WIND_FANS; ++i) {
        if ((pins & BIT(tach_pin[i].pin)) &&
            (!tach[i].count || now - tach[i].last_ms >= 1U)) {
            tach[i].last_ms = now;
            tach[i].count++;
        }
    }
}

static int set_pwm(void *context, unsigned channel, uint32_t ns)
{
    ARG_UNUSED(context);
    return pwm_set_pulse_dt(&pwm[channel], ns);
}
static int set_enable(void *context, bool enabled)
{
    ARG_UNUSED(context);
    return gpio_pin_set_dt(&enable, enabled);
}
static const struct wind_io io = {.pwm = set_pwm, .enable = set_enable};

int main(void)
{
    struct wind_control state;
    wind_init(&state, k_uptime_get_32());
    if (!gpio_is_ready_dt(&enable) || gpio_pin_configure_dt(&enable, GPIO_OUTPUT_INACTIVE)) return 1;
    if (!device_is_ready(usb) || !device_is_ready(watchdog)) return 2;
    for (unsigned i = 0; i < WIND_FANS; ++i) if (!pwm_is_ready_dt(&pwm[i])) return 3;
    if (wind_apply(&state.output, &io)) return 4;
    if (uart_irq_callback_user_data_set(usb, status_irq, NULL)) return 12;
    if (!gpio_is_ready_dt(&status) || gpio_pin_configure_dt(&status, GPIO_OUTPUT_INACTIVE)) return 5;
    uint32_t mask = 0;
    for (unsigned i = 0; i < WIND_FANS; ++i) {
        if (!gpio_is_ready_dt(&tach_pin[i]) || gpio_pin_configure_dt(&tach_pin[i], GPIO_INPUT)) return 6;
        mask |= BIT(tach_pin[i].pin);
    }
    gpio_init_callback(&tach_cb, tach_edge, mask);
    if (gpio_add_callback(tach_pin[0].port, &tach_cb)) return 7;
    for (unsigned i = 0; i < WIND_FANS; ++i)
        if (gpio_pin_interrupt_configure_dt(&tach_pin[i], GPIO_INT_EDGE_FALLING)) return 8;
    // ESP32 driver has an interrupt stage followed by a system-reset stage.
    // 500 ms per stage: do not claim a 500 ms total watchdog reset latency.
    struct wdt_timeout_cfg timeout = {
        .window = {.min = 0, .max = 500}, .flags = WDT_FLAG_RESET_SOC,
    };
    int channel = wdt_install_timeout(watchdog, &timeout);
    if (channel < 0 || wdt_setup(watchdog, 0)) return 9;
    unsigned char byte;
    unsigned discarded = 0;
    while (discarded < 256U && !uart_poll_in(usb, &byte)) discarded++;
    if (discarded == 256U) wind_fault(&state, true);
    uint32_t last_status = k_uptime_get_32() - WIND_STATUS_MS;
    uint32_t last_rpm = k_uptime_get_32();
    uint32_t prior_count[WIND_FANS] = {0}, rpm[WIND_FANS] = {0};
    for (;;) {
        struct wind_tach snapshot[WIND_FANS];
        unsigned key = irq_lock();
        for (unsigned i = 0; i < WIND_FANS; ++i) snapshot[i] = tach[i];
        irq_unlock(key);
        uint32_t now = k_uptime_get_32();
        wind_tick(&state, now, snapshot);
        unsigned received = 0;
        while (received < 64U && !uart_poll_in(usb, &byte)) {
            wind_byte(&state, byte, k_uptime_get_32());
            received++;
        }
        if (received == 64U) wind_fault(&state, true);
        wind_tick(&state, k_uptime_get_32(), snapshot);
        if (wind_apply(&state.output, &io)) {
            (void)gpio_pin_set_dt(&enable, false);
            return 10; // no watchdog feed after an actuator failure
        }
        (void)gpio_pin_set_dt(&status, state.output.enable);
        now = k_uptime_get_32();
        if (now - last_status >= WIND_STATUS_MS) {
            unsigned char frame[WIND_TELEMETRY_BYTES];
            wind_status(&state, frame);
            unsigned size = WIND_STATUS_BYTES;
            if (now - last_rpm >= 1000U) {
                for (unsigned i = 0; i < WIND_FANS; ++i) {
                    rpm[i] = wind_rpm(snapshot[i].count - prior_count[i], now - last_rpm);
                    prior_count[i] = snapshot[i].count;
                }
                last_rpm = now;
                size += wind_telemetry(&state, rpm, now, frame + size,
                                       (unsigned)sizeof(frame) - size);
            }
            publish_status(frame, size);
            last_status = now;
        }
        if (wdt_feed(watchdog, channel)) {
            struct wind_output stopped = {0};
            (void)wind_apply(&stopped, &io);
            return 11;
        }
        k_msleep(5);
    }
}
