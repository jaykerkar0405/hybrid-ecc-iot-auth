/* Primitive micro-benchmarks for the symbols in the paper's Table III
 * (T_H, T_SE/D, T_ECM) plus the primitives this implementation actually uses.
 * Same C source on every platform; only the timer/emit hooks differ.
 * CSV: BENCH,platform,op,variant,bytes,reps,runs,median_us,p25_us,p75_us,min_us,max_us */
#include "prim_bench.h"

#include <stdio.h>
#include <string.h>

#if defined(__has_include) && __has_include(<bearssl/bearssl.h>)
#include <bearssl/bearssl.h>
#else
#include "bearssl.h"
#endif

#ifdef ARDUINO /* BearSSL keeps curve constants in flash on the ESP8266; byte loads from flash fault */
#include <pgmspace.h>
#define GEN_COPY(dst, src, n) memcpy_P((dst), (src), (n))
#else
#define GEN_COPY(dst, src, n) memcpy((dst), (src), (n))
#endif

#define MAX_RUNS 128
static uint32_t samples[MAX_RUNS];

static void sort_u32(uint32_t *a, int n) {
    for (int i = 1; i < n; i++) { uint32_t v = a[i]; int j = i - 1; while (j >= 0 && a[j] > v) { a[j + 1] = a[j]; j--; } a[j + 1] = v; }
}

/* Time `reps` back-to-back executions per sample, report per-execution us. */
#define MEASURE(plat, op, variant, bytes, reps, runs, STMT)                                           \
    do {                                                                                              \
        int n_ = (runs) > MAX_RUNS ? MAX_RUNS : (runs);                                               \
        for (int r_ = 0; r_ < n_; r_++) {                                                             \
            uint32_t t0_ = bench_tick();                                                              \
            for (int k_ = 0; k_ < (reps); k_++) { STMT; }                                             \
            uint32_t d_ = bench_tick() - t0_;                                                         \
            samples[r_] = (uint32_t)(bench_tick_to_ns(d_) / (uint64_t)(reps));                        \
            bench_yield();                                                                            \
        }                                                                                             \
        report(plat, op, variant, bytes, reps, n_);                                                   \
    } while (0)

static void report(const char *plat, const char *op, const char *variant, int bytes, int reps, int n) {
    sort_u32(samples, n);
    char line[200];
    snprintf(line, sizeof line, "BENCH,%s,%s,%s,%d,%d,%d,%.3f,%.3f,%.3f,%.3f,%.3f", plat, op, variant, bytes, reps, n,
             samples[n / 2] / 1000.0, samples[n / 4] / 1000.0, samples[(3 * n) / 4] / 1000.0, samples[0] / 1000.0,
             samples[n - 1] / 1000.0);
    bench_emit(line);
}

static void emit_check(const char *plat, const char *label, const void *data, size_t len) {
    br_sha256_context c; uint8_t d[32]; char line[160], hex[17];
    br_sha256_init(&c); br_sha256_update(&c, data, len); br_sha256_out(&c, d);
    for (int i = 0; i < 8; i++) snprintf(hex + 2 * i, 3, "%02x", d[i]);
    snprintf(line, sizeof line, "BENCH_CHECK,%s,%s,%s", plat, label, hex);
    bench_emit(line);
}

static uint8_t key32[32], iv[12], msg[64], out[64], tag[16], hash[32];
static volatile uint8_t sink;

static void fill(void) {
    for (int i = 0; i < 32; i++) key32[i] = (uint8_t)(i * 7 + 1);
    for (int i = 0; i < 12; i++) iv[i] = (uint8_t)(i + 3);
    for (int i = 0; i < 64; i++) msg[i] = (uint8_t)(i * 13 + 5);
}

/* ---- AES-GCM variants -------------------------------------------------- */
typedef void (*gcm_fn)(int keylen, int len, int enc);

