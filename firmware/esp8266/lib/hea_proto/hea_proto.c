#include "hea_proto.h"

#include <stdio.h>
#include <string.h>

#if defined(__has_include) && __has_include(<bearssl/bearssl.h>)
#include <bearssl/bearssl.h>
#else
#include "bearssl.h"
#endif

static const char INFO_ROOT[] = "hybrid-ecc-auth/pairwise-root/v1";
static const char INFO_SESSION[] = "hybrid-ecc-auth/session-key/v1";

/* ---- base64 -------------------------------------------------------- */
static const char B64[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

static size_t b64_encode(const uint8_t *in, size_t n, char *out) {
    size_t o = 0;
    for (size_t i = 0; i < n; i += 3) {
        uint32_t v = (uint32_t)in[i] << 16;
        if (i + 1 < n) v |= (uint32_t)in[i + 1] << 8;
        if (i + 2 < n) v |= in[i + 2];
        out[o++] = B64[(v >> 18) & 63];
        out[o++] = B64[(v >> 12) & 63];
        out[o++] = (i + 1 < n) ? B64[(v >> 6) & 63] : '=';
        out[o++] = (i + 2 < n) ? B64[v & 63] : '=';
    }
    out[o] = 0;
    return o;
}

static int b64_val(char c) {
    if (c >= 'A' && c <= 'Z') return c - 'A';
    if (c >= 'a' && c <= 'z') return c - 'a' + 26;
    if (c >= '0' && c <= '9') return c - '0' + 52;
    if (c == '+') return 62;
    if (c == '/') return 63;
    return -1;
}

/* returns decoded length or -1 */
static int b64_decode(const char *in, uint8_t *out, size_t cap) {
    size_t n = strlen(in), o = 0;
    if (n % 4) return -1;
    for (size_t i = 0; i < n; i += 4) {
        int a = b64_val(in[i]), b = b64_val(in[i + 1]);
        int c = in[i + 2] == '=' ? 0 : b64_val(in[i + 2]);
        int d = in[i + 3] == '=' ? 0 : b64_val(in[i + 3]);
        if (a < 0 || b < 0 || c < 0 || d < 0) return -1;
        uint32_t v = ((uint32_t)a << 18) | ((uint32_t)b << 12) | ((uint32_t)c << 6) | (uint32_t)d;
        int bytes = 3 - (in[i + 2] == '=') - (in[i + 3] == '=');
        if (o + bytes > cap) return -1;
        out[o++] = (v >> 16) & 0xff;
        if (bytes > 1) out[o++] = (v >> 8) & 0xff;
        if (bytes > 2) out[o++] = v & 0xff;
    }
    return (int)o;
}

/* ---- tiny JSON string-field extractor (handles \" and \\ escapes) --- */
/* Finds "key" : "value" (value may contain escapes) and unescapes into out.
 * Returns 0 on success. Good enough for the flat, ASCII-only envelopes the
 * reference server emits; not a general JSON parser. */
static int json_str(const char *js, const char *key, char *out, size_t cap) {
    char pat[24];
    snprintf(pat, sizeof pat, "\"%s\"", key);
    const char *p = strstr(js, pat);
    if (!p) return -1;
    p += strlen(pat);
    while (*p == ' ' || *p == ':') p++;
    if (*p != '"') return -1;
    p++;
    size_t o = 0;
    while (*p && *p != '"') {
        char c = *p++;
        if (c == '\\') {
            c = *p++;
            if (c == 'n') c = '\n';
            else if (c != '"' && c != '\\' && c != '/') return -1;
        }
        if (o + 1 >= cap) return -1;
        out[o++] = c;
    }
    if (*p != '"') return -1;
    out[o] = 0;
    return 0;
}

/* ---- primitives ----------------------------------------------------- */
static void put_u64(uint8_t *o, uint64_t v) {
    for (int i = 7; i >= 0; i--) { o[i] = v & 0xff; v >>= 8; }
}
static uint64_t get_u64(const uint8_t *o) {
    uint64_t v = 0;
    for (int i = 0; i < 8; i++) v = (v << 8) | o[i];
    return v;
}

/* HKDF-SHA256, salt=None (== HashLen zeros), 32-byte output. */
static void hkdf32(const uint8_t *ikm, size_t ikm_len, const char *info, uint8_t out[32]) {
    br_hkdf_context hc;
    br_hkdf_init(&hc, &br_sha256_vtable, NULL, 0);
    br_hkdf_inject(&hc, ikm, ikm_len);
    br_hkdf_flip(&hc);
    br_hkdf_produce(&hc, info, strlen(info), out, 32);
}

static void sha256_pid(const uint8_t lam[32], uint64_t epoch, uint8_t out[32]) {
    br_sha256_context sc;
    uint8_t e[8];
    put_u64(e, epoch);
    br_sha256_init(&sc);
    br_sha256_update(&sc, lam, 32);
    br_sha256_update(&sc, e, 8);
    br_sha256_out(&sc, out);
}

/* AES-256-GCM. 12-byte iv, 16-byte tag. Constant-time (ct) AES + ctmul32 GHASH,
 * the small/portable BearSSL implementations. */
static void gcm_run(const uint8_t key[32], const uint8_t iv[12], const uint8_t *aad, size_t aad_len, uint8_t *data,
                    size_t len, int encrypt, uint8_t tag[16]) {
    br_aes_ct_ctr_keys bc;
    br_gcm_context gc;
    br_aes_ct_ctr_init(&bc, key, 32);
    br_gcm_init(&gc, &bc.vtable, br_ghash_ctmul32);
    br_gcm_reset(&gc, iv, 12);
    br_gcm_aad_inject(&gc, aad, aad_len);
    br_gcm_flip(&gc);
    br_gcm_run(&gc, encrypt, data, len);
    br_gcm_get_tag(&gc, tag); /* for decrypt: computed tag, caller compares */
}

/* ---- public API ----------------------------------------------------- */
void hea_init(hea_device *d, const uint8_t lam_device[32], const uint8_t lam_server[32], const char *server_id,
              uint64_t epoch) {
    uint8_t ikm[64];
    memcpy(d->lam, lam_device, 32);
    memcpy(ikm, lam_device, 32); /* device lambda first, server second (Eq. 9) */
    memcpy(ikm + 32, lam_server, 32);
    hkdf32(ikm, 64, INFO_ROOT, d->k_star);
    memset(d->server_id, 0, sizeof d->server_id);
    strncpy(d->server_id, server_id, HEA_ID_MAX - 1);
    d->epoch = epoch;
}

size_t hea_build_m1(hea_device *d, hea_pending *p, uint8_t *out, size_t cap) {
    uint8_t pt[HEA_PID_LEN + HEA_NONCE_LEN + 8], iv[12], tag[16];
    char b_pid[48], b_iv[20], b_ct[80], b_tag[28];

    p->epoch = d->epoch;
    sha256_pid(d->lam, p->epoch, p->pid);
    hea_random(p->n_i, HEA_NONCE_LEN);
    hea_random(iv, 12);

    memcpy(pt, p->pid, HEA_PID_LEN);
    memcpy(pt + HEA_PID_LEN, p->n_i, HEA_NONCE_LEN);
    put_u64(pt + HEA_PID_LEN + HEA_NONCE_LEN, p->epoch);
    gcm_run(d->k_star, iv, NULL, 0, pt, sizeof pt, 1, tag); /* pt is now ciphertext */

    b64_encode(p->pid, HEA_PID_LEN, b_pid);
    b64_encode(iv, 12, b_iv);
    b64_encode(pt, sizeof pt, b_ct);
    b64_encode(tag, 16, b_tag);

    /* Same key order and separators as json.dumps(..., separators=(",", ":")) */
    int n = snprintf((char *)out, cap, "{\"v\":1,\"type\":\"M1\",\"pid\":\"%s\",\"nonce\":\"%s\",\"ct\":\"%s\",\"tag\":\"%s\"}",
                     b_pid, b_iv, b_ct, b_tag);
    if (n < 0 || (size_t)n >= cap) return 0;
    d->epoch++;
    return (size_t)n;
}

static int fail(char *err, size_t cap, int code, const char *msg) {
    if (err && cap) snprintf(err, cap, "%s", msg);
    return code;
}

int hea_complete(const hea_device *d, const hea_pending *p, const uint8_t *envelope, size_t len,
                 uint8_t session_key[32], char *err, size_t err_cap) {
    /* Large buffers are static: the ESP8266 task ("cont") stack is only 4 KB.
     * Not re-entrant; the device runs one handshake at a time. */
    static char env[1024], payload[640], b_ct[96];
    static uint8_t ct[64];
    char sid[HEA_ID_MAX], b_iv[24], b_tag[32];
    uint8_t iv[12], tag[16], calc[16], aad[HEA_PID_LEN + HEA_NONCE_LEN];

    if (len >= sizeof env) return fail(err, err_cap, HEA_E_FORMAT, "envelope too large");
    memcpy(env, envelope, len);
    env[len] = 0;

    if (!strstr(env, "\"ok\": true") && !strstr(env, "\"ok\":true")) {
        char et[48] = "?", msg[128] = "?";
        json_str(env, "error_type", et, sizeof et);
        json_str(env, "message", msg, sizeof msg);
        if (err && err_cap) snprintf(err, err_cap, "%s: %s", et, msg);
        return HEA_E_REJECTED;
    }
    if (json_str(env, "payload", payload, sizeof payload)) return fail(err, err_cap, HEA_E_FORMAT, "no payload");
    if (json_str(payload, "sid", sid, sizeof sid) || json_str(payload, "nonce", b_iv, sizeof b_iv) ||
        json_str(payload, "ct", b_ct, sizeof b_ct) || json_str(payload, "tag", b_tag, sizeof b_tag))
        return fail(err, err_cap, HEA_E_FORMAT, "malformed M2");
    if (strcmp(sid, d->server_id) != 0) return fail(err, err_cap, HEA_E_FORMAT, "M2 from unexpected server id");

    if (b64_decode(b_iv, iv, sizeof iv) != 12 || b64_decode(b_tag, tag, sizeof tag) != 16)
        return fail(err, err_cap, HEA_E_FORMAT, "bad nonce/tag length");
    int ctl = b64_decode(b_ct, ct, sizeof ct);
    if (ctl < 8 + 1) return fail(err, err_cap, HEA_E_FORMAT, "bad ciphertext length");

    memcpy(aad, p->pid, HEA_PID_LEN);
    memcpy(aad + HEA_PID_LEN, p->n_i, HEA_NONCE_LEN);
    gcm_run(d->k_star, iv, aad, sizeof aad, ct, (size_t)ctl, 0, calc); /* ct is now plaintext */

    /* constant-time tag compare */
    uint8_t diff = 0;
    for (int i = 0; i < 16; i++) diff |= calc[i] ^ tag[i];
    if (diff) return fail(err, err_cap, HEA_E_INTEGRITY, "M2 tag mismatch (sigma_2)");

    size_t nj_len = (size_t)ctl - 8;
    if (get_u64(ct + nj_len) != p->epoch) return fail(err, err_cap, HEA_E_EPOCH, "M2 epoch mismatch");

    uint8_t ikm[HEA_KEY_LEN + 64 + 8];
    if (nj_len > 64) return fail(err, err_cap, HEA_E_FORMAT, "N_j too long");
    memcpy(ikm, d->k_star, 32);
    memcpy(ikm + 32, p->n_i, HEA_NONCE_LEN);
    memcpy(ikm + 32 + HEA_NONCE_LEN, ct, nj_len);
    put_u64(ikm + 32 + HEA_NONCE_LEN + nj_len, p->epoch);
    hkdf32(ikm, 32 + HEA_NONCE_LEN + nj_len + 8, INFO_SESSION, session_key);
    return 0;
}
