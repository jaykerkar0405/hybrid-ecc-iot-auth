/* Copy of the shape that tools/gen_config.py writes to include/config.h
 * (gitignored: it holds Wi-Fi credentials and the device's long-term secret). */
#pragma once
#define WIFI_SSID "your-ssid"
#define WIFI_PASS "your-pass"
#define SERVER_HOST "192.168.1.10"
#define SERVER_PORT 8443
#define SERVER_ID "server-A"
#define EPOCH_GENERATION 0x12345678u /* changes on re-enrollment -> epoch resets to 0 */
static const uint8_t LAM_DEVICE[32] = {0};
static const uint8_t LAM_SERVER[32] = {0};
