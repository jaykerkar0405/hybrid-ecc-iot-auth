#ifndef PRIM_BENCH_H
#define PRIM_BENCH_H
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
/* Platform hooks */
uint32_t bench_tick(void);                 /* free-running counter */
uint64_t bench_tick_to_ns(uint32_t delta); /* counter delta -> nanoseconds */
void bench_emit(const char *line);         /* one CSV line */
void bench_yield(void);                    /* feed watchdog on MCUs */
void bench_big_stack(void (*fn)(void));    /* run fn on a larger stack if the platform needs one */
/* Runs every primitive; `platform` is a label put in each CSV row. */
void bench_run_all(const char *platform, int runs);
#ifdef __cplusplus
}
#endif
#endif
