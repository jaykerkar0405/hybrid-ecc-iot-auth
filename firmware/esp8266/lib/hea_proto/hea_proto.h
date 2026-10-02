/* Device side of the hybrid ECC + symmetric-key mutual authentication
 * protocol (see hybrid_ecc_auth/protocol/device.py). Portable C: depends only
 * on BearSSL and on a platform-provided hea_random(). Byte-compatible with the
 * Python server's M1/M2 wire format (JSON + base64, v=1). */
#ifndef HEA_PROTO_H
#define HEA_PROTO_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define HEA_KEY_LEN 32
#define HEA_NONCE_LEN 16 /* N_i / N_j, ell = 128 bits */
#define HEA_PID_LEN 32
#define HEA_ID_MAX 32

/* Platform hook: fill `out` with cryptographically secure random bytes. */
void hea_random(uint8_t *out, size_t len);

typedef struct {
    uint8_t lam[HEA_KEY_LEN];    /* device long-term secret (big-endian) */
    uint8_t k_star[HEA_KEY_LEN]; /* pairwise root, Eq. 9 */
    char server_id[HEA_ID_MAX];
    uint64_t epoch; /* next epoch t to use; caller persists it */
} hea_device;

typedef struct {
    uint8_t pid[HEA_PID_LEN];
    uint8_t n_i[HEA_NONCE_LEN];
    uint64_t epoch;
} hea_pending;

void hea_init(hea_device *d, const uint8_t lam_device[HEA_KEY_LEN], const uint8_t lam_server[HEA_KEY_LEN],
              const char *server_id, uint64_t epoch);

/* Build M1 (JSON, no length prefix) into out. Returns length, 0 on overflow.
 * Increments d->epoch (as the Python reference does, even if rejected). */
size_t hea_build_m1(hea_device *d, hea_pending *p, uint8_t *out, size_t cap);

/* Parse the server envelope, verify M2, derive the session key.
 * Returns 0 on success, otherwise a negative HEA_E_* and a message in err. */
#define HEA_E_REJECTED (-1) /* server sent {"ok": false, ...} */
#define HEA_E_FORMAT (-2)
#define HEA_E_INTEGRITY (-3)
#define HEA_E_EPOCH (-4)
int hea_complete(const hea_device *d, const hea_pending *p, const uint8_t *envelope, size_t len,
                 uint8_t session_key[HEA_KEY_LEN], char *err, size_t err_cap);

#ifdef __cplusplus
}
#endif
#endif
