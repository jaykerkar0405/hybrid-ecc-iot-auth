"""Unit tests for the benchmarking harness (PRD Section 6)."""

from __future__ import annotations

import json

from hybrid_ecc_auth.bench import proposed
from hybrid_ecc_auth.bench.baselines import (
    BASELINE_COMMUNICATION,
    BASELINE_COMPUTATION_FORMULAS,
    BASELINE_STORAGE,
    TABLE_III_CONSTANTS,
    evaluate_formula,
)
from hybrid_ecc_auth.bench.harness import measure_processing_cost_vs_population, run_full_benchmark
from hybrid_ecc_auth.bench.report import compute_reduction_summary, generate_report


def test_measure_communication_cost_structure():
    result = proposed.measure_communication_cost()
    assert result["m1_wire_bytes"] > 0
    assert result["m2_wire_bytes"] > 0
    assert result["session_total_wire_bytes"] == result["m1_wire_bytes"] + result["m2_wire_bytes"]
    assert result["offline_registration_wire_bytes"] == 0
    assert sum(result["m1_field_breakdown_raw_bytes"].values()) < result["m1_wire_bytes"]  # base64+JSON overhead


def test_measure_processing_cost_structure():
    result = proposed.measure_processing_cost(n_trials=20)
    warm = result["warm_steady_state_pairwise_root_cached_FR_3_2"]
    assert warm["device_build_request"]["n"] == 20
    assert warm["server_handle_request"]["mean_ms"] > 0
    cold = result["cold_pairwise_root_recomputed_every_session_matches_paper_Eq22"]
    assert cold["n_trials"] >= 50 or cold["n_trials"] == 20 // 10 or cold["n_trials"] == 50


def test_measure_storage_cost_structure():
    result = proposed.measure_storage_cost()
    assert result["device_persisted_state_bytes"] > 0
    assert result["server_persisted_state_bytes"] > 0
    # Per-field breakdown serializes each value alone (no outer key label
    # bytes), so it's necessarily a bit smaller than the combined object.
    assert 0 < sum(result["device_state_breakdown_bytes"].values()) <= result["device_persisted_state_bytes"]


def test_baseline_reference_data_has_proposed_and_nine_baselines():
    non_proposed_comm = [k for k in BASELINE_COMMUNICATION if not k.startswith("Proposed")]
    non_proposed_storage = [k for k in BASELINE_STORAGE if not k.startswith("Proposed")]
    non_proposed_computation = [k for k in BASELINE_COMPUTATION_FORMULAS if not k.startswith("Proposed")]
    assert len(non_proposed_comm) == 9
    assert len(non_proposed_storage) == 6  # Table VI lists 6 non-proposed rows
    assert len(non_proposed_computation) == 9  # Table V lists 9 non-proposed rows (Challa; no Fakroon in Table V)


def test_evaluate_formula_matches_table_v_proposed_scheme():
    formula = BASELINE_COMPUTATION_FORMULAS["Proposed scheme (paper-reported)"]["server"]
    assert formula == "4*TH + 5*TECM"
    value = evaluate_formula(formula, TABLE_III_CONSTANTS)
    expected = 4 * TABLE_III_CONSTANTS["TH"] + 5 * TABLE_III_CONSTANTS["TECM"]
    assert value == expected


def test_evaluate_formula_restricted_namespace_rejects_builtins():
    import pytest

    with pytest.raises(Exception):
        evaluate_formula("__import__('os').system('echo pwned')")


def test_measure_processing_cost_vs_population_increases_with_population():
    points = measure_processing_cost_vs_population([50, 400], trials_per_point=5)
    assert points[0]["num_devices"] == 50
    assert points[1]["num_devices"] == 400
    # Linear-scan pseudonym resolution (FR-4.2) should cost measurably more
    # with a larger known-peer population.
    assert points[1]["mean_ms"] > points[0]["mean_ms"]


def test_run_full_benchmark_end_to_end():
    results = run_full_benchmark(processing_trials=20, population_points=[50, 200], population_trials_per_point=5)
    assert "proposed" in results and "baselines" in results
    assert results["proposed"]["communication"]["session_total_wire_bytes"] > 0
    # JSON-serializable (required for BR-4.1's results.json output).
    json.dumps(results)


def test_compute_reduction_summary_directions():
    results = run_full_benchmark(processing_trials=20, population_points=[50], population_trials_per_point=5)
    summary = compute_reduction_summary(results)
    assert set(summary) == {"communication", "processing", "storage"}
    for row in summary.values():
        assert "measured_reduction_pct_vs_baseline_mean" in row
        assert "direction_consistent_with_paper_claim" in row


def test_generate_report_writes_all_artifacts(tmp_path):
    results = run_full_benchmark(processing_trials=20, population_points=[50, 200], population_trials_per_point=5)
    paths = generate_report(results, tmp_path)
    for key, path in paths.items():
        assert path.exists(), f"{key} was not written"
    assert (tmp_path / "report.md").read_text().startswith("# Hybrid ECC IoT Authentication")
    assert "<html>" in (tmp_path / "report.html").read_text()
    json.loads((tmp_path / "results.json").read_text())  # must be valid JSON
