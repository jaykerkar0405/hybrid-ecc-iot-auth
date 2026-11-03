"""Server-side pseudonym resolution strategies.

The base paper (Al-Rasheed et al., Sec. III, Eq. 11) has the device send
PID = H2(lambda_V || t) in clear, while t and N_i travel only inside C1,
encrypted under the device-specific pairwise key k* (Eqs. 9, 12-15). A
server therefore has to find which device (and which epoch) a pseudonym
belongs to before it can decrypt or verify M1. The paper does not specify
how. This module implements several ways of doing it, all of them OUR
choices, and counts the cost of each in *probes*: one probe is one
evaluation of H2 (or of the equivalent keyed hash in the RFID-derived
schemes). Table look-ups cost no hash and are not probes.

Strategies that keep the paper's wire format (PID = H2(lambda || t)):

  LinearScan       O1  counter epochs, on-demand scan (the original code)
  CounterTable     O2  counter epochs, precomputed table, slides on accept
  ClockScan        O3  clock epochs, on-demand scan
  ClockTable       O4  clock epochs, table extended once per epoch
                       (the time-based idea of Tsudik's YA-TRAP)
  TimeMemoryTable      counter epochs with a fixed lifetime, rainbow-table
                       time-memory trade-off (Avoine and Oechslin)

Strategies drawn from RFID work that change M1 (they need a fresh value r
in clear) live in evaluation/resolution/rfid_schemes.py, because
they are not wire-compatible with the Section III exchange.

Every resolver keeps `probes` (resolution work done for incoming
messages) separate from `precompute_probes` (work done offline or at an
epoch boundary), so the two can be reported separately.
"""

from __future__ import annotations

import hmac
import random
from typing import Callable

from ..crypto.hashes import h2_pseudonym
from ..storage.session_log import SessionLog
from .errors import ReplayDetected, UnknownPeerError

#: Size we charge for one stored pseudonym entry: 32-byte key plus an
#: 8-byte (device index, epoch) value.
TABLE_ENTRY_BYTES = 40
#: One stored per-device epoch counter.
COUNTER_BYTES = 8
#: One rainbow-chain record: start index and end index, 4 bytes each.
CHAIN_RECORD_BYTES = 8
#: One cached nonce (N_i is 128 bits by default) with its epoch tag.
NONCE_CACHE_ENTRY_BYTES = 24


class Resolver:
    """Interface. A Server calls attach() once, resolve() for every M1,
    and accept() after M1 has been verified."""

    name = "abstract"
    wire_compatible = True

    def __init__(self) -> None:
        self.probes = 0
        self.precompute_probes = 0
        self.peer_secrets: dict[str, int] = {}
        self.session_log: SessionLog | None = None

    # -- counting ---------------------------------------------------------
    def _h2(self, lam: int, epoch: int, *, precompute: bool = False) -> bytes:
        if precompute:
            self.precompute_probes += 1
        else:
            self.probes += 1
        return h2_pseudonym(lam, epoch)

    def reset_counters(self) -> None:
        self.probes = 0
        self.precompute_probes = 0

    # -- protocol hooks ---------------------------------------------------
    def attach(self, peer_secrets: dict[str, int], session_log: SessionLog) -> None:
        self.peer_secrets = peer_secrets
        self.session_log = session_log

    def resolve(self, pid: bytes) -> tuple[str, int]:  # pragma: no cover - interface
        raise NotImplementedError

    def accept(self, peer_identity: str, epoch: int, n_i: bytes) -> None:
        assert self.session_log is not None
        self.session_log.accept_epoch(peer_identity, epoch)

    def storage_bytes(self) -> int:
        """Resolution state held in addition to the N long-term secrets."""
        return 0


