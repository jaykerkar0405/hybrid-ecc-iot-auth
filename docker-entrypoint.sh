#!/usr/bin/env bash
set -eo pipefail

# ==============================================================================
# IoT Environment Simulation Entrypoint
# ==============================================================================

apply_traffic_control() {
    local preset="${IOT_LINK_PRESET:-zigbee}"
    local iface="${IOT_IFACE:-eth0}"

    if [ "$ENABLE_IOT_NETWORK_SHAPING" = "1" ] || [ "$ENABLE_IOT_NETWORK_SHAPING" = "true" ]; then
        echo "==> Configuring IoT Network Shaping on interface: $iface (Preset: $preset) <=="
        
        # Reset existing qdisc if any
        sudo tc qdisc del dev "$iface" root 2>/dev/null || true

        case "$preset" in
            "zigbee"|"802.15.4")
                echo "[IoT Network] Emulating IEEE 802.15.4 / Zigbee (250 kbps, 25ms delay, 5ms jitter)"
                sudo tc qdisc add dev "$iface" root handle 1: netem delay 25ms 5ms
                sudo tc qdisc add dev "$iface" parent 1: handle 2: tbf rate 250kbit burst 32kbit latency 400ms
                ;;
            "lora"|"lorawan")
                echo "[IoT Network] Emulating LoRaWAN (50 kbps, 100ms delay, 15ms jitter, 1% loss)"
                sudo tc qdisc add dev "$iface" root handle 1: netem delay 100ms 15ms loss 1%
                sudo tc qdisc add dev "$iface" parent 1: handle 2: tbf rate 50kbit burst 16kbit latency 800ms
                ;;
            "ble")
                echo "[IoT Network] Emulating Bluetooth Low Energy (1 Mbps, 15ms delay, 3ms jitter)"
                sudo tc qdisc add dev "$iface" root handle 1: netem delay 15ms 3ms
                sudo tc qdisc add dev "$iface" parent 1: handle 2: tbf rate 1mbit burst 64kbit latency 200ms
                ;;
            *)
                echo "[IoT Network] Custom delay: 25ms"
                sudo tc qdisc add dev "$iface" root netem delay 25ms 5ms
                ;;
        esac
    fi
# Fix permissions on any mounted host volumes
if [ -d "/app/bench_output" ]; then
    sudo chown -R iotuser:iotuser /app/bench_output 2>/dev/null || true
    sudo chmod 777 /app/bench_output 2>/dev/null || true
fi
if [ -d "/app/creds" ]; then
    sudo chown -R iotuser:iotuser /app/creds 2>/dev/null || true
    sudo chmod 777 /app/creds 2>/dev/null || true
fi

apply_traffic_control

case "$1" in
    "bench")
        shift
        echo "==> Running Quick / CI Benchmark Suite <=="
        mkdir -p /app/bench_output
        exec python -m hybrid_ecc_auth.bench.harness --out /app/bench_output "$@"
        ;;
    "bench-full")
        shift
        echo "==> Running Full Paper-Scale Benchmark Suite (1000 trials, population sweep) <=="
        mkdir -p /app/bench_output
        exec python -m hybrid_ecc_auth.bench.harness --full --out /app/bench_output "$@"
        ;;
    "test")
        shift
        echo "==> Running Test Suite with Coverage <=="
        exec pytest hybrid_ecc_auth/tests/ --cov=hybrid_ecc_auth.protocol --cov=hybrid_ecc_auth.crypto --cov-report=term-missing "$@"
        ;;
    "server")
        shift
        exec hea-server start "$@"
        ;;
    "device")
        shift
        exec hea-device authenticate "$@"
        ;;
    "ta")
        shift
        exec hea-ta "$@"
        ;;
    "bash"|"sh")
        exec "$@"
        ;;
    *)
        exec "$@"
        ;;
esac