#define DEFINE_GCM(NAME, KEYS_T, INIT, GHASH)                                     \
    static void gcm_##NAME(int keylen, int len, int enc) {                        \
        KEYS_T bc; br_gcm_context gc;                                             \
        INIT(&bc, key32, keylen);                                                 \
        br_gcm_init(&gc, &bc.vtable, GHASH);                                      \
        br_gcm_reset(&gc, iv, 12);                                                \
        br_gcm_flip(&gc);                                                         \
        memcpy(out, msg, len);                                                    \
        br_gcm_run(&gc, enc, out, len);                                           \
        br_gcm_get_tag(&gc, tag);                                                 \
        sink = out[0] ^ tag[0];                                                   \
    }
DEFINE_GCM(ct, br_aes_ct_ctr_keys, br_aes_ct_ctr_init, br_ghash_ctmul32)
DEFINE_GCM(small, br_aes_small_ctr_keys, br_aes_small_ctr_init, br_ghash_ctmul32)
DEFINE_GCM(big, br_aes_big_ctr_keys, br_aes_big_ctr_init, br_ghash_ctmul32)

/* GCM with the key schedule prepared once (k* is fixed per pair, so a device can cache it) */
#define DEFINE_GCM_CACHED(NAME, KEYS_T, INIT, GHASH)                              \
    static KEYS_T cached_##NAME; static int cached_##NAME##_ok;                   \
    static void gcmc_##NAME(int len, int enc) {                                   \
        br_gcm_context gc;                                                        \
        if (!cached_##NAME##_ok) { INIT(&cached_##NAME, key32, 32); cached_##NAME##_ok = 1; } \
        br_gcm_init(&gc, &cached_##NAME.vtable, GHASH);                           \
        br_gcm_reset(&gc, iv, 12);                                                \
        br_gcm_flip(&gc);                                                         \
        memcpy(out, msg, len);                                                    \
        br_gcm_run(&gc, enc, out, len);                                           \
        br_gcm_get_tag(&gc, tag);                                                 \
        sink = out[0] ^ tag[0];                                                   \
    }
DEFINE_GCM_CACHED(ct, br_aes_ct_ctr_keys, br_aes_ct_ctr_init, br_ghash_ctmul32)
DEFINE_GCM_CACHED(small, br_aes_small_ctr_keys, br_aes_small_ctr_init, br_ghash_ctmul32)
DEFINE_GCM_CACHED(big, br_aes_big_ctr_keys, br_aes_big_ctr_init, br_ghash_ctmul32)

/* Bare AES variants: what a reader of "T_SE/D = symmetric encryption" might count */
static void bench_aes_bare(const char *plat, int runs) {
    static br_aes_ct_cbcenc_keys k1; static br_aes_small_cbcenc_keys k2; static br_aes_big_cbcenc_keys k3;
    static br_aes_ct_ctr_keys c1; static br_aes_small_ctr_keys c2; static br_aes_big_ctr_keys c3;
    uint8_t blk[16], ivz[16];
    br_aes_ct_cbcenc_init(&k1, key32, 32); br_aes_small_cbcenc_init(&k2, key32, 32); br_aes_big_cbcenc_init(&k3, key32, 32);
    br_aes_ct_ctr_init(&c1, key32, 32); br_aes_small_ctr_init(&c2, key32, 32); br_aes_big_ctr_init(&c3, key32, 32);
#define ONEBLK(V, K, RUN) MEASURE(plat, "AES-256 single block (key schedule cached)", V, 16, 16, runs, \
        memcpy(blk, msg, 16); memset(ivz, 0, 16); RUN(&K, ivz, blk, 16); sink = blk[0]); emit_check(plat, "aes_block_" V, blk, 16)
    ONEBLK("aes_ct", k1, br_aes_ct_cbcenc_run);
    ONEBLK("aes_small", k2, br_aes_small_cbcenc_run);
    ONEBLK("aes_big", k3, br_aes_big_cbcenc_run);
#define CTR56(V, K, RUN) MEASURE(plat, "AES-256-CTR 56 B (key schedule cached; no GHASH)", V, 56, 8, runs, \
        memcpy(out, msg, 56); RUN(&K, iv, 0, out, 56); sink = out[0]); emit_check(plat, "aes_ctr56_" V, out, 56)
    CTR56("aes_ct", c1, br_aes_ct_ctr_run);
    CTR56("aes_small", c2, br_aes_small_ctr_run);
    CTR56("aes_big", c3, br_aes_big_ctr_run);
