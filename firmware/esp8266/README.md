# ESP8266 (NodeMCU) device port

C port of the **device side** of the protocol (`hybrid_ecc_auth/protocol/device.py`).
Talks to the unmodified Python `Server` over the same framed-JSON TCP wire format.

- `lib/hea_proto/` – portable C core (BearSSL: AES-256-GCM, SHA-256, HKDF-SHA256). No Arduino deps.
- `src/main.cpp` – Arduino firmware: Wi-Fi, handshake loop, per-step timings, replay test.
  The epoch is persisted to flash (the Python reference keeps it in RAM and resets it on restart).
- `host/` – the same core built natively for macOS/Linux; `tools/interop.py` checks it against the real Python server.
- Offline enrollment stays on the laptop (P-256/TA math is not run on the chip); the board gets λ_device and λ_server.

## Verify without hardware
    make -C firmware/esp8266/host
    .venv/bin/python firmware/esp8266/tools/interop.py -n 20

## Run on the board
    python firmware/esp8266/tools/gen_config.py --ssid <wifi> --server-host <mac-lan-ip>   # writes include/config.h (gitignored)
    pio run -t upload && pio device monitor                                                  # 115200 baud
    .venv/bin/python firmware/esp8266/tools/interop.py --listen                              # in another terminal
Compare the `fp=` session-key fingerprints printed by the board and by the server.
If you restart the server, send `z` over serial to reset the device epoch to 0.

Notes: the ESP8266 RNG is only high quality while the radio is on (we join Wi-Fi first). 80 MHz stock clock;
set `board_build.f_cpu = 160000000L` to compare. No hardware crypto: all AES/SHA runs in software.
