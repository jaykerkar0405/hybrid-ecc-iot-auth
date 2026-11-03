"""FR-2: Offline Registration (Trusted Authority phase).

Mirrors the paper's Section II offline/registration phase and Section IV-A
ECC setup (Eq. 8): the TA samples a master secret s, and for each module X
computes a per-module ECC secret lambda_X = H1(ID_X || s) mod n. Per the
paper's "list of secret keys of trusted modules" distribution model
(Section II), the TA also hands each entity the lambda values of its
trusted peers so that the pairwise symmetric root k*_ij = KDF(lambda_Vi ||
lambda_Rj) (Eq. 9) can be computed locally, offline, on both sides -- see
protocol/entity.py::derive_pairwise_root.

FR-2.3: this module performs no network I/O. That invariant is enforced by
tests/unit/test_ta.py, which monkeypatches socket.socket to raise if called
during any TA operation.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field

from ..crypto.curve import scalar_to_public_point
from ..crypto.hashes import h1_derive_secret

VALID_ROLES = ("device", "server")


def derive_long_term_secret(identity: str, master_secret: bytes) -> int:
    """lambda_X = H1(ID_X || s) mod n (Eq. 8, FR-2.1)."""
    return h1_derive_secret(identity.encode("utf-8"), master_secret)


@dataclass
class Credential:
    """An entity's TA-issued offline credential bundle.

    `peer_secrets` holds the lambda values of trusted peers this entity is
    allowed to talk to (Section II's "list of secret keys"), keyed by peer
    identity. It starts empty and is populated by
    TrustedAuthority.share_peer_keys.
    """

    identity: str
    role: str
    lam: int
    public_point: bytes | None = None
    peer_secrets: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "identity": self.identity,
            "role": self.role,
            "lam": self.lam,
            "public_point": self.public_point.hex() if self.public_point is not None else None,
            "peer_secrets": {k: v for k, v in self.peer_secrets.items()},
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Credential":
        return cls(
            identity=d["identity"],
            role=d["role"],
            lam=d["lam"],
            public_point=bytes.fromhex(d["public_point"]) if d.get("public_point") else None,
            peer_secrets=dict(d.get("peer_secrets", {})),
        )


class TrustedAuthority:
    """Offline root of trust (Section IV-A). No network I/O anywhere in this
    class -- registration is executed entirely locally per the paper's
    "intrusion-free offline process" assumption.
    """

    def __init__(self, master_secret: bytes | None = None):
        self.master_secret = master_secret if master_secret is not None else secrets.token_bytes(32)
        self._registry: dict[str, Credential] = {}

    def enroll(self, identity: str, role: str, *, export_public_point: bool = False) -> Credential:
        """Register a single device or server module (Eq. 8, FR-2.1/2.2)."""
        if role not in VALID_ROLES:
            raise ValueError(f"role must be one of {VALID_ROLES}, got {role!r}")
        if identity in self._registry:
            raise ValueError(f"identity {identity!r} is already enrolled")

        lam = derive_long_term_secret(identity, self.master_secret)
        public_point = scalar_to_public_point(lam) if export_public_point else None

        cred = Credential(identity=identity, role=role, lam=lam, public_point=public_point)
        self._registry[identity] = cred
        return cred

    def enroll_batch(self, manifest: list[dict]) -> dict[str, Credential]:
        """FR-2.4: batch-enroll N devices and M servers from a manifest list
        of {"identity": ..., "role": ..., "export_public_point": bool}."""
        return {
            entry["identity"]: self.enroll(
                entry["identity"],
                entry["role"],
                export_public_point=entry.get("export_public_point", False),
            )
            for entry in manifest
        }

    def share_peer_keys(self, cred: Credential, peers: list[Credential]) -> None:
        """Populate `cred.peer_secrets` with each peer's lambda (Section II
        peer-key list model, FR-3.1). Symmetric: does not also update the
        peers -- call this once per direction, or once per pair via
        share_mutual_peer_keys."""
        for peer in peers:
            if peer.identity == cred.identity:
                continue
            cred.peer_secrets[peer.identity] = peer.lam

    def share_mutual_peer_keys(self, creds: list[Credential]) -> None:
        """Convenience: every credential in `creds` learns every other's
        lambda (full mesh peer-key distribution, as used by the demo/bench
        harness for small device/server populations)."""
        for cred in creds:
            self.share_peer_keys(cred, [c for c in creds if c.identity != cred.identity])

    def lookup(self, identity: str) -> Credential:
        return self._registry[identity]


__all__ = ["TrustedAuthority", "Credential", "VALID_ROLES"]