#define GCMC(V, N) MEASURE(plat, "AES-256-GCM encrypt 56 B (key schedule cached)", V, 56, 4, runs, gcmc_##N(56, 1)); \
        emit_check(plat, "gcm_cached_ct_" V, out, 56); emit_check(plat, "gcm_cached_tag_" V, tag, 16)
    GCMC("aes_ct", ct); GCMC("aes_small", small); GCMC("aes_big", big);
}

static void bench_gcm(const char *plat, int runs) {
    struct { const char *name; gcm_fn f; } impl[] = {{"aes_ct(bitsliced,const-time)", gcm_ct},
                                                      {"aes_small(table,small)", gcm_small},
                                                      {"aes_big(table,fast)", gcm_big}};
    for (int i = 0; i < 3; i++) {
        int kl[2] = {32, 16};
        for (int k = 0; k < 2; k++) {
            char v[80];
            snprintf(v, sizeof v, "%s/AES-%d", impl[i].name, kl[k] * 8);
            MEASURE(plat, "AES-GCM encrypt+tag (incl. key setup)", v, 56, 4, runs, impl[i].f(kl[k], 56, 1));
            { char l[60]; snprintf(l, sizeof l, "gcm_enc_%d_%d", i, kl[k] * 8); emit_check(plat, l, out, 56); emit_check(plat, l, tag, 16); }
            MEASURE(plat, "AES-GCM decrypt+tag (incl. key setup)", v, 24, 4, runs, impl[i].f(kl[k], 24, 0));
        }
    }
    /* key schedule alone, to separate setup from per-message cost */
    {
        br_aes_ct_ctr_keys a; br_aes_small_ctr_keys b; br_aes_big_ctr_keys c;
        MEASURE(plat, "AES-256 key schedule only", "aes_ct", 32, 8, runs, br_aes_ct_ctr_init(&a, key32, 32); sink = ((uint8_t *)&a)[0]);
        MEASURE(plat, "AES-256 key schedule only", "aes_small", 32, 8, runs, br_aes_small_ctr_init(&b, key32, 32); sink = ((uint8_t *)&b)[0]);
        MEASURE(plat, "AES-256 key schedule only", "aes_big", 32, 8, runs, br_aes_big_ctr_init(&c, key32, 32); sink = ((uint8_t *)&c)[0]);
    }
}

/* ---- hashes / MAC / KDF ------------------------------------------------ */
static void bench_hash(const char *plat, int runs) {
    br_sha1_context s1; br_sha256_context s2; br_hmac_key_context kc; br_hmac_context hc; br_hkdf_context kd;
    MEASURE(plat, "T_H: SHA-1 (paper's T_H)", "bearssl", 32, 16, runs,
            br_sha1_init(&s1); br_sha1_update(&s1, msg, 32); br_sha1_out(&s1, hash); sink = hash[0]);
    emit_check(plat, "sha1_32B", hash, 20);
    MEASURE(plat, "T_H: SHA-1 (2 blocks)", "bearssl", 100, 16, runs,
            br_sha1_init(&s1); br_sha1_update(&s1, msg, 64); br_sha1_update(&s1, msg, 36); br_sha1_out(&s1, hash); sink = hash[0]);
    emit_check(plat, "sha1_100B", hash, 20);
    MEASURE(plat, "SHA-256 (PID = H2(lambda||t), 40 B)", "bearssl", 40, 16, runs,
            br_sha256_init(&s2); br_sha256_update(&s2, msg, 40); br_sha256_out(&s2, hash); sink = hash[0]);
    emit_check(plat, "sha256_40B", hash, 32);
    MEASURE(plat, "HMAC-SHA256 (incl. key setup)", "bearssl", 56, 8, runs,
            br_hmac_key_init(&kc, &br_sha256_vtable, key32, 32); br_hmac_init(&hc, &kc, 0);
            br_hmac_update(&hc, msg, 56); br_hmac_out(&hc, hash); sink = hash[0]);
    emit_check(plat, "hmac_sha256", hash, 32);
    MEASURE(plat, "HKDF-SHA256 extract+expand (64 B ikm to 32 B)", "bearssl", 64, 8, runs,
            br_hkdf_init(&kd, &br_sha256_vtable, NULL, 0); br_hkdf_inject(&kd, msg, 64); br_hkdf_flip(&kd);
            br_hkdf_produce(&kd, "hybrid-ecc-auth/session-key/v1", 30, hash, 32); sink = hash[0]);
    emit_check(plat, "hkdf_sha256", hash, 32);
}