class LinearScan(Resolver):
    """O1, the original behaviour of Server.resolve_pseudonym: for every
    enrolled peer, probe every epoch in SessionLog.epoch_search_window()."""

    name = "O1 counter + linear scan"

    def resolve(self, pid: bytes) -> tuple[str, int]:
        log = self.session_log
        assert log is not None
        for peer_identity, peer_lam in self.peer_secrets.items():
            for epoch in log.epoch_search_window(peer_identity):
                if hmac.compare_digest(self._h2(peer_lam, epoch), pid):
                    if log.is_stale_epoch(peer_identity, epoch):
                        raise ReplayDetected(f"pseudonym for {peer_identity!r} reuses stale epoch {epoch}")
                    return peer_identity, epoch
        raise UnknownPeerError("pseudonym did not resolve to any known, in-window peer")

    def storage_bytes(self) -> int:
        return COUNTER_BYTES * len(self.peer_secrets)


class CounterTable(Resolver):
    """O2: a dictionary from every acceptable future pseudonym to its
    (peer, epoch). For a peer whose last accepted epoch is `last`, the
    table holds epochs last+1 .. last+F, the same forward tolerance F as
    the linear scan. After an epoch e is accepted, entries <= e are
    dropped and the window is refilled, which costs (e - last) probes:
    one in the normal case. A stale (replayed) pseudonym is no longer in
    the table and is rejected as unknown."""

    name = "O2 counter + precomputed table"

    def __init__(self, forward_tolerance: int | None = None) -> None:
        super().__init__()
        self._forward = forward_tolerance
        self._table: dict[bytes, tuple[str, int]] = {}
        self._hi: dict[str, int] = {}  # highest epoch currently tabled per peer

    @property
    def forward(self) -> int:
        assert self.session_log is not None
        return self._forward if self._forward is not None else self.session_log.forward_tolerance

    def attach(self, peer_secrets, session_log) -> None:
        super().attach(peer_secrets, session_log)
        self._table.clear()
        self._hi.clear()
        for peer in peer_secrets:
            self._fill(peer, precompute=True)

    def _last(self, peer: str) -> int:
        assert self.session_log is not None
        return self.session_log._last_accepted_epoch.get(peer, -1)

    def _fill(self, peer: str, *, precompute: bool) -> None:
        last = self._last(peer)
        start = max(self._hi.get(peer, last), last) + 1
        lam = self.peer_secrets[peer]
        for epoch in range(start, last + self.forward + 1):
            self._table[self._h2(lam, epoch, precompute=precompute)] = (peer, epoch)
        self._hi[peer] = last + self.forward

    def resolve(self, pid: bytes) -> tuple[str, int]:
        hit = self._table.get(pid)
        if hit is None:
            raise UnknownPeerError("pseudonym is not in the precomputed table")
        return hit

    def accept(self, peer_identity: str, epoch: int, n_i: bytes) -> None:
        super().accept(peer_identity, epoch, n_i)
        last = self._last(peer_identity)
        for key in [k for k, (p, e) in self._table.items() if p == peer_identity and e <= last]:
            del self._table[key]
        self._fill(peer_identity, precompute=False)

    def storage_bytes(self) -> int:
        return TABLE_ENTRY_BYTES * len(self._table) + COUNTER_BYTES * len(self.peer_secrets)


