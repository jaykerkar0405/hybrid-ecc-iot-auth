#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "prim_bench.h"
uint32_t bench_tick(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return (uint32_t)((uint64_t)t.tv_sec * 1000000000ull + t.tv_nsec); }
uint64_t bench_tick_to_ns(uint32_t d) { return d; }
void bench_emit(const char *l) { puts(l); }
void bench_yield(void) {}
void bench_big_stack(void (*fn)(void)) { fn(); }
int main(int argc, char **argv) { bench_run_all(argc > 1 ? argv[1] : "host", argc > 2 ? atoi(argv[2]) : 100); return 0; }