/* ---- elliptic curve scalar multiplication (paper's T_ECM) -------------- */
static const char *ec_plat; static int ec_runs;
static void bench_ec_body(void) {
    const char *plat = ec_plat; int runs = ec_runs;
    struct { const char *name; const br_ec_impl *ec; int curve; } c[] = {
        {"P-256 ec_p256_m15", &br_ec_p256_m15, BR_EC_secp256r1},
#ifndef BENCH_NO_31 /* the ESP8266 core only ships the 15-bit-limb implementations */
        {"P-256 ec_p256_m31", &br_ec_p256_m31, BR_EC_secp256r1},
#endif
        {"P-256 ec_prime_i15(generic)", &br_ec_prime_i15, BR_EC_secp256r1},
#ifndef BENCH_NO_31
        {"P-256 ec_prime_i31(generic)", &br_ec_prime_i31, BR_EC_secp256r1},
#endif
        {"X25519 ec_c25519_m15", &br_ec_c25519_m15, BR_EC_curve25519},
#ifndef BENCH_NO_31
        {"X25519 ec_c25519_m31", &br_ec_c25519_m31, BR_EC_curve25519},
#endif
    };
    uint8_t scalar[32], P[133];
    for (int i = 0; i < 32; i++) scalar[i] = (uint8_t)(0x5a ^ (i * 29));
    scalar[0] &= 0x7f; /* keep below the group order */
    for (int i = 0; i < (int)(sizeof c / sizeof c[0]); i++) {
        size_t glen; const unsigned char *g = c[i].ec->generator(c[i].curve, &glen);
        int er = runs < 24 ? runs : 24; /* ECC is slow on MCUs: fewer runs */
        GEN_COPY(P, g, glen);
        uint32_t ok = 1; size_t gl = 1;
        MEASURE(plat, "T_ECM: scalar mult (variable base)", c[i].name, 32, 1, er,
                GEN_COPY(P, g, glen); ok &= c[i].ec->mul(P, glen, scalar, 32, c[i].curve); sink = P[1]);
        emit_check(plat, c[i].name, P, glen);
        MEASURE(plat, "scalar mult (fixed base; mulgen)", c[i].name, 32, 1, er,
                gl = c[i].ec->mulgen(P, scalar, 32, c[i].curve); sink = P[1]);
        emit_check(plat, c[i].name, P, gl);
        if (!ok || !gl) { char l[160]; snprintf(l, sizeof l, "BENCH_ERROR,%s,ec operation failed (mul ok=%u, mulgen len=%u)", c[i].name, (unsigned)ok, (unsigned)gl); bench_emit(l); }
    }
    bench_emit("BENCH_DONE");
}
static void bench_ec(const char *plat, int runs) { ec_plat = plat; ec_runs = runs; bench_big_stack(bench_ec_body); }

void bench_run_all(const char *plat, int runs) {
    fill();
    bench_emit("BENCH_HEADER,platform,op,variant,bytes,reps,runs,median_us,p25_us,p75_us,min_us,max_us");
    bench_hash(plat, runs);
    bench_aes_bare(plat, runs);
    bench_gcm(plat, runs);
#ifndef BENCH_SKIP_EC
    bench_ec(plat, runs);
#else
    bench_emit("BENCH_DONE");
#endif
}
