"""Nonce/pseudonym replay-window bookkeeping (SEC-01) and the block-list for
repeatedly failing entities (Section II "maximum of three attempts",
FR-5.6, SEC-05). Shared by both Device and Server -- the paper describes
the three-attempts rule symmetrically for "every object."

Epoch/clock-drift handling is explicitly unspecified by the source paper
(see PRD Section 12, risk row). This module documents its own tolerance
window as an implementation decision, flagged for security review: a
resolved pseudonym is accepted only if its epoch is strictly greater than
the last epoch accepted for that peer, and the search for a matching
pseudonym is bounded to [last_accepted - replay_lookback, last_accepted +
forward_tolerance] so that (a) a handful of dropped messages doesn't
desynchronize the session, and (b) resolution stays O(1) rather than
scanning an unbounded epoch range.
"""

from __future__ import annotations

from typing import Callable

DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_FORWARD_TOLERANCE = 8
DEFAULT_REPLAY_LOOKBACK = 16


class SessionLog:
    def __init__(
        self,
        *,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        forward_tolerance: int = DEFAULT_FORWARD_TOLERANCE,
        replay_lookback: int = DEFAULT_REPLAY_LOOKBACK,
    ):
        self.max_attempts = max_attempts
        self.forward_tolerance = forward_tolerance
        self.replay_lookback = replay_lookback
        self._last_accepted_epoch: dict[str, int] = {}
        self._failed_attempts: dict[str, int] = {}
        self._blocked: set[str] = set()
        self._block_listeners: list[Callable[[str], None]] = []

    # -- epoch / replay-window -------------------------------------------

    def epoch_search_window(self, peer_identity: str) -> range:
        """Bounded epoch range to probe when resolving an incoming
        pseudonym for `peer_identity` (FR-4.2)."""
        last = self._last_accepted_epoch.get(peer_identity, -1)
        lo = max(0, last - self.replay_lookback)
        hi = last + self.forward_tolerance
        return range(lo, hi + 1)

    def is_stale_epoch(self, peer_identity: str, epoch: int) -> bool:
        """True if `epoch` has already been accepted (or superseded) for
        this peer -- i.e. a replayed pseudonym/nonce (SEC-01)."""
        last = self._last_accepted_epoch.get(peer_identity, -1)
        return epoch <= last

    def accept_epoch(self, peer_identity: str, epoch: int) -> None:
        last = self._last_accepted_epoch.get(peer_identity, -1)
        if epoch > last:
            self._last_accepted_epoch[peer_identity] = epoch

    # -- block-list (FR-5.6, SEC-05) ---------------------------------------

    def is_blocked(self, peer_identity: str) -> bool:
        return peer_identity in self._blocked

    def record_failure(self, peer_identity: str) -> bool:
        """Record one failed attempt for `peer_identity`. Returns True if
        this call caused (or the entity already was) block-listed."""
        if peer_identity in self._blocked:
            return True
        count = self._failed_attempts.get(peer_identity, 0) + 1
        self._failed_attempts[peer_identity] = count
        if count >= self.max_attempts:
            self._block(peer_identity)
            return True
        return False

    def record_success(self, peer_identity: str) -> None:
        self._failed_attempts.pop(peer_identity, None)

    def block(self, peer_identity: str) -> None:
        """Directly block an identity (operator override / propagated
        block notice from a peer, see subscribe_block)."""
        self._block(peer_identity)

    def _block(self, peer_identity: str) -> None:
        newly_blocked = peer_identity not in self._blocked
        self._blocked.add(peer_identity)
        if newly_blocked:
            for listener in self._block_listeners:
                listener(peer_identity)

    def subscribe_block(self, callback: Callable[[str], None]) -> None:
        """FR-5.6: a simple pub/sub hook. The demo layer uses this to
        broadcast a newly blocked identifier to other locally-known
        trusted peers (Algorithm 1/2, lines 14-15)."""
        self._block_listeners.append(callback)
