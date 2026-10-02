// ESP8266 primitive benchmark: no Wi-Fi, cycle-accurate timing. Prints CSV over serial.
// Send any character to run again.
#include <Arduino.h>
#include <ESP8266WiFi.h>
extern "C" {
#include "prim_bench.h"
}
#ifndef BENCH_RUNS
#define BENCH_RUNS 100
#endif
extern "C" uint32_t bench_tick(void) { return ESP.getCycleCount(); }
extern "C" uint64_t bench_tick_to_ns(uint32_t d) { return (uint64_t)d * 1000ull / (F_CPU / 1000000UL); }
extern "C" void bench_emit(const char *l) { Serial.println(l); }
static bool on_big_stack = false;
// yield() validates the stack pointer against the 4 KB cont stack, so only feed the WDT on the big stack.
extern "C" void bench_yield(void) { if (!on_big_stack) yield(); ESP.wdtFeed(); }

// P-256 (ec_p256_m15) builds a ~4 KB window table on the stack; the ESP8266 task stack is only 4 KB.
// Run those on a temporary heap stack by swapping a1 (sp). Not for production use.
static uint32_t saved_sp;
extern "C" void bench_big_stack(void (*fn)(void)) {
  const size_t N = 12 * 1024;
  uint8_t *mem = (uint8_t *)malloc(N);
  if (!mem) { Serial.println("# no memory for big stack"); return; }
  uint32_t top = ((uint32_t)(mem + N)) & ~0xFu;
  on_big_stack = true;
  asm volatile("mov %0, a1\n\tmov a1, %1" : "=&r"(saved_sp) : "r"(top) : "memory");
  fn();
  // Returning to the original stack reset the chip in testing (cause not found), so after the
  // benchmark has printed BENCH_DONE we stay here and just keep the watchdog fed. Press reset to rerun.
  for (;;) ESP.wdtFeed();
}

static void go() {
  char plat[40];
  snprintf(plat, sizeof plat, "esp8266@%luMHz", (unsigned long)(F_CPU / 1000000UL));
  Serial.printf("# chip %08x, %s, free heap %u\n", ESP.getChipId(), plat, ESP.getFreeHeap());
  bench_run_all(plat, BENCH_RUNS);
}
void setup() { Serial.begin(115200); delay(500); WiFi.mode(WIFI_OFF); go(); }
void loop() { if (Serial.available()) { Serial.read(); go(); } }
