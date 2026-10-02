// ESP8266 (NodeMCU) device for the hybrid ECC + symmetric-key mutual
// authentication protocol. Protocol core: lib/hea_proto (portable C + BearSSL).
//
// On boot: join Wi-Fi, run HEA_BENCH_N handshakes against the Python hea-server,
// print per-step timings, then try to replay the last M1 (must be rejected).
// Serial commands afterwards: 'a' = run another batch, 'z' = reset epoch to 0.
#include <Arduino.h>
#include <EEPROM.h>
#include <ESP8266WiFi.h>

extern "C" {
#include "hea_proto.h"
#if defined(__has_include) && __has_include(<bearssl/bearssl.h>)
#include <bearssl/bearssl.h>
#else
#include "bearssl.h"
#endif
}
#include "config.h"

#ifndef HEA_BENCH_N
#define HEA_BENCH_N 20
#endif

// ESP8266 hardware RNG register (best entropy while the Wi-Fi radio is on).
extern "C" void hea_random(uint8_t *out, size_t len) {
  for (size_t i = 0; i < len; i += 4) {
    uint32_t r = RANDOM_REG32;
    memcpy(out + i, &r, (len - i) < 4 ? (len - i) : 4);
  }
}

// ---- epoch persistence (fixes the reference implementation's in-RAM epoch) ----
struct EpochRecord { uint32_t magic, generation; uint64_t epoch; };
static const uint32_t MAGIC = 0x48454131;  // "HEA1"

static uint64_t epoch_load() {
  EpochRecord r; EEPROM.get(0, r);
  return (r.magic == MAGIC && r.generation == EPOCH_GENERATION) ? r.epoch : 0;
}
static void epoch_store(uint64_t e) {
  EpochRecord r = {MAGIC, EPOCH_GENERATION, e};
  EEPROM.put(0, r);
  EEPROM.commit();
}

static hea_device dev;
static uint8_t last_m1[512];
static size_t last_m1_len = 0;

static void fingerprint(const uint8_t *key, char *out) {
  uint8_t d[32]; br_sha256_context c;
  br_sha256_init(&c); br_sha256_update(&c, key, 32); br_sha256_out(&c, d);
  for (int i = 0; i < 8; i++) sprintf(out + 2 * i, "%02x", d[i]);
}

static IPAddress server_ip() { IPAddress a; a.fromString(SERVER_HOST); return a; }

static bool exchange(const uint8_t *m1, size_t m1_len, uint8_t *resp, size_t cap, size_t *resp_len,
                     uint32_t *connect_us) {
  WiFiClient c;
  c.setNoDelay(true);
  c.setTimeout(1500);  // connect() waits for this long; must stay under the 3.2 s soft WDT
  uint32_t t0 = micros();
  bool up = false;
  for (int attempt = 0; attempt < 3 && !up; attempt++) {  // short bounded connect, stays under the soft WDT
    up = c.connect(server_ip(), SERVER_PORT);
  }
  if (!up) return false;
  c.setTimeout(2500);  // read timeout
  *connect_us = micros() - t0;
  uint8_t hdr[4] = {(uint8_t)(m1_len >> 24), (uint8_t)(m1_len >> 16), (uint8_t)(m1_len >> 8), (uint8_t)m1_len};
  c.write(hdr, 4);
  c.write(m1, m1_len);
  if (c.readBytes(hdr, 4) != 4) return false;
  size_t n = ((size_t)hdr[0] << 24) | ((size_t)hdr[1] << 16) | ((size_t)hdr[2] << 8) | hdr[3];
  if (n > cap || c.readBytes(resp, n) != n) return false;
  *resp_len = n;
  return true;
}

struct Stat { uint32_t sum = 0, mn = UINT32_MAX, mx = 0; void add(uint32_t v) { sum += v; if (v < mn) mn = v; if (v > mx) mx = v; } };
static void print_stat(const char *name, const Stat &s, int n) {
  Serial.printf("  %-14s mean %7.2f ms   min %7.2f   max %7.2f\n", name, s.sum / (float)n / 1000.0f,
                s.mn / 1000.0f, s.mx / 1000.0f);
}

