/* Hardware-assisted primitive costs through OpenSSL libcrypto, measured the way the protocol uses them:
 * AES-256-GCM per MESSAGE (fresh IV, update, final, tag; key schedule cached on the context), one-shot SHA-1 on 32 B
 * (1 block) and 100 B (2 blocks), and HKDF-SHA256 (64 B ikm -> 32 B). NOT an MCU. Output matches prim_bench CSV rows.
 *   cc -O2 libcrypto_bench.c -I$(brew --prefix openssl@3)/include -L$(brew --prefix openssl@3)/lib -lcrypto */
#include <openssl/evp.h>
#include <openssl/sha.h>
#include <openssl/hmac.h>
#include <openssl/kdf.h>
#include <openssl/core_names.h>
#include <openssl/params.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static double now_ns(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec * 1e9 + t.tv_nsec; }
static int cmpd(const void *a, const void *b) { double x = *(double *)a, y = *(double *)b; return (x > y) - (x < y); }
static const char *plat;
static void report(const char *op, const char *variant, int bytes, double *s, int n) {
    qsort(s, n, sizeof *s, cmpd);
    printf("BENCH,%s,%s,%s,%d,%d,%d,%.3f,%.3f,%.3f,%.3f,%.3f\n", plat, op, variant, bytes, 2000, n, s[n/2]/1e3, s[n/4]/1e3, s[3*n/4]/1e3, s[0]/1e3, s[n-1]/1e3);
}
#define RUNS 100
#define REPS 2000
#define TIME(op, variant, bytes, STMT) do { double s_[RUNS]; for (int r_ = 0; r_ < RUNS; r_++) { double t0_ = now_ns(); for (int k_ = 0; k_ < REPS; k_++) { STMT; } s_[r_] = (now_ns() - t0_) / REPS; } report(op, variant, bytes, s_, RUNS); } while (0)

static EVP_KDF *kdf_g;
/* HMAC-SHA256 on the low-level SHA-256 API (hardware-accelerated, no EVP object setup) */
static void hmac256_ll(const unsigned char *key, size_t kl, const unsigned char *m, size_t ml, unsigned char out[32]) {
    unsigned char kp[64] = {0}, pad[64], inner[32]; SHA256_CTX c;
    memcpy(kp, key, kl);
    for (int i = 0; i < 64; i++) pad[i] = kp[i] ^ 0x36;
    SHA256_Init(&c); SHA256_Update(&c, pad, 64); SHA256_Update(&c, m, ml); SHA256_Final(inner, &c);
    for (int i = 0; i < 64; i++) pad[i] = kp[i] ^ 0x5c;
    SHA256_Init(&c); SHA256_Update(&c, pad, 64); SHA256_Update(&c, inner, 32); SHA256_Final(out, &c);
}
static void hkdf_once(const unsigned char *ikm, unsigned char *okm) {
    char dg[] = "SHA256"; static const char info[] = "hybrid-ecc-auth/session-key/v1";
    EVP_KDF_CTX *kc = EVP_KDF_CTX_new(kdf_g);
    OSSL_PARAM p[4];
    p[0] = OSSL_PARAM_construct_utf8_string(OSSL_KDF_PARAM_DIGEST, dg, 0);
    p[1] = OSSL_PARAM_construct_octet_string(OSSL_KDF_PARAM_KEY, (void *)ikm, 72);
    p[2] = OSSL_PARAM_construct_octet_string(OSSL_KDF_PARAM_INFO, (void *)info, sizeof info - 1);
    p[3] = OSSL_PARAM_construct_end();
    EVP_KDF_derive(kc, okm, 32, p);
    EVP_KDF_CTX_free(kc);
}

