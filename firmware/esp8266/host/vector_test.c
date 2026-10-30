/* Conformance of the ESP8266 device core to the independent reference vectors
 * (hybrid_ecc_auth/tests/vectors). Randomness is replaced by the vectors' fixed
 * N_i and GCM IV, so every output byte can be compared with the expected value.
 * usage: vector_test <reference_vectors.txt> */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "hea_proto.h"

static int failures, checks;
static uint8_t rnd_queue[64];
static size_t rnd_len, rnd_pos;

void hea_random(uint8_t *out, size_t len) {
    if (rnd_pos + len > rnd_len) { fprintf(stderr, "hea_random: queue exhausted\n"); abort(); }
    memcpy(out, rnd_queue + rnd_pos, len);
    rnd_pos += len;
}

static char *lines[256];
static size_t nlines;

static const char *get(const char *key) {
    size_t kl = strlen(key);
    for (size_t i = 0; i < nlines; i++)
        if (!strncmp(lines[i], key, kl) && lines[i][kl] == '=') return lines[i] + kl + 1;
    fprintf(stderr, "missing key %s\n", key);
    abort();
}

static size_t unhex(const char *h, uint8_t *o, size_t cap) {
    size_t n = strlen(h) / 2;
    if (n > cap) abort();
    for (size_t i = 0; i < n; i++) { unsigned v; sscanf(h + 2 * i, "%2x", &v); o[i] = (uint8_t)v; }
    return n;
}

static void check(int ok, const char *what) {
    checks++;
    if (!ok) { failures++; printf("FAIL  %s\n", what); } else printf("ok    %s\n", what);
}

static void queue_random(const char *n_i_hex, const char *iv_hex) {
    rnd_len = unhex(n_i_hex, rnd_queue, sizeof rnd_queue);
    rnd_len += unhex(iv_hex, rnd_queue + rnd_len, sizeof rnd_queue - rnd_len);
    rnd_pos = 0;
}

static void run_case(const char *name, const uint8_t lam_d[32], const uint8_t lam_s[32], const char *sid,
                     const uint8_t root[32]) {
    char key[64], msg[96], err[160];
    uint8_t expect[32], got[32], m1[512];
    hea_device dev;
    hea_pending pend;
    uint64_t epoch = strtoull(get((snprintf(key, sizeof key, "%s.epoch", name), key)), NULL, 10);

    hea_init(&dev, lam_d, lam_s, sid, epoch);
    snprintf(msg, sizeof msg, "%s: pairwise root k*", name);
    check(!memcmp(dev.k_star, root, 32), msg);

    snprintf(key, sizeof key, "%s.n_i", name); const char *n_i = get(key);
    snprintf(key, sizeof key, "%s.iv_m1", name); const char *iv = get(key);
    queue_random(n_i, iv);
    size_t n = hea_build_m1(&dev, &pend, m1, sizeof m1);
    snprintf(key, sizeof key, "%s.m1_wire", name);
    const char *want_m1 = get(key);
    snprintf(msg, sizeof msg, "%s: M1 wire bytes (PID, C1, mu_1)", name);
    check(n == strlen(want_m1) && !memcmp(m1, want_m1, n), msg);
    snprintf(msg, sizeof msg, "%s: epoch advanced after M1", name);
    check(dev.epoch == epoch + 1, msg);

    snprintf(key, sizeof key, "%s.envelope", name);
    const char *env = get(key);
    snprintf(key, sizeof key, "%s.session_key", name);
    unhex(get(key), expect, 32);
    int rc = hea_complete(&dev, &pend, (const uint8_t *)env, strlen(env), got, err, sizeof err);
    snprintf(msg, sizeof msg, "%s: M2 accepted, session key K", name);
    check(rc == 0 && !memcmp(got, expect, 32), msg);

    /* Tamper with one base64 character in each field of M2; GCM must reject it. */
    static const char *fields[] = {"\\\"ct\\\":\\\"", "\\\"tag\\\":\\\"", "\\\"nonce\\\":\\\""};
    static const char *labels[] = {"ciphertext", "tag", "IV"};
    for (int f = 0; f < 3; f++) {
        char bad[1024];
        strncpy(bad, env, sizeof bad - 1); bad[sizeof bad - 1] = 0;
        char *p = strstr(bad, fields[f]);
        if (!p) { check(0, "tamper: field not found"); continue; }
        p += strlen(fields[f]);
        *p = (*p == 'A') ? 'B' : 'A';
        rc = hea_complete(&dev, &pend, (const uint8_t *)bad, strlen(bad), got, err, sizeof err);
        snprintf(msg, sizeof msg, "%s: tampered M2 %s rejected", name, labels[f]);
        check(rc == HEA_E_INTEGRITY, msg);
    }
}

int main(int argc, char **argv) {
    if (argc < 2) return 2;
    FILE *fp = fopen(argv[1], "r");
    if (!fp) { perror(argv[1]); return 2; }
    static char buf[1 << 16];
    char *line;
    size_t used = 0;
    static char row[4096];
    while ((line = fgets(row, sizeof row, fp))) {
        size_t l = strlen(row);
        while (l && (row[l - 1] == '\n' || row[l - 1] == '\r')) row[--l] = 0;
        if (used + l + 1 > sizeof buf || nlines >= 256) abort();
        memcpy(buf + used, row, l + 1);
        lines[nlines++] = buf + used;
        used += l + 1;
    }
    fclose(fp);

    uint8_t lam_d[32], lam_s[32], root[32];
    unhex(get("lambda_device"), lam_d, 32);
    unhex(get("lambda_server"), lam_s, 32);
    unhex(get("pairwise_root"), root, 32);
    const char *sid = get("server_id");

    run_case("epoch0", lam_d, lam_s, sid, root);
    run_case("epoch3", lam_d, lam_s, sid, root);

    /* Cross-session replay: epoch0's M2 must not verify against epoch3's outstanding request. */
    {
        hea_device dev; hea_pending pend; uint8_t m1[512], got[32]; char err[160];
        hea_init(&dev, lam_d, lam_s, sid, 3);
        queue_random(get("epoch3.n_i"), get("epoch3.iv_m1"));
        hea_build_m1(&dev, &pend, m1, sizeof m1);
        const char *stale = get("epoch0.envelope");
        int rc = hea_complete(&dev, &pend, (const uint8_t *)stale, strlen(stale), got, err, sizeof err);
        check(rc == HEA_E_INTEGRITY, "replay: M2 of another session rejected");
    }

    printf("%d checks, %d failed\n", checks, failures);
    return failures ? 1 : 0;
}