static void run_batch(int n) {
  Stat build, conn, rtt, complete, total;
  int ok = 0;
  static uint8_t resp[1024];  // static: keep the 4 KB cont stack free for crypto
  uint8_t key[32];
  char err[120], fp[20];
  uint32_t heap_before = ESP.getFreeHeap();
  for (int i = 0; i < n; i++) {
    hea_pending p;
    uint32_t t0 = micros();
    last_m1_len = hea_build_m1(&dev, &p, last_m1, sizeof last_m1);
    uint32_t t_build = micros() - t0;
    epoch_store(dev.epoch);

    size_t rl = 0; uint32_t t_conn = 0;
    uint32_t t1 = micros();
    if (!exchange(last_m1, last_m1_len, resp, sizeof resp, &rl, &t_conn)) {
      Serial.printf("HS %d transport_error\n", i); continue;
    }
    uint32_t t_rtt = micros() - t1;

    uint32_t t2 = micros();
    int rc = hea_complete(&dev, &p, resp, rl, key, err, sizeof err);
    uint32_t t_comp = micros() - t2;
    if (rc) { Serial.printf("HS %d FAIL rc=%d %s\n", i, rc, err); continue; }
    fingerprint(key, fp);
    uint32_t t_tot = micros() - t0;
    Serial.printf("HS %d ok epoch=%u build_us=%u connect_us=%u rtt_us=%u complete_us=%u total_us=%u fp=%s\n", i,
                  (unsigned)p.epoch, t_build, t_conn, t_rtt, t_comp, t_tot, fp);
    build.add(t_build); conn.add(t_conn); rtt.add(t_rtt); complete.add(t_comp); total.add(t_tot);
    ok++;
  }
  if (ok) {
    Serial.printf("\nSUMMARY %d/%d handshakes ok (M1 = %u bytes)\n", ok, n, (unsigned)last_m1_len);
    print_stat("build M1", build, ok);
    print_stat("verify M2+KDF", complete, ok);
    print_stat("TCP connect", conn, ok);
    print_stat("send+wait+recv", rtt, ok);
    print_stat("total", total, ok);
    Serial.printf("  device compute (build+verify) mean %.2f ms\n", (build.sum + complete.sum) / (float)ok / 1000.0f);
  }
  Serial.printf("  free heap %u -> %u B, min stack headroom %u B\n", heap_before, ESP.getFreeHeap(),
                (unsigned)ESP.getFreeContStack());

  if (last_m1_len) {  // replay: server must refuse
    size_t rl = 0; uint32_t t_conn = 0; hea_pending dummy = {};
    if (exchange(last_m1, last_m1_len, resp, sizeof resp, &rl, &t_conn)) {
      int rc = hea_complete(&dev, &dummy, resp, rl, key, err, sizeof err);
      Serial.printf("REPLAY rc=%d %s  -> %s\n", rc, err, rc == HEA_E_REJECTED ? "rejected (expected)" : "UNEXPECTED");
    }
  }
}

static void banner() {
  Serial.printf("\n\n== hybrid-ecc-auth ESP8266 device ==\n");
  Serial.printf("chip %08x, cpu %u MHz, flash %u KB, sdk %s\n", ESP.getChipId(), ESP.getCpuFreqMHz(),
                ESP.getFlashChipRealSize() / 1024, ESP.getSdkVersion());
  Serial.printf("free heap %u B, sketch %u B\n", ESP.getFreeHeap(), ESP.getSketchSize());
}

void setup() {
  Serial.begin(115200);
  delay(300);
  banner();
  EEPROM.begin(16);

  uint32_t t0 = micros();
  uint64_t epoch = epoch_load();
  hea_init(&dev, LAM_DEVICE, LAM_SERVER, SERVER_ID, epoch);
  Serial.printf("pairwise root k* derived in %u us (HKDF-SHA256); resuming at epoch %u\n", micros() - t0,
                (unsigned)epoch);

  WiFi.persistent(false);               // don't wear flash with Wi-Fi settings
  WiFi.mode(WIFI_STA);
  WiFi.setSleepMode(WIFI_NONE_SLEEP);   // modem sleep makes RTT/connect erratic (esp. on phone hotspots)
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("wifi");
  uint32_t w0 = millis();
  while (WiFi.status() != WL_CONNECTED) {
    delay(250); Serial.print('.');
    if (millis() - w0 > 15000) {  // diagnose instead of spinning forever
      // 1=no SSID found, 4=connect failed (wrong password), 6=wrong password/disconnected
      Serial.printf("\nwifi status %d after 15 s; networks visible to the board:\n", WiFi.status());
      int n = WiFi.scanNetworks();
      for (int i = 0; i < n; i++)
        Serial.printf("  %-32s ch%-2d %d dBm %s\n", WiFi.SSID(i).c_str(), WiFi.channel(i), WiFi.RSSI(i),
                      WiFi.encryptionType(i) == ENC_TYPE_NONE ? "open" : "secured");
      WiFi.begin(WIFI_SSID, WIFI_PASS); w0 = millis(); Serial.print("retry");
    }
  }
  Serial.printf(" up, ip %s, rssi %d dBm, server %s:%d\n", WiFi.localIP().toString().c_str(), WiFi.RSSI(), SERVER_HOST,
                SERVER_PORT);
  run_batch(HEA_BENCH_N);
  Serial.println("\ncommands: 'a' another batch, 'z' reset epoch to 0");
}

void loop() {
  if (!Serial.available()) return;
  int ch = Serial.read();
  if (ch == 'a') run_batch(HEA_BENCH_N);
  else if (ch == 'z') { dev.epoch = 0; epoch_store(0); Serial.println("epoch reset to 0"); }
}
