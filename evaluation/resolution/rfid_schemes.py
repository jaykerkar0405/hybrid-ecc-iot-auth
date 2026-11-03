# Copyright (c) 2026 Jay Kerkar, Chaitanya Kelkar, Chirag Poornamath, Yash Kolekar and Shanta Sondur
# SPDX-License-Identifier: Apache-2.0
"""Pseudonym-resolution schemes from RFID privacy work that do NOT keep the
Section III wire format: each needs a fresh random value r sent in clear in
M1. They are modelled at the resolution level only (device-side pseudonym
generation plus server-side search), with every keyed-hash evaluation counted
as one probe, the same unit as implementation/python/hybrid_ecc_auth/protocol/resolution.py.

  RandomizedHashLock  Weis, Sarma, Rivest and Engels (SPC 2003): the device
                      sends (r, H(lambda || r)); the server tries every key.
  KeyTree             Molnar and Wagner (CCS 2004): keys form a tree of
                      branching factor delta; the device sends one keyed hash
                      of r per level and the server walks down the tree.

The keyed hash is SHA-256 over (key || r), the same primitive as H2.
"""
from __future__ import annotations

import hashlib
import hmac
import math
import os

R_BYTES = 16          # fresh value sent in clear (same size as N_i)
DIGEST_BYTES = 32
KEY_BYTES = 32


def _h(key: bytes, r: bytes) -> bytes:
    return hashlib.sha256(key + r).digest()


class RandomizedHashLock:
    name = "Randomized hash lock (challenge-response)"

    def __init__(self, keys: dict[str, bytes]):
        self.keys = keys
        self.probes = 0

    @staticmethod
    def device_message(key: bytes) -> tuple[bytes, bytes]:
        r = os.urandom(R_BYTES)
        return r, _h(key, r)

    def resolve(self, r: bytes, tag: bytes) -> str | None:
        for peer, key in self.keys.items():
            self.probes += 1
            if hmac.compare_digest(_h(key, r), tag):
                return peer
        return None

    def storage_bytes(self) -> int:
        return 0  # only the N secrets the server already holds

    @staticmethod
    def extra_m1_bytes(n: int) -> int:
        return R_BYTES


class KeyTree:
    """Balanced key tree. Device i is leaf i; its path from the root is the
    base-delta digits of i. Each internal node and each leaf has its own key.
    The device sends r and one tag per level; the leaf-level tag plays the
    role of the pseudonym."""

    name = "Key tree"

    def __init__(self, peers: list[str], delta: int = 32, seed: bytes = b"tree"):
        self.peers = peers
        self.delta = delta
        self.depth = max(1, math.ceil(math.log(max(len(peers), 2), delta) - 1e-12))
        self.probes = 0
        self._key: dict[tuple[int, ...], bytes] = {}
        self._children: dict[tuple[int, ...], list[int]] = {}
        for i in range(len(peers)):
            path = self.path(i)
            for level in range(1, self.depth + 1):
                node = path[:level]
                if node not in self._key:
                    self._key[node] = hashlib.sha256(seed + repr(node).encode()).digest()
                    self._children.setdefault(node[:-1], []).append(node[-1])

    def path(self, i: int) -> tuple[int, ...]:
        digits = []
        for _ in range(self.depth):
            digits.append(i % self.delta)
            i //= self.delta
        return tuple(reversed(digits))

    def device_message(self, i: int) -> tuple[bytes, list[bytes]]:
        r = os.urandom(R_BYTES)
        path = self.path(i)
        return r, [_h(self._key[path[:level]], r) for level in range(1, self.depth + 1)]

    def resolve(self, r: bytes, tags: list[bytes]) -> str | None:
        node: tuple[int, ...] = ()
        for tag in tags:
            for child in self._children.get(node, []):
                self.probes += 1
                if hmac.compare_digest(_h(self._key[node + (child,)], r), tag):
                    node = node + (child,)
                    break
            else:
                return None
        index = 0
        for digit in node:
            index = index * self.delta + digit
        return self.peers[index]

    def storage_bytes(self) -> int:
        """Keys of the internal nodes; the leaf keys replace the N secrets."""
        return KEY_BYTES * sum(1 for node in self._key if len(node) < self.depth)

    def extra_m1_bytes(self) -> int:
        return R_BYTES + DIGEST_BYTES * (self.depth - 1)