class _ClockResolver(Resolver):
    """Shared logic for clock epochs: t = floor(clock() / epoch_seconds).
    A pseudonym is accepted for epochs cur-drift .. cur+drift. Because
    several sessions in one epoch share a pseudonym, the epoch no longer
    detects replays, so accepted nonces N_i are cached per epoch."""

    def __init__(self, clock: Callable[[], float], *, epoch_seconds: float = 60.0, drift: int = 1) -> None:
        super().__init__()
        self.clock = clock
        self.epoch_seconds = epoch_seconds
        self.drift = drift
        self._nonces: dict[int, set[bytes]] = {}

    def current_epoch(self) -> int:
        return int(self.clock() // self.epoch_seconds)

    def window(self) -> list[int]:
        cur = self.current_epoch()
        # Probe the expected epoch first, then the neighbours.
        return [cur] + [cur + d for k in range(1, self.drift + 1) for d in (-k, k) if cur + d >= 0]

    def accept(self, peer_identity: str, epoch: int, n_i: bytes) -> None:
        lo = self.current_epoch() - self.drift
        for old in [e for e in self._nonces if e < lo]:
            del self._nonces[old]
        seen = self._nonces.setdefault(epoch, set())
        tag = peer_identity.encode() + b"\x00" + n_i
        if tag in seen:
            raise ReplayDetected(f"nonce already accepted for {peer_identity!r} in epoch {epoch}")
        seen.add(tag)
        assert self.session_log is not None
        last = self.session_log._last_accepted_epoch.get(peer_identity, -1)
        if epoch > last:
            self.session_log._last_accepted_epoch[peer_identity] = epoch

    def nonce_cache_entries(self) -> int:
        return sum(len(s) for s in self._nonces.values())

    def storage_bytes(self) -> int:
        return NONCE_CACHE_ENTRY_BYTES * self.nonce_cache_entries()


class ClockScan(_ClockResolver):
    """O3: probe every peer for each epoch in the drift window."""

    name = "O3 clock + linear scan"

    def resolve(self, pid: bytes) -> tuple[str, int]:
        window = self.window()
        for peer_identity, peer_lam in self.peer_secrets.items():
            for epoch in window:
                if hmac.compare_digest(self._h2(peer_lam, epoch), pid):
                    return peer_identity, epoch
        raise UnknownPeerError("pseudonym did not resolve for any peer in the clock window")


class ClockTable(_ClockResolver):
    """O4: a table of every peer's pseudonym for epochs cur-drift ..
    cur+drift. When the clock enters a new epoch, the entries for the
    epoch that left the window are dropped and one new epoch is added for
    every peer: N probes per epoch, none per authentication."""

    name = "O4 clock + per-epoch table"

    def __init__(self, clock, *, epoch_seconds: float = 60.0, drift: int = 1) -> None:
        super().__init__(clock, epoch_seconds=epoch_seconds, drift=drift)
        self._table: dict[bytes, tuple[str, int]] = {}
        self._tabled: set[int] = set()

    def attach(self, peer_secrets, session_log) -> None:
        super().attach(peer_secrets, session_log)
        self._table.clear()
        self._tabled.clear()
        self._advance()

    def _advance(self) -> None:
        want = set(self.window())
        for epoch in sorted(want - self._tabled):
            for peer, lam in self.peer_secrets.items():
                self._table[self._h2(lam, epoch, precompute=True)] = (peer, epoch)
        gone = self._tabled - want
        if gone:
            for key in [k for k, (_, e) in self._table.items() if e in gone]:
                del self._table[key]
        self._tabled = want

    def resolve(self, pid: bytes) -> tuple[str, int]:
        self._advance()
        hit = self._table.get(pid)
        if hit is None:
            raise UnknownPeerError("pseudonym is not in the current epoch table")
        return hit

    def storage_bytes(self) -> int:
        return TABLE_ENTRY_BYTES * len(self._table) + super().storage_bytes()


class TimeMemoryTable(Resolver):
    """Rainbow-table time-memory trade-off over the space of all
    (device, epoch) pairs with epoch < lifetime, after Avoine and
    Oechslin's treatment of the OSK protocol. Point x in [0, S), S = N *
    lifetime, stands for device x // lifetime at epoch x % lifetime, and
    f(x) = H2(lambda_device || epoch). Chains of length `chain_length`
    are stored only by their start and end points, in `tables` tables
    with different reduction functions.

    The device is unchanged: it sends H2(lambda || t) for a counter t.
    The server accepts t only if it is above the last accepted epoch, so
    dropped messages never desynchronise the pair until t reaches the
    lifetime. A pseudonym whose point no chain covers is not found (a
    miss); the device's counter has already advanced, so its next attempt
    is a different point."""

    name = "Rainbow time-memory trade-off"

    def __init__(self, *, lifetime: int = 128, tables: int = 6, chain_length: int | None = None,
                 chains_per_table: int | None = None, seed: int = 1) -> None:
        super().__init__()
        self.lifetime = lifetime
        self.n_tables = tables
        self._chain_length = chain_length
        self._chains_per_table = chains_per_table
        self.seed = seed
        self._peers: list[str] = []
        self._lams: list[int] = []
        self._ends: list[dict[int, int]] = []
        self.false_alarms = 0

    # Parameters chosen so that time and memory both grow as S^(2/3).
    @property
    def space(self) -> int:
        return len(self._peers) * self.lifetime

    @property
    def chain_length(self) -> int:
        if self._chain_length is not None:
            return self._chain_length
        return max(1, round(self.space ** (1 / 3)))

    @property
    def chains_per_table(self) -> int:
        if self._chains_per_table is not None:
            return self._chains_per_table
        return max(1, -(-2 * self.space // self.chain_length))

    def _f(self, x: int, *, precompute: bool) -> bytes:
        return self._h2(self._lams[x // self.lifetime], x % self.lifetime, precompute=precompute)

    def _reduce(self, digest: bytes, column: int, table: int) -> int:
        return (int.from_bytes(digest[:8], "big") + column + table * 1_000_003) % self.space

    def attach(self, peer_secrets, session_log) -> None:
        super().attach(peer_secrets, session_log)
        self._peers = list(peer_secrets)
        self._lams = [peer_secrets[p] for p in self._peers]
        rng = random.Random(self.seed)
        self._ends = []
        tau = self.chain_length
        for table in range(self.n_tables):
            ends: dict[int, int] = {}
            m = min(self.chains_per_table, self.space)
            for start in rng.sample(range(self.space), m):
                x = start
                for column in range(tau):
                    x = self._reduce(self._f(x, precompute=True), column, table)
                ends.setdefault(x, start)  # keep one chain per end point (a "perfect" table)
            self._ends.append(ends)

    def _lookup(self, pid: bytes) -> int | None:
        tau = self.chain_length
        for table, ends in enumerate(self._ends):
            for column in range(tau - 1, -1, -1):
                z = self._reduce(pid, column, table)
                for j in range(column + 1, tau):
                    z = self._reduce(self._f(z, precompute=False), j, table)
                start = ends.get(z)
                if start is None:
                    continue
                x = start
                for j in range(column):
                    x = self._reduce(self._f(x, precompute=False), j, table)
                if hmac.compare_digest(self._f(x, precompute=False), pid):
                    return x
                self.false_alarms += 1
        return None

    def resolve(self, pid: bytes) -> tuple[str, int]:
        x = self._lookup(pid)
        if x is None:
            raise UnknownPeerError("pseudonym is not covered by the time-memory tables")
        peer, epoch = self._peers[x // self.lifetime], x % self.lifetime
        assert self.session_log is not None
        if self.session_log.is_stale_epoch(peer, epoch):
            raise ReplayDetected(f"pseudonym for {peer!r} reuses stale epoch {epoch}")
        return peer, epoch

    def storage_bytes(self) -> int:
        return CHAIN_RECORD_BYTES * sum(len(e) for e in self._ends) + COUNTER_BYTES * len(self._peers)

    def coverage(self) -> float:
        """Fraction of the S points that some chain covers (counts no probes)."""
        saved = (self.probes, self.precompute_probes)
        covered: set[int] = set()
        tau = self.chain_length
        for table, ends in enumerate(self._ends):
            for start in ends.values():
                x = start
                for column in range(tau):
                    covered.add(x)
                    x = self._reduce(self._f(x, precompute=True), column, table)
        self.probes, self.precompute_probes = saved
        return len(covered) / self.space