int main(int argc, char **argv) {
    plat = argc > 1 ? argv[1] : "libcrypto";
    unsigned char key[32], iv[12], msg[128], out[160], tag[16], hash[64], okm[32];
    for (int i = 0; i < 32; i++) key[i] = i * 7 + 1;
    for (int i = 0; i < 12; i++) iv[i] = i + 3;
    for (int i = 0; i < 128; i++) msg[i] = i * 13 + 5;
    volatile unsigned char sink = 0; int len, flen; unsigned hl;

    EVP_MD_CTX *md = EVP_MD_CTX_new();
    TIME("T_H: SHA-1 (1 block; libcrypto)", "openssl-hw", 32, EVP_DigestInit_ex(md, EVP_sha1(), NULL); EVP_DigestUpdate(md, msg, 32); EVP_DigestFinal_ex(md, hash, &hl); sink = hash[0]);
    TIME("T_H: SHA-1 (2 blocks; libcrypto)", "openssl-hw", 100, EVP_DigestInit_ex(md, EVP_sha1(), NULL); EVP_DigestUpdate(md, msg, 100); EVP_DigestFinal_ex(md, hash, &hl); sink = hash[0]);

    /* low-level SHA-1 (no EVP object setup): the fairest per-call cost for the hash side */
    SHA_CTX sc;
    TIME("T_H: SHA-1 (1 block; libcrypto low-level)", "openssl-hw", 32, SHA1_Init(&sc); SHA1_Update(&sc, msg, 32); SHA1_Final(hash, &sc); sink = hash[0]);
    TIME("T_H: SHA-1 (2 blocks; libcrypto low-level)", "openssl-hw", 100, SHA1_Init(&sc); SHA1_Update(&sc, msg, 100); SHA1_Final(hash, &sc); sink = hash[0]);

    /* GCM: key set once (schedule cached), per-message IV re-init, update, final, tag */
    EVP_CIPHER_CTX *c = EVP_CIPHER_CTX_new();
    EVP_EncryptInit_ex(c, EVP_aes_256_gcm(), NULL, key, NULL);
    EVP_CIPHER_CTX_ctrl(c, EVP_CTRL_GCM_SET_IVLEN, 12, NULL);
    TIME("AES-256-GCM encrypt 56 B per message (libcrypto; key cached)", "openssl-hw", 56,
         EVP_EncryptInit_ex(c, NULL, NULL, NULL, iv); EVP_EncryptUpdate(c, out, &len, msg, 56); EVP_EncryptFinal_ex(c, out + len, &flen);
         EVP_CIPHER_CTX_ctrl(c, EVP_CTRL_GCM_GET_TAG, 16, tag); sink = out[0] ^ tag[0]);
    unsigned char ct[56], t2[16];
    EVP_EncryptInit_ex(c, NULL, NULL, NULL, iv); EVP_EncryptUpdate(c, ct, &len, msg, 56); EVP_EncryptFinal_ex(c, out, &flen); EVP_CIPHER_CTX_ctrl(c, EVP_CTRL_GCM_GET_TAG, 16, t2);
    EVP_CIPHER_CTX *d = EVP_CIPHER_CTX_new();
    EVP_DecryptInit_ex(d, EVP_aes_256_gcm(), NULL, key, NULL); EVP_CIPHER_CTX_ctrl(d, EVP_CTRL_GCM_SET_IVLEN, 12, NULL);
    int ok = 1;
    TIME("AES-256-GCM decrypt+verify 56 B per message (libcrypto; key cached)", "openssl-hw", 56,
         EVP_DecryptInit_ex(d, NULL, NULL, NULL, iv); EVP_DecryptUpdate(d, out, &len, ct, 56); EVP_CIPHER_CTX_ctrl(d, EVP_CTRL_GCM_SET_TAG, 16, t2);
         ok &= EVP_DecryptFinal_ex(d, out + len, &flen) > 0; sink = out[0]);
    if (!ok) { fprintf(stderr, "GCM verify failed\n"); return 1; }
    /* with key schedule paid every message */
    EVP_CIPHER_CTX *c2 = EVP_CIPHER_CTX_new();
    TIME("AES-256-GCM encrypt 56 B per message (libcrypto; incl. key setup)", "openssl-hw", 56,
         EVP_EncryptInit_ex(c2, EVP_aes_256_gcm(), NULL, NULL, NULL); EVP_CIPHER_CTX_ctrl(c2, EVP_CTRL_GCM_SET_IVLEN, 12, NULL); EVP_EncryptInit_ex(c2, NULL, NULL, key, iv);
         EVP_EncryptUpdate(c2, out, &len, msg, 56); EVP_EncryptFinal_ex(c2, out + len, &flen); EVP_CIPHER_CTX_ctrl(c2, EVP_CTRL_GCM_GET_TAG, 16, tag); sink = out[0]);

    /* HKDF-SHA256, ikm 72 B (k* || N_i || N_j || t, as in Eq. 16), 32 B out */
    kdf_g = EVP_KDF_fetch(NULL, "HKDF", NULL);
    TIME("HKDF-SHA256 extract+expand (72 B ikm to 32 B; libcrypto)", "openssl-hw", 72, hkdf_once(msg, okm); sink = okm[0]);
    /* HKDF built from two one-shot HMACs (extract with zero salt, expand one block): lower per-call overhead than EVP_KDF */
    unsigned char zero[32] = {0}, prk[32], exp[64]; unsigned int pl;
    memcpy(exp, "hybrid-ecc-auth/session-key/v1", 30); exp[30] = 1;
    TIME("HKDF-SHA256 as 2 HMAC calls (72 B ikm to 32 B; libcrypto)", "openssl-hw", 72,
         HMAC(EVP_sha256(), zero, 32, msg, 72, prk, &pl); HMAC(EVP_sha256(), prk, 32, exp, 31, okm, &pl); sink = okm[0]);
    TIME("HKDF-SHA256 on low-level SHA-256 (72 B ikm to 32 B; libcrypto low-level)", "openssl-hw", 72,
         hmac256_ll(zero, 32, msg, 72, prk); hmac256_ll(prk, 32, exp, 31, okm); sink = okm[0]);
    /* correctness: low-level HKDF must equal the EVP_KDF result */
    unsigned char ref[32]; hkdf_once(msg, ref); hmac256_ll(zero, 32, msg, 72, prk); hmac256_ll(prk, 32, exp, 31, okm);
    if (memcmp(ref, okm, 32)) { fprintf(stderr, "low-level HKDF mismatch\n"); return 1; }
    return 0;
}
