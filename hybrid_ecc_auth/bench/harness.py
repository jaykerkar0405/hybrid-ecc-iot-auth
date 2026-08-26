"""BR-4: runs the full benchmark suite -- proposed-scheme measurements
(bench/proposed.py) plus the paper-reference baseline tables
(bench/baselines/) -- and assembles one machine-readable results dict that
bench/report.py renders into Markdown/HTML/PNG artifacts.
"""

from __future__ import annotations

import platform
import sys
import time

import cryptography

from . import proposed
from .baselines import (
    BASELINE_COMMUNICATION,
    BASELINE_COMPUTATION_FORMULAS,
    BASELINE_STORAGE,
    TABLE_III_CONSTANTS,
    evaluate_formula,
)
from .proposed import BENCH_SERVER_ID
from ..protocol.device import Device
from ..protocol.server import Server
from ..protocol.ta import TrustedAuthority

#: Mirrors the paper's Table II population scale (100-1000 devices) and its
#: Figures' x-axis sample points (relabeled "devices" per PRD BR-2.3).
DEFAULT_DEVICE_POPULATION_POINTS = [100, 300, 600, 900, 1200, 1500, 1800]


def environment_fingerprint() -> dict:
    """Reproducibility (Section 8 NFR): record what actually produced the
    numbers, since this PoC deliberately measures real hardware instead of
    reusing the paper's assumed constants (PRD 6.2)."""
    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor() or platform.machine(),
        "cryptography_version": cryptography.__version__,
    }


def measure_processing_cost_vs_population(
    device_counts: list[int] | None = None,
    trials_per_point: int = 50,
) -> list[dict]:
    """BR-2.3: server-side handle_auth_request() latency as a function of
    the number of devices enrolled with that server.

    This is a genuine, measured effect of this implementation's design:
    Server.resolve_pseudonym (FR-4.2) does a bounded linear scan over its
    known peers to resolve an incoming pseudonym, so per-session server
    cost grows with the size of the device population -- unlike the
    paper's Figure 1 (which plots an assumed per-op constant that does not
    itself model population-dependent lookup cost).
    """
    device_counts = device_counts if device_counts is not None else DEFAULT_DEVICE_POPULATION_POINTS
    results = []

    for count in device_counts:
        ta = TrustedAuthority(master_secret=f"population-bench-{count}".encode())
        device_creds = [ta.enroll(f"pop-device-{i:05d}", "device") for i in range(count)]
        server_cred = ta.enroll(BENCH_SERVER_ID, "server")
        ta.share_mutual_peer_keys(device_creds + [server_cred])

        server = Server(server_cred)
        # Exercise the *last-enrolled* device each trial: this is close to
        # a worst-case scan position and keeps the measurement stable
        # across repeated trials without needing a fresh population per
        # trial.
        probe_device = Device(device_creds[-1])

        samples_ms: list[float] = []
        for _ in range(trials_per_point):
            msg1 = probe_device.build_auth_request(BENCH_SERVER_ID)
            t0 = time.perf_counter()
            server.handle_auth_request(msg1)
            t1 = time.perf_counter()
            samples_ms.append((t1 - t0) * 1000.0)

        results.append(
            {
                "num_devices": count,
                "n_trials": trials_per_point,
                "mean_ms": sum(samples_ms) / len(samples_ms),
                "min_ms": min(samples_ms),
                "max_ms": max(samples_ms),
            }
        )

    return results


def run_full_benchmark(
    *,
    processing_trials: int = 1000,
    population_points: list[int] | None = None,
    population_trials_per_point: int = 50,
) -> dict:
    """BR-4.1: the single entry point the report generator (and CI) calls."""
    baseline_computation_evaluated = {
        scheme: {
            role: evaluate_formula(formula, TABLE_III_CONSTANTS)
            for role, formula in roles.items()
        }
        for scheme, roles in BASELINE_COMPUTATION_FORMULAS.items()
    }

    return {
        "environment": environment_fingerprint(),
        "proposed": {
            "communication": proposed.measure_communication_cost(),
            "processing": proposed.measure_processing_cost(n_trials=processing_trials),
            "storage": proposed.measure_storage_cost(),
            "processing_vs_device_population": measure_processing_cost_vs_population(
                population_points, population_trials_per_point
            ),
        },
        "baselines": {
            "communication_bits_source_paper_table_IV": BASELINE_COMMUNICATION,
            "computation_formulas_source_paper_table_V": BASELINE_COMPUTATION_FORMULAS,
            "computation_ms_evaluated_with_table_III_constants": baseline_computation_evaluated,
            "storage_bytes_source_paper_table_VI": BASELINE_STORAGE,
            "table_III_constants_ms": TABLE_III_CONSTANTS,
        },
    }


def _build_arg_parser():
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m hybrid_ecc_auth.bench.harness",
        description="BR-4: run the hybrid-ecc-auth benchmark suite and render a report (PRD Section 6).",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Full paper-scale run: processing over 1000 trials and the full 100-1000 device population sweep "
        "(BR-4.2: intended for on-demand/nightly runs, not every CI merge).",
    )
    parser.add_argument("--trials", type=int, default=None, help="Override processing-cost trial count.")
    parser.add_argument(
        "--population-points", type=str, default=None, help="Comma-separated device counts, e.g. 100,300,600."
    )
    parser.add_argument(
        "--population-trials", type=int, default=None, help="Trials per device-population point."
    )
    parser.add_argument("--out", type=str, default="bench_output", help="Output directory for the report.")
    return parser


def main(argv: list[str] | None = None) -> None:
    from .report import generate_report

    args = _build_arg_parser().parse_args(argv)

    if args.full:
        processing_trials = args.trials or 1000
        population_points = (
            [int(x) for x in args.population_points.split(",")] if args.population_points else DEFAULT_DEVICE_POPULATION_POINTS
        )
        population_trials = args.population_trials or 50
    else:
        # BR-4.2: lightweight default, suitable for CI on every merge.
        processing_trials = args.trials or 100
        population_points = (
            [int(x) for x in args.population_points.split(",")] if args.population_points else [100, 500, 1000]
        )
        population_trials = args.population_trials or 10

    print(f"Running benchmark ({'full' if args.full else 'quick'}): "
          f"processing_trials={processing_trials}, population_points={population_points}, "
          f"population_trials_per_point={population_trials}")

    results = run_full_benchmark(
        processing_trials=processing_trials,
        population_points=population_points,
        population_trials_per_point=population_trials,
    )
    paths = generate_report(results, args.out)

    print(f"Report written to {args.out}/:")
    for name, path in paths.items():
        print(f"  {name}: {path}")


if __name__ == "__main__":
    main()
