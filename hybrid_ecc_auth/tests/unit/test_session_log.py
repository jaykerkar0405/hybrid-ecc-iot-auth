"""Unit tests for storage/session_log.py (replay window + block-list)."""

from __future__ import annotations

from hybrid_ecc_auth.storage.session_log import SessionLog


def test_epoch_search_window_starts_at_zero_for_unseen_peer():
    log = SessionLog(forward_tolerance=8, replay_lookback=16)
    window = log.epoch_search_window("peer-1")
    assert list(window) == list(range(0, 8))


def test_accept_epoch_advances_window():
    log = SessionLog(forward_tolerance=4, replay_lookback=2)
    log.accept_epoch("peer-1", 10)
    window = log.epoch_search_window("peer-1")
    assert list(window) == list(range(8, 15))


def test_accept_epoch_never_moves_backward():
    log = SessionLog()
    log.accept_epoch("peer-1", 10)
    log.accept_epoch("peer-1", 3)  # stale, should be ignored
    assert log.is_stale_epoch("peer-1", 10) is True
    assert log.is_stale_epoch("peer-1", 11) is False


def test_is_stale_epoch():
    log = SessionLog()
    log.accept_epoch("peer-1", 5)
    assert log.is_stale_epoch("peer-1", 5) is True
    assert log.is_stale_epoch("peer-1", 4) is True
    assert log.is_stale_epoch("peer-1", 6) is False


def test_record_failure_blocks_after_max_attempts():
    log = SessionLog(max_attempts=3)
    assert log.record_failure("peer-1") is False
    assert log.record_failure("peer-1") is False
    assert log.record_failure("peer-1") is True
    assert log.is_blocked("peer-1") is True


def test_record_success_resets_failure_count():
    log = SessionLog(max_attempts=3)
    log.record_failure("peer-1")
    log.record_failure("peer-1")
    log.record_success("peer-1")
    assert log.record_failure("peer-1") is False  # counter was reset, not yet blocked
    assert log.is_blocked("peer-1") is False


def test_block_and_subscribe_block_notifies_once():
    log = SessionLog()
    notified = []
    log.subscribe_block(notified.append)
    log.block("peer-1")
    log.block("peer-1")  # already blocked -- must not notify twice
    assert notified == ["peer-1"]


def test_already_blocked_entity_short_circuits_record_failure():
    log = SessionLog(max_attempts=3)
    log.block("peer-1")
    assert log.record_failure("peer-1") is True
