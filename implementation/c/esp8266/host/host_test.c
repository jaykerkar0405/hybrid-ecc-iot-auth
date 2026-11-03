/* Native build of the ESP8266 protocol core, used to prove byte-compatibility
 * with the Python server without hardware.
 * usage: host_test <lam_dev_hex> <lam_srv_hex> <server_id> <host> <port> <n> */
#include <arpa/inet.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

#include "bearssl.h"
#include "hea_proto.h"

void hea_random(uint8_t *out, size_t len) {
    FILE *f = fopen("/dev/urandom", "rb");
    if (!f || fread(out, 1, len, f) != len) abort();
    fclose(f);
}

static void unhex(const char *h, uint8_t *o, size_t n) {
    for (size_t i = 0; i < n; i++) { unsigned v; sscanf(h + 2 * i, "%2x", &v); o[i] = v; }
}

static int rx(int s, uint8_t *b, size_t n) {
    while (n) { ssize_t r = read(s, b, n); if (r <= 0) return -1; b += r; n -= r; }
    return 0;
}

/* one framed request/response; returns envelope length or -1 */
static int exchange(const char *host, int port, const uint8_t *m1, size_t m1len, uint8_t *resp, size_t cap) {
    int s = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in a = {.sin_family = AF_INET, .sin_port = htons(port)};
    inet_pton(AF_INET, host, &a.sin_addr);
    if (connect(s, (void *)&a, sizeof a)) { close(s); return -1; }
    uint32_t be = htonl((uint32_t)m1len);
    write(s, &be, 4);
    write(s, m1, m1len);
    uint8_t h[4];
    if (rx(s, h, 4)) { close(s); return -1; }
    uint32_t n = ((uint32_t)h[0] << 24) | (h[1] << 16) | (h[2] << 8) | h[3];
    if (n > cap || rx(s, resp, n)) { close(s); return -1; }
    close(s);
    return (int)n;
}

static void fingerprint(const uint8_t *key, char *out) {
    uint8_t d[32];
    br_sha256_context c;
    br_sha256_init(&c); br_sha256_update(&c, key, 32); br_sha256_out(&c, d);
    for (int i = 0; i < 8; i++) sprintf(out + 2 * i, "%02x", d[i]);
}

int main(int argc, char **argv) {
    if (argc < 7) return 2;
    uint8_t ld[32], ls[32], m1[512], resp[1024], key[32];
    unhex(argv[1], ld, 32); unhex(argv[2], ls, 32);
    int n = atoi(argv[6]);
    hea_device dev; hea_pending pend; char err[160], fp[20];
    hea_init(&dev, ld, ls, argv[3], 0);
    int ok = 0;
    uint8_t last_m1[512]; size_t last_len = 0;
    for (int i = 0; i < n; i++) {
        size_t l = hea_build_m1(&dev, &pend, m1, sizeof m1);
        memcpy(last_m1, m1, l); last_len = l;
        int r = exchange(argv[4], atoi(argv[5]), m1, l, resp, sizeof resp);
        if (r < 0) { printf("RESULT transport_error\n"); return 1; }
        int rc = hea_complete(&dev, &pend, resp, r, key, err, sizeof err);
        if (rc) { printf("RESULT fail epoch=%d rc=%d %s\n", i, rc, err); continue; }
        fingerprint(key, fp);
        printf("RESULT ok epoch=%d m1_bytes=%zu fp=%s\n", i, l, fp);
        ok++;
    }
    /* replay the last M1: the server must reject it */
    int r = exchange(argv[4], atoi(argv[5]), last_m1, last_len, resp, sizeof resp);
    int rc = hea_complete(&dev, &pend, resp, r, key, err, sizeof err);
    printf("RESULT replay rc=%d %s\n", rc, err);
    printf("RESULT summary ok=%d/%d\n", ok, n);
    return ok == n && rc == HEA_E_REJECTED ? 0 : 1;
}
